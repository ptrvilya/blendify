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
        self.smpl = smplx.create(self.smpl_root, model_type = 'smpl', gender=gender, betas=self.shape_params).to(self.device)
        self.faces = np.array(self.smpl.faces, dtype=np.int64)

    @staticmethod
    def _center_output(smpl_model, params, smpl_output):
        """Center the SMPL model local coordinate system around the root joint"""
        if 'transl' in params and params['transl'] is not None:
            transl = params['transl']
        else:
            transl = None
        apply_trans = transl is not None or hasattr(smpl_model, 'transl')
        if transl is None and hasattr(smpl_model, 'transl'):
            transl = smpl_model.transl
        diff = -smpl_output.joints[:, 0, :]
        if apply_trans:
            diff = diff + transl
        smpl_output.joints = smpl_output.joints + diff.view(-1, 1, 3)
        smpl_output.vertices = smpl_output.vertices + diff.view(-1, 1, 3)
        return smpl_output

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

        smpl_params = dict(global_orient=global_orient, body_pose=body_pose, transl=translation_params)

        with torch.no_grad():
            output = self.smpl(**smpl_params)
        output = self._center_output(self.smpl, smpl_params, output)
        return output.vertices.squeeze(0).cpu().numpy()
