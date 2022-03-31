from typing import Union

import numpy as np
import trimesh
from scipy.spatial import KDTree

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
