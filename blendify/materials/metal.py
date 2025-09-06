from .bsdf import PrincipledBSDFMaterial, PrincipledBSDFWireframeMaterial


class MetalMaterial(PrincipledBSDFMaterial):
    def __init__(
            self, roughness=0.55, metallic=0.9, coat_ior=0.0, specular_ior=0.5,
            coat_roughness=0.0, **kwargs
    ):
        super().__init__(
            roughness=roughness, metallic=metallic, coat_ior=coat_ior, specular_ior=specular_ior,
            coat_roughness=coat_roughness, **kwargs
        )


class MetalWireframeMaterial(PrincipledBSDFWireframeMaterial):
    def __init__(
            self, roughness=0.55, metallic=0.9,
            coat_ior=0.0, specular_ior=0.5, coat_roughness=0.0,
            wireframe_thickness=0.01, wireframe_color=(0., 0., 0., 1.), **kwargs
    ):
        super().__init__(
            wireframe_thickness=wireframe_thickness, wireframe_color=wireframe_color,
            roughness=roughness, metallic=metallic, coat_ior=coat_ior, specular=specular,
            coat_roughness=coat_roughness, **kwargs
        )
