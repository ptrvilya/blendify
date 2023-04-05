from setuptools import setup, find_packages
version = '1.0.0'

with open("README.md", "r") as fi:
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

requirements = [
    "numpy",
    "scipy",
    "bpy==3.4.0"
]

features_requirements = [
    "opencv-python",    # Features: saving depth
]

utils_requirements = [
    "open3d",           # Utils: normals estimation
]

examples_requirements = [
    "smplx",            # Example 5
    "videoio",          # Examples 4,5,6
    "scikit-image",     # Examples 3,4,5,6
    "trimesh"           # Examples 2,3,4,5
]

requirements_all = features_requirements + utils_requirements + examples_requirements

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
        "features": features_requirements,
        "utils": utils_requirements,
        "examples": examples_requirements,
        "all": requirements_all
    }
)
