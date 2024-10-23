from typing import Union

import numpy as np
import trimesh
import torch
import open3d as o3d
from loguru import logger
from scipy.spatial import KDTree
import logging
import time
from pathlib import Path
from skimage.io import imsave

from ..internal.types import Vector3d, Vector4d


def estimate_pc_normals_from_mesh(pc_vertices: np.ndarray, mesh: trimesh.base.Trimesh):
    """Approximate PC per-vertex normals from mesh that is registered to PC.
    For each PC vertex averages vertex normals for 5 nearest mesh vertices.

    Args:
        pc_vertices (np.ndarray): pointcloud vertices (n_vertices x 3)
        mesh (trimesh.base.Trimesh): mesh, registered to the PC;

    Returns:
        np.ndarray: estimated normals n_vertices x 3
    """
    mesh_normals = mesh.vertex_normals
    tree = KDTree(mesh.vertices)
    dd, nn_index = tree.query(pc_vertices, k=5, p=2, workers=-1)
    pc_normals = mesh_normals[nn_index]
    pc_normals = pc_normals.mean(axis=1)
    pc_normals = pc_normals / (np.sqrt(pc_normals ** 2).sum(axis=1, keepdims=True))

    return pc_normals


def estimate_normals_from_pointcloud(pc_vertices: np.ndarray, backend="open3d", device="gpu"):
    """Approximate PC per-vertex normals using algorithms implemented in opend3d or pytorch3d.

    Args:
        pc_vertices (np.ndarray): pointcloud vertices (n_vertices x 3)
        backend (str, optional): backend that is used to estimate normals,
            pytorch3d and open3d are supported (default: "open3d")
        device (str, optional): pytorch device (default: "gpu")

    Returns:
        np.ndarray: estimated normals n_vertices x 3
    """
    if backend == "open3d":
        import open3d as o3d

        pc = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pc_vertices))
        pc.estimate_normals(fast_normal_computation=False)
        pc.orient_normals_consistent_tangent_plane(k=10)

        pc_normals = np.asarray(pc.normals).astype(np.float32)
    elif backend == "pytorch3d":
        import torch
        from pytorch3d.ops import estimate_pointcloud_normals

        pc_vertices_th = torch.tensor(pc_vertices, dtype=torch.float, device=device)
        pc_normals_th = estimate_pointcloud_normals(pc_vertices_th.unsqueeze(0), 5).squeeze(0)

        pc_normals = pc_normals_th.cpu().numpy().astype(np.float32)
    else:
        raise NotImplementedError(f"backend {backend} is not supported. Possible backends: open3d, pytorch3d.")

    return pc_normals


def approximate_colors_from_camera(
        camera_viewdir: np.ndarray, vertex_normals: np.ndarray, per_vertex_color: Union[Vector3d, Vector4d],
        back_color: Union[Vector3d, Vector4d] = (0.6, 0.6, 0.6)
):
    """Approximation of visible vertices from camera.
    PC vertices are colored with their initial color only if they are visible from camera (here we use the approximation
    of visibility, by calculating the angle between vertex normal and camera's view direction), otherwise the vertices
    are colored with back_color.

    Args:
        camera_viewdir (np.ndarray): view direction of the camera
        vertex_normals (np.ndarray): per-vertex normals of the point cloud
        per_vertex_color (Union[Vector3d, Vector4d]): colors for the point cloud
        back_color (Union[Vector3d, Vector4d], optional): color for vertices that are not visible from camera. With
            the approximation of visibility, described above (default: (0.6, 0.6, 0.6))

    Returns:
        np.ndarray: new per-vertex coloring with invisible vertices colored in back_color
    """
    # Add alpha
    back_color = np.array(back_color)
    if back_color.shape[0] == 3:
        back_color = np.concatenate((back_color, [1.0]), axis=0)

    # Expand colors if needed
    num_vertices = vertex_normals.shape[0]
    per_vertex_color = np.array(per_vertex_color)
    if per_vertex_color.ndim == 1:
        per_vertex_color = np.repeat(per_vertex_color[np.newaxis], num_vertices, axis=0).astype(np.float32)
    elif per_vertex_color.ndim == 2:
        assert per_vertex_color.shape[0] == num_vertices, \
            "Length of vertex_colors is to be equal to the number of vertices."
    else:
        raise NotImplementedError("Only uniform or per-vertex colors are supported for color approximation.")

    # Add alpha to colors if needed
    if per_vertex_color.shape[1] == 3:
        per_vertex_color = np.concatenate((per_vertex_color, np.ones((num_vertices, 1), np.float32)), axis=1)

    # Add alpha to support transparent back_color
    if per_vertex_color.shape[1] == 3:
        alpha = np.ones((per_vertex_color.shape[0], 1), dtype=np.float32)
        vertex_colors = np.concatenate((per_vertex_color, alpha), axis=1)

    # Compute mask and recolor
    dot_product = (vertex_normals * camera_viewdir[np.newaxis, :]).sum(axis=1)
    back_mask = dot_product > 0.0
    per_vertex_color[back_mask] = back_color[np.newaxis]

    return per_vertex_color


