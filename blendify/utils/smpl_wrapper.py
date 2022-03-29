import numpy as np
import torch
from smplpytorch.pytorch.smpl_layer import SMPL_Layer


class SMPLWrapper:
    """A wrapper for the smplpytorch layer
    """

    def __init__(self, smpl_root: str, gender: str, shape_params: np.ndarray, device: torch.device = None):
        self.device = torch.device(device if device is not None else "cpu")
        self.smpl_root = smpl_root
        self.shape_params = self._preprocess_param(shape_params)
        self.smpl_layer = SMPL_Layer(center_idx=0, gender=gender, model_root=self.smpl_root).to(self.device)
        self.faces = self.smpl_layer.th_faces.cpu().numpy()

    def _preprocess_param(self, param: np.ndarray) -> torch.Tensor:
        """Prepare the parameters for SMPL layer
        """
        if not isinstance(param, torch.Tensor):
            param = torch.tensor(param, dtype=torch.float32)
        param = param.to(self.device)
        return param

    def get_smpl(self, pose_params: np.ndarray, translation_params: np.ndarray) -> np.ndarray:
        """Get the SMPL mesh vertices from the target pose and global translation

        Args:
            pose_params: Pose parameters vector of shape (72)
            translation_params: Global translation vector of shape (3)

        Returns:
            np.ndarray: vertices of SMPL model
        """
        pose_params = self._preprocess_param(pose_params)
        translation_params = self._preprocess_param(translation_params)
        verts, joints = self.smpl_layer(th_pose_axisang=pose_params.unsqueeze(0),
                                        th_betas=self.shape_params.unsqueeze(0))
        return (verts.squeeze(0) + translation_params.unsqueeze(0)).cpu().numpy()
