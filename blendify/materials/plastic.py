from .bsdf import PrincipledBSDFMaterial, PrincipledBSDFWireframeMaterial


class PlasticMaterial(PrincipledBSDFMaterial):
    def __init__(
            self, roughness=0.3, ior=1.45, coat_ior=0.0, specular_ior=0.5,
            coat_roughness=0.0, **kwargs
    ):
        super().__init__(
            roughness=roughness, ior=ior, coat_ior=coat_ior, specular_ior=specular_ior,
            coat_roughness=coat_roughness, **kwargs
        )


class PlasticWireframeMaterial(PrincipledBSDFWireframeMaterial):
    def __init__(
            self, roughness=0.3, ior=1.45, coat_ior=0.0, specular_ior=0.5,
            coat_roughness=0.0, wireframe_thickness=0.01, wireframe_color=(0., 0., 0., 1.),
            **kwargs
    ):
        super().__init__(roughness=roughness, ior=ior, coat_ior=coat_ior, specular_ior=specular_ior,
                         coat_roughness=coat_roughness, wireframe_thickness=wireframe_thickness,
                         wireframe_color=wireframe_color, **kwargs
                         )
