import numpy as np
import smplx
import torch


class SMPLWrapper:
    """A wrapper for the SMPL model
    """

    def __init__(self, smpl_root: str, gender: str, shape_params: np.ndarray, device: torch.device = None):
        self.device = torch.device(device if device is not None else "cpu")
        self.smpl_root = smpl_root
        self.shape_params = self._preprocess_param(shape_params)
        self.smpl = smplx.SMPL(model_path=self.smpl_root, gender=gender, betas=self.shape_params).to(self.device)
        self.faces = np.array(self.smpl.faces, dtype=np.int64)

    def _preprocess_param(self, param: np.ndarray) -> torch.Tensor:
        """Prepare the parameters for SMPL
        """
        if not isinstance(param, torch.Tensor):
            param = torch.tensor(param, dtype=torch.float32)
        param = param.to(self.device).reshape(1, -1)
        return param

    def get_smpl(self, pose_params: np.ndarray, translation_params: np.ndarray) -> np.ndarray:
        """Get the SMPL mesh vertices from the target pose and global translation

        Args:
            pose_params: Pose parameters vector of shape (72)
            translation_params: Global translation vector of shape (3)

        Returns:
            np.ndarray: vertices of SMPL model
        """
        global_orient = self._preprocess_param(pose_params[:3])
        body_pose = self._preprocess_param(pose_params[3:])
        translation_params = self._preprocess_param(translation_params)

        with torch.no_grad():
            output = self.smpl(
                global_orient=global_orient,
                body_pose=body_pose,
                transl=translation_params
            )
        return output.vertices.squeeze(0).cpu().numpy()
