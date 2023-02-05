# Table of Contents
1. [Installing blendify from git](#1-installing-blendify-from-git)
1. [Optional requirements](#2-optional-requirements)

## 1. Installing blendify from git
```bash
pip install git+https://gitlab.com/real-virtual-humans/visuals/blendify.git
```

## 2. Optional requirements
**Saving depth:**
```bash
pip install opencv-python
```

**Requirements for examples and utils:**

[PyTorch](https://pytorch.org/) with [PyTorch3d](https://github.com/facebookresearch/pytorch3d/blob/main/INSTALL.md) and
`pip install trimesh open3d smplpytorch videoio scikit-image`

To make `smplpytorch` work, SMPL model files need to be downloaded, follow the installation instructions in smplpytorch 
[README](https://github.com/gulvarol/smplpytorch/blob/master/README.md).
