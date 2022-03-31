"""
Code taken from https://github.com/vguzov/cloudrender/blob/main/cloudrender/camera/trajectory.py
"""
from typing import Sequence

import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
from scipy.signal.windows import gaussian
from scipy.spatial.transform import Rotation, Slerp


class Trajectory:
    def __init__(self):
        self.trajectory = []

    def set_trajectory(self, keypoints):
        self.trajectory = [{k: np.array(v) for k, v in x.items()} for x in keypoints]

    def find_closest_kp_in_traj(self, time: float):
        times = np.array([x['time'] for x in self.trajectory])
        times_diff = times - time
        times_mask = times_diff > 0
        if times_mask.sum() == 0:
            return self.trajectory[-1], self.trajectory[-1]
        times_inds = np.flatnonzero(times_mask)
        curr_ind = times_inds[0]
        if curr_ind == 0:
            return self.trajectory[0], self.trajectory[0]
        return self.trajectory[curr_ind], self.trajectory[curr_ind-1]

    def serialize_trajectory(self):
        """Make trajectory json-serializable

        Returns:
            List[dict]: trajectory keypoints - each keypoint has "time", "position" and "quaternion"
        """
        s_traj = [{k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in x.items()} for x in self.trajectory]
        return s_traj

    def sort_trajectory(self):
        times = [x['time'] for x in self.trajectory]
        ind_sorted = np.argsort(times)
        self.trajectory = [self.trajectory[k] for k in ind_sorted]
        return ind_sorted

    def add_keypoint(self, quaternion: Sequence[float], position: Sequence[float],
                     time: float, check_time: bool = True):
        keypoint = {"position": np.array(position), "quaternion": np.array(quaternion), "time": time}
        if check_time:
            times = np.array([x['time'] for i, x in enumerate(self.trajectory)])
            diff = times - keypoint['time']
            if np.any(np.abs(diff) < 1e-4):
                return
        self.trajectory.append(keypoint)
        self.sort_trajectory()

    def rot_gaussian_smoothing(self, rots, sigma=5.):
        def get_rot_ind(ind):
            while ind >= len(rots) or ind < 0:
                if ind >= len(rots):
                    ind = 2 * len(rots) - 1 - ind
                if ind < 0:
                    ind = -ind
            return ind

        winradius = round(2 * 3 * sigma)
        if winradius < 1:
            return rots
        weights = gaussian(winradius * 2 + 1, sigma)
        res = []
        for ind in range(len(rots)):
            window_inds = [get_rot_ind(i) for i in range(ind - winradius, ind + winradius + 1)]
            res.append(rots[window_inds].mean(weights))
        return res

    def refine_trajectory(self, time_step: float = 1/60., interp_type: str = "quadratic", smoothness: float = 5.0):
        """Refines the trajectory by creating keypoints inbetween existion ones via interpolation

        Args:
            time_step (float): how often to create new points
            interp_type (str): interpolation type, "linear", "quadratic", "cubic"
            smoothness (float): how hard to smooth the pose trajectory

        Returns:
             List[dict]: trajectory keypoints - each keypoint has "time", "position" and "quaternion"
        """
        min_pts_for_interp = {"linear": 2, "quadratic": 3, "cubic": 4}
        assert interp_type in min_pts_for_interp.keys(), \
            f"Available interpolations are: {list(min_pts_for_interp.keys())}"
        if len(self.trajectory) < min_pts_for_interp[interp_type]:
            print(f'Not enough points for interpolation with "{interp_type}", returning unchanged')
            return
        start_time = self.trajectory[0]['time']
        end_time = self.trajectory[-1]['time']
        cam_times = [x['time'] for x in self.trajectory]
        cam_rots = Rotation.from_quat([np.roll(x['quaternion'], -1) for x in self.trajectory])
        cam_poses = [x['position'] for x in self.trajectory]
        rot_slerp = Slerp(cam_times, cam_rots)
        interp_times = np.concatenate([np.arange(start_time, end_time, time_step), [end_time]])
        interp_rots = rot_slerp(interp_times)
        pos_intrp = interp1d(cam_times, cam_poses, axis=0, kind=interp_type)
        interp_poses = pos_intrp(interp_times)
        interp_poses = np.array(list(zip(*[gaussian_filter1d(x, smoothness) for x in zip(*interp_poses)])))
        interp_rots = self.rot_gaussian_smoothing(interp_rots, smoothness)
        interp_quats = [np.roll(x.as_quat(), 1) for x in interp_rots]
        interp_traj = [{'position': interp_poses[i], 'quaternion': interp_quats[i], 'time': interp_times[i]}
                       for i in range(len(interp_times))]
        self.trajectory = interp_traj

        return interp_traj
