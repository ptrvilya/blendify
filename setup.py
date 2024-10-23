from pkg_resources import DistributionNotFound, get_distribution
from setuptools import setup, find_packages
version = '2.0.0'

with open("docs/pip_readme.md", "r") as fi:
    long_description = fi.read()

keywords = ["rendering", "pointcloud", "blender", "mesh"]

classifiers = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Natural Language :: English',
    'Operating System :: Unix',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3'
]

# Check if any of OpenCV packages is installed, if not, install the first one
possible_opencv_packages = ("opencv-python-headless", "opencv-python", "opencv-contrib-python", "opencv-contrib-python-headless")
selected_opencv_package = possible_opencv_packages[0]
for package in possible_opencv_packages:
    try:
        get_distribution(package)
        selected_opencv_package = package
        break
    except DistributionNotFound:
        pass


requirements = [
    "numpy",
    "scipy",
    "bpy==3.6.0",
    selected_opencv_package
]

docs_requirements = [
    "sphinx",
    "myst_parser",
    "furo"
]

utils_requirements = [
    "loguru",           # Utils: logging
    "scikit-learn",     # Utils: KNN search
    "open3d",           # Utils: normals estimation, mesh reconstruction
    "smplx",            # Utils: smpl wrapper
    "torch",            # Utils: point cloud normals, texture generation
]

examples_requirements = utils_requirements + [
    "videoio",          # Examples 4,5,6
    "scikit-image",     # Examples 3
    "trimesh"           # Examples 2,3,4,5,7,8
]

requirements_all = requirements + examples_requirements + docs_requirements

setup(
    name="blendify",
    packages=find_packages(),
    version=version,
    description="Python rendering framework for Blender",
    author="Vladimir Guzov, Ilya Petrov",
    author_email="vguzov@mpi-inf.mpg.de, i.petrov@uni-tuebingen.de",
    url="https://github.com/ptrvilya/blendify",
    keywords=keywords,
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requirements,
    classifiers=classifiers,
    python_requires=">=3.10",
    extras_require={
        "utils": utils_requirements,
        "examples": examples_requirements,
        "docs": docs_requirements,
        "all": requirements_all
    }
)
