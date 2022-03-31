from setuptools import setup, find_packages
version = '1.0.0'

with open("README.md", "r") as fi:
    long_description = fi.read()

keywords = ["rendering", "pointcloud", "blender", "mesh"]

classifiers = [
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ]

requirements = [
        "numpy"
]

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
    classifiers=classifiers
)