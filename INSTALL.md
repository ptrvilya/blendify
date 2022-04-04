# Table of Contents
1. [Installing blendify from git](#1-installing-blendify-from-git)
1. [Building Blender Python module](#2-building-blender-python-module)
   * [Pre-built binaries for Ubuntu](#pre-built-binaries-for-ubuntu)
   * [Building instructions](#building-instructions)
1. [Optional requirements](#3-optional-requirements)

## 1. Installing blendify from git
```bash
pip install git+https://gitlab.com/real-virtual-humans/visuals/blendify.git
```


## 2. Building Blender Python module

### Pre-built binaries for Ubuntu
Pre-built library for Python 3.9 and Blender 2.93 (built on Ubuntu 20.04) can be found [here](https://nextcloud.mpi-klsb.mpg.de/index.php/s/qzf2EjtydBf7SnK).

The `bpy.so` and `2.93` folder is to be copied into Python's site-packages, i.e.:
```bash
cp -r bpy.so 2.93 <path to lib/python3.9/site-packages/>
```

Resulting file tree:
```
|site-packages
└──2.93
|  └──datafiles
|  |  |  ...
|  └──scripts
|  |  |  ...
└──bpy.so
```

### Building instructions
Blender wiki links: 
* [Building Blender](https://wiki.blender.org/wiki/Building_Blender);
* [Building Blender as a Python Module](https://wiki.blender.org/wiki/Building_Blender/Other/BlenderAsPyModule);
* [Building Blender on Ubuntu](https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu);

Ubuntu:
```bash
BLENDIFY_BLENDER_ROOT=""
PYTHON_SITE_PACKAGES=""
BLENDER_VERSION="v2.93"

# installing dependencies
sudo apt update
sudo apt install build-essential git subversion cmake libx11-dev libxxf86vm-dev \
  libxcursor-dev libxi-dev libxrandr-dev libxinerama-dev libglew-dev

# cloning git repo
mkdir -p ${BLENDIFY_BLENDER_ROOT}/blender-git && cd ${BLENDIFY_BLENDER_ROOT}/blender-git
git clone https://git.blender.org/blender.git

# cloning and updating submodules for release branch
cd ${BLENDIFY_BLENDER_ROOT}/blender-git/blender
git checkout blender-${BLENDER_VERSION}-release && make update

# downloading pre-build libraries
mkdir -p ${BLENDIFY_BLENDER_ROOT}/blender-git/lib && cd ${BLENDIFY_BLENDER_ROOT}/blender-git/lib 
svn checkout https://svn.blender.org/svnroot/bf-blender/trunk/lib/linux_centos7_x86_64

# building bpy
cd ${BLENDIFY_BLENDER_ROOT}/blender-git/blender
make update
make BUILD_CMAKE_ARGS="-D WITH_PYTHON_INSTALL=OFF \
  WITH_AUDASPACE=OFF WITH_PYTHON_MODULE=ON" bpy

# installing bpy
cd ${BLENDIFY_BLENDER_ROOT}/blender-git/build_linux_bpy
cmake "-DCMAKE_INSTALL_PREFIX=${PYTHON_SITE_PACKAGES}" -DWITH_INSTALL_PORTABLE=ON .
make install
cp ${BLENDIFY_BLENDER_ROOT}/blender-git/build_linux_bpy/bin/bpy.so ${PYTHON_SITE_PACKAGES}
```


## 3. Optional requirements
**Saving depth:**
```bash
sudo apt-get install libopenexr-dev
pip install OpenEXR
```

**Requirements for examples and utils:**

[PyTorch](https://pytorch.org/) with [PyTorch3d](https://github.com/facebookresearch/pytorch3d/blob/main/INSTALL.md) and
`pip install trimesh open3d smplpytorch videoio scikit-image`

To make `smplpytorch` work, SMPL model files need to be downloaded, follow the install instructions in smplpytorch 
[README](https://github.com/gulvarol/smplpytorch/blob/master/README.md).