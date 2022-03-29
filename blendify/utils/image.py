import numpy as np

from ..internal.types import Vector3d


def blend_with_background(img: np.ndarray, bkg_color: Vector3d = (1., 1., 1.)) -> np.ndarray:
    """Blend the RGBA image with uniform colored background, return RGB image

    Args:
        img: RGBA foreground image
        bkg_color: RGB uniform background color (default is white)

    Returns:
        np.ndarray: RGB image blended with background
    """
    bkg_color = np.array(bkg_color)
    if img.dtype == np.uint8:
        bkg_color_uint8 = (bkg_color*255).astype(np.uint8)
        alpha = img[:, :, 3:4].astype(np.int32)
        img_with_bkg = ((img[:, :, :3] * alpha + bkg_color_uint8[None, None, :] * (255 - alpha)) // 255).astype(np.uint8)
    else:
        alpha = img[:, :, 3:4]
        img_with_bkg = (img[:, :, :3] * alpha + bkg_color[None, None, :] * (1. - alpha))
    return img_with_bkg
