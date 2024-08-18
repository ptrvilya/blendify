from .bsdf import PrincipledBSDFMaterial, PrincipledBSDFWireframeMaterial


class MetalMaterial(PrincipledBSDFMaterial):
    def __init__(
            self, roughness=0.55, metallic=0.9, clearcoat=0.0, specular=0.5,
            clearcoat_roughness=0.0, **kwargs
    ):
        super().__init__(
            roughness=roughness, metallic=metallic, clearcoat=clearcoat, specular=specular,
            clearcoat_roughness=clearcoat_roughness, **kwargs
        )


class MetalWireframeMaterial(PrincipledBSDFWireframeMaterial):
    def __init__(
            self, roughness=0.55, metallic=0.9,
            clearcoat=0.0, specular=0.5, clearcoat_roughness=0.0,
            wireframe_thickness=0.01, wireframe_color=(0., 0., 0., 1.), **kwargs
    ):
        super().__init__(
            wireframe_thickness=wireframe_thickness, wireframe_color=wireframe_color,
            roughness=roughness, metallic=metallic, clearcoat=clearcoat, specular=specular,
            clearcoat_roughness=clearcoat_roughness, **kwargs
        )
