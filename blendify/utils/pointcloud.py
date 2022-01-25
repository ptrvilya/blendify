import trimesh
import numpy as np
from scipy.spatial import KDTree


def estimate_normals_from_mesh(pc_vertices: np.ndarray, mesh: trimesh.base.Trimesh):
    mesh_normals = mesh.vertex_normals
    tree = KDTree(mesh.vertices)
    dd, nn_index = tree.query(pc_vertices, k=5, p=2, workers=-1)
    pc_normals = mesh_normals[nn_index]
    pc_normals = pc_normals.mean(axis=1)
    pc_normals = pc_normals / (np.sqrt(pc_normals ** 2).sum(axis=1, keepdims=True))

    return pc_normals


def estimate_normals_from_pointcloud(pc_vertices: np.ndarray, backend="open3d", device="gpu"):
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
        raise RuntimeError(f"backend {backend} is not supported. Possible backends: open3d, pytorch3d.")

    return pc_normals
