from typing import Dict, Iterable, Union, Sequence

import numpy as np

from . import primitives
from .base import Renderable
from .mesh import Mesh
from .pointcloud import PointCloud
from ..colors import UniformColors
from ..colors.base import Colors, ColorsList
from ..internal import Singleton
from ..internal.types import Vector3d, RotationParams
from ..materials.base import Material, MaterialList


class RenderablesCollection(metaclass=Singleton):
    def __init__(self):
        self._renderables: Dict[str, Renderable] = dict()

    # =================================================== PointCloud ===================================================
    def add_pointcloud(
            self,
            vertices: np.ndarray,
            material: Material,
            colors: Colors,
            point_size: float = 0.006,
            base_primitive: str = "CUBE",
            particle_emission_strength: int = 1,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> PointCloud:
        """Add PointCloud object to the scene.
        The object supports uniform (UniformColors) and per-vertex (VertexColors) coloring.

        Args:
            vertices (np.ndarray): point cloud vertices
            material (Material): Material instance
            colors (Colors): VertexColors or UniformColors instance
            point_size (float, optional): size of a primitive, representing each vertex (default: 0.006)
            base_primitive (str, optional): type of primitive for representing each point
                (possible values are PLANE, CUBE, SPHERE, default: CUBE)
            particle_emission_strength (int, optional): strength of the emission from each primitive. This is used to
                increase realism. Values <= 0 turn emission off, values > 0 set the power of emission (default: 1)
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            PointCloud: created and added to the scene object
        """
        tag = self._process_tag(tag, "PointCloud")
        obj = PointCloud(
            vertices=vertices, material=material, colors=colors, point_size=point_size, base_primitive=base_primitive,
            particle_emission_strength=particle_emission_strength, rotation_mode=rotation_mode, rotation=rotation, translation=translation,
            tag=tag
        )
        self._renderables[tag] = obj
        return obj

    # =============================================== End of PointCloud ================================================

    # ============================================ Mesh and Mesh Primitives ============================================
    def add_mesh(
            self,
            vertices: np.ndarray,
            faces: np.ndarray,
            material: Union[Material, MaterialList],
            colors: Union[Colors, ColorsList],
            faces_material: Sequence[Sequence[int]] = None,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> Mesh:
        """Add Mesh object to the scene.
        The object supports uniform (UniformColors), per-vertex (VertexColors), per-vertex uv (VertexUV),
        per-face uv (FacesUV) and texture (TextureColors and FileTextureColors) coloring.

        Args:
            vertices (np.ndarray): mesh vertices
            faces (np.ndarray): mesh faces
            material (Union[Material, MaterialList]): Material instance or list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or list of Colors instances
            faces_material (Sequence[Sequence[int]], optional): for each face, the material index assigned to it
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            Mesh: created and added to the scene object
        """
        tag = self._process_tag(tag, "Mesh")
        obj = Mesh(
            vertices=vertices, faces=faces, material=material, colors=colors, rotation_mode=rotation_mode,
            rotation=rotation, translation=translation, tag=tag, faces_material=faces_material
        )
        self._renderables[tag] = obj
        return obj

    def add_cube_mesh(
            self,
            size: float,
            material: Union[Material, MaterialList],
            colors: Union[Colors, ColorsList],
            faces_material: Sequence[Sequence[int]] = None,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.CubeMesh:
        """Add primitives.CircleMesh object to the scene.
        The object supports only uniform coloring (UniformColors).

        Args:
            size (float): size of a primitive in [0, inf]
            material (Union[Material, MaterialList]): Material instance or list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or list of Colors instances
            faces_material (Sequence[Sequence[int]], optional): for each face, the material index assigned to it
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.CircleMesh: created and added to the scene object
        """
        tag = self._process_tag(tag, "Cube")
        obj = primitives.CubeMesh(
            size=size, material=material, colors=colors, rotation_mode=rotation_mode, rotation=rotation,
            translation=translation, tag=tag, faces_material=faces_material
        )
        self._renderables[tag] = obj
        return obj

    def add_circle_mesh(
            self,
            radius: float,
            material: Union[Material, MaterialList],
            colors: Union[Colors, ColorsList],
            faces_material: Sequence[Sequence[int]] = None,
            num_vertices: int = 32,
            fill_type: str = "NGON",
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.CircleMesh:
        """Add primitives.CircleMesh object to the scene.
        The object supports only uniform coloring (UniformColors).

        Args:
            radius (float): radius of a primitive in [0, inf]
            material (Union[Material, MaterialList]): Material instance or list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or list of Colors instances
            faces_material (Sequence[Sequence[int]], optional): for each face, the material index assigned to it
            num_vertices (int, optional): number of vertices in primitive in [3, 10000000] (default: 32)
            fill_type (str, optional): fill type, one of [NOTHING, NGON, TRIFAN] (default: NGON)
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.CircleMesh: created and added to the scene object
        """
        tag = self._process_tag(tag, "Circle")
        obj = primitives.CircleMesh(
            radius=radius, material=material, colors=colors, num_vertices=num_vertices, fill_type=fill_type,
            rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag, faces_material=faces_material
        )
        self._renderables[tag] = obj
        return obj

    def add_cylinder_mesh(
            self,
            radius: float,
            height: float,
            material: Union[Material, MaterialList],
            colors: Union[Colors, ColorsList],
            faces_material: Sequence[Sequence[int]] = None,
            num_vertices: int = 32,
            fill_type: str = "NGON",
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.CylinderMesh:
        """Add primitives.CylinderMesh object to the scene.
        The object supports only uniform coloring (UniformColors).

        Args:
            radius (float): radius of a primitive in [0, inf]
            height (float): height of a primitive in [0, inf]
            material (Union[Material, MaterialList]): Material instance or list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or list of Colors instances
            faces_material (Sequence[Sequence[int]], optional): for each face, the material index assigned to it
            num_vertices (int, optional): number of vertices in primitive in [3, 10000000] (default: 32)
            fill_type (str, optional): fill type, one of [NOTHING, NGON, TRIFAN] (default: NGON)
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.CylinderMesh: created and added to the scene object
        """
        tag = self._process_tag(tag, "Cylinder")
        obj = primitives.CylinderMesh(
            radius=radius, height=height, material=material, colors=colors, num_vertices=num_vertices,
            fill_type=fill_type, rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag, faces_material=faces_material
        )
        self._renderables[tag] = obj
        return obj

    def add_plane_mesh(
            self,
            size: float,
            material: Union[Material, MaterialList],
            colors: Union[Colors, ColorsList],
            faces_material: Sequence[Sequence[int]] = None,
            shadow_catcher: bool = False,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.PlaneMesh:
        """Add primitives.PlaneMesh object to the scene.
        The object supports only uniform coloring (UniformColors).

        Args:
            size (float): size of a plane in [0, inf]
            material (Union[Material, MaterialList]): Material instance or list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or list of Colors instances
            faces_material (Sequence[Sequence[int]], optional): for each face, the material index assigned to it
            shadow_catcher (bool, optional): if True, the plane will act as a shadow catcher (default: False)
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.PlaneMesh: created and added to the scene object
        """
        tag = self._process_tag(tag, "Plane")
        obj = primitives.PlaneMesh(
            size=size, material=material, colors=colors, shadow_catcher=shadow_catcher,
            rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag, faces_material=faces_material
        )
        self._renderables[tag] = obj
        return obj

    # ======================================== End of Mesh and Mesh Primitives =========================================

    # ============================================= Parametric Primitives ==============================================
    def add_ellipsoid_nurbs(
            self,
            radius: Vector3d,
            material: Material,
            colors: UniformColors,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.EllipsoidNURBS:
        """Add primitives.EllipsoidNURBS object to the scene.
        Implemented as NURBS Sphere that is rescaled along axes, supports only uniform coloring (UniformColors).

        Args:
            radius (float): radius of a primitive in [0, inf]
            material (Material): Material instance
            colors (UniformColors): UniformColors instance
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.EllipsoidNURBS: created and added to the scene object
        """
        tag = self._process_tag(tag, "Ellipsoid")
        obj = primitives.EllipsoidNURBS(
            radius=radius, material=material, colors=colors, rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
        )
        self._renderables[tag] = obj
        return obj

    def add_sphere_nurbs(
            self,
            radius: float,
            material: Material,
            colors: UniformColors,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.SphereNURBS:
        """Add primitives.SphereNURBS object to the scene.
        The object supports only uniform coloring (UniformColors).

        Args:
            radius (float): radius of a primitive in [0, inf]
            material (Material): Material instance
            colors (UniformColors): UniformColors instance
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.SphereNURBS: created and added to the scene object
        """
        tag = self._process_tag(tag, "Sphere")
        obj = primitives.SphereNURBS(
            radius=radius, material=material, colors=colors, rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
        )
        self._renderables[tag] = obj
        return obj

    def add_curve_nurbs(
            self,
            keypoints: np.ndarray,
            radius: float,
            material: Material,
            colors: UniformColors,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> primitives.CurveBezier:
        """Add primitives.CurveBezier object to the scene.
        Keypoints are intermediate points of the Bezier Curve. The object supports
        only uniform coloring (UniformColors).

        Args:
            keypoints (np.ndarray): keypoints for the curve
            radius (float): radius of a primitive in [0, inf]
            material (Material): Material instance
            colors (UniformColors): UniformColors instance
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created object in Blender. If None is passed, the tag
                is automatically generated (default: None)

        Returns:
            primitives.CurveBezier: created and added to the scene object
        """
        tag = self._process_tag(tag, "Curve")
        obj = primitives.CurveBezier(
            keypoints=keypoints, radius=radius, material=material, colors=colors, rotation_mode=rotation_mode, rotation=rotation,
            translation=translation, tag=tag
        )
        self._renderables[tag] = obj
        return obj

    # ========================================== End of Parametric Primitives ==========================================

    def _process_tag(self, tag: str, default_prefix: str = "Renderable"):
        renderable_keys = self._renderables.keys()

        if tag is None:
            _tag = default_prefix + "_{:03d}"
            index = 0
            while _tag.format(index) in renderable_keys:
                index += 1
            tag = _tag.format(index)
        elif tag in renderable_keys:
            raise RuntimeError(f"Object with tag {tag} is already in collection.")

        return tag

    def keys(self):
        return self._renderables.keys()

    def values(self):
        return self._renderables.values()

    def items(self):
        return self._renderables.items()

    def remove(self, obj_or_tag: Union[Renderable, str]):
        assert isinstance(obj_or_tag, (Renderable, str)), "Only Renderable object or it's tag is allowed"
        if isinstance(obj_or_tag, str):
            tag = obj_or_tag
        else:
            obj = obj_or_tag
            tag = obj.tag
        self.__delitem__(tag)

    def __getitem__(self, key: str) -> Renderable:
        return self._renderables[key]

    def __delitem__(self, key: str):
        self._renderables[key]._blender_remove_object()
        del self._renderables[key]

    def __iter__(self) -> Iterable:
        return iter(self._renderables)

    def __len__(self) -> int:
        return len(self._renderables)

    def _reset(self):
        self._renderables = dict()