class PCMeshifier:
    torch_dtype = torch.float32
    np_dtype = np.float64

    def __init__(self, subsampled_mesh_faces_count=1_000_000, texture_resolution=(30_000, 30_000), pc_subsample=None,
            max_query_size=2_000, knn=3, gpu_index=None, bpa_radius=None):
        self.subsampled_mesh_faces_count = subsampled_mesh_faces_count
        self.texture_resolution = np.asarray(texture_resolution)
        self.pc_subsample = pc_subsample
        self.max_query_size = max_query_size
        self.knn = knn
        self.gpu_index = gpu_index
        self.bpa_radius = bpa_radius
        self.device = torch.device(f"cuda:{gpu_index}" if gpu_index is not None else "cpu")

    def o3d_mesh_from_pc(self, pc_vertices: np.ndarray, pc_colors: np.ndarray = None, pc_normals: np.ndarray = None):
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pc_vertices)
        if pc_colors is not None:
            if np.issubdtype(pc_colors.dtype, np.integer):
                pc_colors = pc_colors.astype(np.float64) / 255.
            pc_colors = pc_colors[:, :3].astype(np.float64).copy()
            pcd.colors = o3d.utility.Vector3dVector(pc_colors)
        if pc_normals is None:
            logger.info("pc_normals is None, estimating normals from points")
            pcd.estimate_normals()
            pcd.orient_normals_consistent_tangent_plane(min(len(pc_vertices), 100))
        else:
            pcd.normals = o3d.utility.Vector3dVector(pc_normals)
        logger.info("Generating mesh from PC with BPA (if it takes too long, consider adjusting bpa_radius)")
        stime = time.time()
        if self.bpa_radius is None:
            logger.info("bpa_radius is None, running radius estimation")
            dists = pcd.compute_nearest_neighbor_distance()
            med_dist = np.median(dists)
            bpa_radius = med_dist / np.sqrt(2)
            logger.info(f"Estimated radius: {bpa_radius}")
        else:
            bpa_radius = self.bpa_radius
        bpa_radius_range = o3d.utility.DoubleVector([bpa_radius, bpa_radius * 2])
        bpa_mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(pcd, bpa_radius_range)
        runtime = time.time() - stime
        logger.info(f"BPA done in {runtime / 3600:.2f} hours ({runtime / 60:.2f} mins)")
        return bpa_mesh

    def o3d_decimate_mesh(self, o3d_mesh: o3d.geometry.TriangleMesh):
        logger.info(f"Performing mesh decimation (to {self.subsampled_mesh_faces_count} faces)")
        stime = time.time()
        dec_mesh = o3d_mesh.simplify_quadric_decimation(self.subsampled_mesh_faces_count)
        dec_mesh.remove_degenerate_triangles()
        dec_mesh.remove_duplicated_triangles()
        dec_mesh.remove_duplicated_vertices()
        dec_mesh.remove_non_manifold_edges()
        runtime = time.time() - stime
        logger.info(f"Decimation done in {runtime / 3600:.2f} hours ({runtime / 60:.2f} mins)")
        return dec_mesh

    def generate_naive_uvmap(self, o3d_mesh: o3d.geometry.TriangleMesh):
        """Will pack faces one after another in the texture, two triangles per square

        Args:
            o3d_mesh (o3d.geometry.TriangleMesh): mesh to generate UV map for

        """
        logger.info("Generating UV map")
        mesh_faces = np.asarray(o3d_mesh.triangles)

        faces_count = len(mesh_faces)
        uv_squares_count = ((faces_count + 1) // 2)
        uv_squares_per_row = np.ceil(np.sqrt(uv_squares_count)).astype(int)
        sq_size = 1. / uv_squares_per_row.astype(np.float64)

        triangle_off = np.array([[(0.1, 0.1), (0.1, 0.8), (0.9, 0.1)],
                                 [(0.9, 0.2), (0.1, 0.9), (0.9, 0.9)]], dtype=self.np_dtype).reshape(1, 6, 2)

        scaled_triangle_off = triangle_off * sq_size
        faces_offsets = np.stack((np.arange(uv_squares_count) // uv_squares_per_row, np.arange(uv_squares_count) % uv_squares_per_row),
                                 axis=1).astype(
            self.np_dtype) * sq_size
        faces_uv = (scaled_triangle_off + faces_offsets[:, None, :]).reshape(uv_squares_count * 2, 3, 2)
        if len(mesh_faces) % 2 == 1:
            faces_uv = faces_uv[:-1]
        logger.info(f"Done, mesh faces count {len(mesh_faces)}, faces uv count {len(faces_uv)}")
        return faces_uv

    def _get_texture_pixels_position_in_3dworld(self, target_texture_coords, mesh_vertices, mesh_faces, uv_map):
        texture_coords_grid = torch.stack([x.reshape(-1) for x in torch.meshgrid(*target_texture_coords, indexing='xy')],
                                          dim=1)  # N,2
        faces_count = len(mesh_faces)
        uv_squares_count = ((faces_count + 1) // 2)
        uv_squares_per_row = np.ceil(np.sqrt(uv_squares_count)).astype(int)

        pix_faces_coords = texture_coords_grid * uv_squares_per_row
        pix_faces_int_coords = torch.floor(pix_faces_coords).long()
        inface_coords = pix_faces_coords - pix_faces_int_coords
        odd_face = (1 - inface_coords[:, 0]) < inface_coords[:, 1]
        pix_faces_inds = (pix_faces_int_coords[:, 0] * uv_squares_per_row + pix_faces_int_coords[:, 1]) * 2 + odd_face
        pix_faces_inds[pix_faces_inds >= faces_count] = faces_count - 1
        # Computing pixels XYZ coords
        pix_faces = mesh_faces[pix_faces_inds]  # N,3
        pix_faces_xyz = mesh_vertices[pix_faces.flatten()].reshape(pix_faces.shape[0], 3, 3)
        pix_faces_uv = uv_map[pix_faces_inds]  # N,3,2
        # Computing barycentric coords
        T = torch.stack([pix_faces_uv[:, 0, :] - pix_faces_uv[:, 2, :], pix_faces_uv[:, 1, :] - pix_faces_uv[:, 2, :]], dim=2)  # N,2,2
        baric_coords2 = torch.linalg.solve(T, texture_coords_grid - pix_faces_uv[:, 2, :])  # N,2
        baric_coords = torch.cat([baric_coords2, 1 - baric_coords2.sum(dim=1)[:, None]], dim=1)  # N,3
        pix_xyz = torch.matmul(baric_coords[:, None, :], pix_faces_xyz)[:, 0, :]  # N,3
        return pix_xyz

    def _generate_texture_block(self, target_texture_coords, mesh_vertices, mesh_faces, uv_map, pc_tree, pc_colors):
        resolution = (len(target_texture_coords[1]), len(target_texture_coords[0]))
        pix_xyz = self._get_texture_pixels_position_in_3dworld(target_texture_coords, mesh_vertices, mesh_faces, uv_map)
        # Querying KDTree
        dists, inds = pc_tree.query(pix_xyz.cpu().numpy(), k=self.knn, workers=-1)
        dists = torch.tensor(dists, dtype=self.torch_dtype, device=self.device)
        inds = torch.tensor(inds, dtype=torch.long, device=self.device)
        # Computing weighed sum
        w = 1. / dists
        w[~torch.isfinite(w)] = 1e6
        w[w > 1e6] = 1e6
        w_sum = w.sum(dim=1)
        target_colors = pc_colors[inds.flatten()].reshape(-1, self.knn, 3)
        pix_colors = (target_colors * w[:, :, None]).sum(dim=1) / w_sum[:, None]
        texture = pix_colors.reshape(resolution + (3,)).clamp(0, 1)
        texture = (texture * 255).cpu().numpy().astype(np.uint8)
        return texture

    def generate_texture_from_pc_block_by_block(self, o3d_mesh: o3d.geometry.TriangleMesh, uv_map: np.ndarray, pc_vertices: np.ndarray,
            pc_colors: np.ndarray,
            query_block_size: int = 2000):

        if self.pc_subsample is not None and self.pc_subsample < len(pc_vertices):
            logger.info(f"Subsampling the cloud to {self.pc_subsample} pts ({self.pc_subsample / len(pc_vertices) * 100:.2f}%)")
            np.random.seed(42)
            sub_inds = np.random.choice(len(pc_vertices), self.pc_subsample, replace=False)
            pc_vertices = pc_vertices[sub_inds]
            pc_colors = pc_colors[sub_inds]

        if np.issubdtype(pc_colors.dtype, np.integer):
            pc_colors = pc_colors.astype(np.float64) / 255.
        pc_colors = pc_colors[:, :3].astype(np.float64).copy()

        logger.info("Creating KDTree for texture generation queries")
        pc_tree = KDTree(pc_vertices)

        mesh_faces = np.asarray(o3d_mesh.triangles)
        mesh_vertices = np.asarray(o3d_mesh.vertices)
        faces_count = len(mesh_faces)
        uv_squares_count = ((faces_count + 1) // 2)

        logger.info("Raising data to device")
        mesh_faces_torch = torch.tensor(mesh_faces, device=self.device)
        mesh_vertices_torch = torch.tensor(mesh_vertices, dtype=self.torch_dtype, device=self.device)
        uv_map_torch = torch.tensor(uv_map, dtype=self.torch_dtype, device=self.device)
        pc_colors_torch = torch.tensor(pc_colors, dtype=self.torch_dtype, device=self.device)

        logger.info("Assigning pixels to faces")
        texture_coords = [(torch.arange(r, dtype=self.torch_dtype, device=self.device) + 0.5) / r for r in self.texture_resolution]
        texture_coords[1] = 1 - texture_coords[1]
        texture_coords_splits = [torch.split(tc, query_block_size) for tc in texture_coords]

        logger.info("Starting texture generation")
        for tex_ind_y, tex_coords_y in enumerate(texture_coords_splits[1]):
            for tex_ind_x, tex_coords_x in enumerate(texture_coords_splits[0]):
                logger.info(f"Generating texture block ({tex_ind_x + 1}, {tex_ind_y + 1}) of "
                            f"({len(texture_coords_splits[0])}, {len(texture_coords_splits[1])})")
                texture_block = self._generate_texture_block([tex_coords_x, tex_coords_y], mesh_vertices_torch,
                                                             mesh_faces_torch, uv_map_torch, pc_tree, pc_colors_torch)
                yield texture_block

    def compute_texture_blocks_count(self, query_block_size):
        blocks_count = np.array(self.texture_resolution + query_block_size - 1) // query_block_size
        return blocks_count

    def generate_texture_from_pc(self, o3d_mesh: o3d.geometry.TriangleMesh, uv_map: np.ndarray,
            pc_vertices: np.ndarray, pc_colors: np.ndarray, query_block_size: int = 2000):
        texture_blocks_count = self.compute_texture_blocks_count(query_block_size)
        curr_row_ind = 0
        all_texture_rows = []
        curr_texture_row = []
        for texture_block in self.generate_texture_from_pc_block_by_block(o3d_mesh, uv_map, pc_vertices, pc_colors, query_block_size):
            curr_texture_row.append(texture_block)
            curr_row_ind += 1
            if curr_row_ind == texture_blocks_count[0]:
                all_texture_rows.append(np.concatenate(curr_texture_row, axis=1))
                curr_row_ind = 0
                curr_texture_row = []
        texture = np.concatenate(all_texture_rows, axis=0)
        return texture


def meshify_pc(pc_vertices, pc_colors, pc_normals=None, subsampled_mesh_faces_count=1_000_000, texture_resolution=(30_000, 30_000), pc_subsample=None,
        max_query_size=2_000, knn=3, gpu_index=None, bpa_radius=None):
    """Turns pointcloud into a subsampled mesh with texture.

    Args:
        pc_vertices (np.ndarray): pointcloud vertices (n_vertices x 3)
        pc_colors (np.ndarray): pointcloud colors (n_vertices x 3)
        pc_normals (np.ndarray, optional): pointcloud normals (n_vertices x 3). If None, normals will be estimated from the pointcloud (default: None)
        subsampled_mesh_faces_count (int, optional): number of faces in the subsampled mesh (default: 1_000_000)
        texture_resolution (tuple, optional): texture resolution (default: (30_000, 30_000))
        pc_subsample (int, optional): number of vertices to subsample from the pointcloud (default: None)
        max_query_size (int, optional): maximum query size for texture generation (default: 2_000)
        knn (int, optional): number of nearest neighbors for texture generation (default: 3)
        gpu_index (int, optional): index of the GPU of texture generation stage. If None, CPU will be used (default: None)
        bpa_radius (float, optional): radius for ball pivoting algorithm for mesh reconstruction.
            If None, radius will be estimated automatically based on PC density

    Returns:
        np.ndarray: vertices of the mesh (V, 3)
        np.ndarray: faces of the mesh (F, 3)
        np.ndarray: per-face UV map of the mesh (F, 3, 2)
        np.ndarray: texture of the mesh (texture_resolution[0], texture_resolution[1], 3)
    """
    meshifier = PCMeshifier(subsampled_mesh_faces_count, texture_resolution, pc_subsample, max_query_size, knn, gpu_index, bpa_radius)
    o3d_mesh = meshifier.o3d_mesh_from_pc(pc_vertices, pc_colors, pc_normals)
    dec_mesh = meshifier.o3d_decimate_mesh(o3d_mesh)
    uv_map = meshifier.generate_naive_uvmap(dec_mesh)
    texture = meshifier.generate_texture_from_pc(dec_mesh, uv_map, pc_vertices, pc_colors)
    mesh_vertices = np.asarray(dec_mesh.vertices)
    mesh_faces = np.asarray(dec_mesh.triangles)
    return mesh_vertices, mesh_faces, uv_map, texture


def meshify_pc_from_file(pc_filepath, output_dir, subsampled_mesh_faces_count=1_000_000, texture_resolution=(30_000, 30_000), pc_subsample=None,
        max_query_size=2_000, knn=3, gpu_index=None, bpa_radius=None):
    """
    Turns pointcloud into a subsampled mesh with texture. Reads pointcloud from a file, writes results to a folder.
        Produces mesh.ply, uv_map.npy and texture.jpg in the target folder

    Args:
        pc_filepath: Path to a pointcloud
        output_dir: Path to a directory which will contain the result
        subsampled_mesh_faces_count (int, optional): number of faces in the subsampled mesh (default: 1_000_000)
        texture_resolution (tuple, optional): texture resolution (default: (30_000, 30_000))
        pc_subsample (int, optional): number of vertices to subsample from the pointcloud (default: None)
        max_query_size (int, optional): maximum query size for texture generation (default: 2_000)
        knn (int, optional): number of nearest neighbors for texture generation (default: 3)
        gpu_index (int, optional): index of the GPU of texture generation stage. If None, CPU will be used (default: None)
        bpa_radius (float, optional): radius in ball pivoting algorithm for mesh reconstruction.
            If None, radius will be estimated automatically based on PC density
    """

    pcd = o3d.io.read_point_cloud(pc_filepath)
    pc_vertices = np.asarray(pcd.points)
    pc_colors = np.asarray(pcd.colors)
    pc_normals = np.asarray(pcd.normals)
    if pc_normals.sum() == 0:
        pc_normals = None

    meshifier = PCMeshifier(subsampled_mesh_faces_count, texture_resolution, pc_subsample, max_query_size,
                            knn, gpu_index, bpa_radius)
    o3d_mesh = meshifier.o3d_mesh_from_pc(pc_vertices, pc_colors, pc_normals)
    dec_mesh = meshifier.o3d_decimate_mesh(o3d_mesh)
    uv_map = meshifier.generate_naive_uvmap(dec_mesh)
    texture = meshifier.generate_texture_from_pc(dec_mesh, uv_map, pc_vertices, pc_colors)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    o3d.io.write_triangle_mesh(output_dir / "mesh.ply", dec_mesh)
    imsave(output_dir / "texture.jpg", texture, quality=98)
    np.save(output_dir / "uv_map.npy", uv_map)
