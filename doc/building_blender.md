Blender wiki links: 
* [Building Blender](https://wiki.blender.org/wiki/Building_Blender);
* [Building Blender as a Python Module](https://wiki.blender.org/wiki/Building_Blender/Other/BlenderAsPyModule);
* [Building Blender on Ubuntu](https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu);

Ubuntu:
```
BLENDIFY_BLENDER_ROOT=""
BLENDIFY_SITE_PACKAGES=""

# installing dependencies
sudo apt update
sudo apt install build-essential git subversion cmake libx11-dev libxxf86vm-dev \
  libxcursor-dev libxi-dev libxrandr-dev libxinerama-dev libglew-dev

# cloning git repo
mkdir -p ${BLENDIFY_BLENDER_ROOT}/blender-git && cd ${BLENDIFY_BLENDER_ROOT}/blender-git
git clone https://git.blender.org/blender.git

# cloning and updating submodules for release branch
cd ${BLENDIFY_BLENDER_ROOT}/blender-git/blender
git checkout blender-v2.93-release && make update

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
cmake "-DCMAKE_INSTALL_PREFIX=${BLENDIFY_SITE_PACKAGES}" -DWITH_INSTALL_PORTABLE=ON .
make install
cp ${BLENDIFY_BLENDER_ROOT}/blender-git/build_linux_bpy/bin/bpy.so ${BLENDIFY_SITE_PACKAGES} 
```