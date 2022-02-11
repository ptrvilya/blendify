#!/bin/sh
mkdir 05_assets
cd 05_assets
wget "https://nextcloud.mpi-klsb.mpg.de/index.php/s/AESiBaXXyagNmrE/download" -O scene_texture.jpg
wget "https://nextcloud.mpi-klsb.mpg.de/index.php/s/QCjTsJqSSrNb5nJ/download" -O scene_mesh.ply
wget "https://nextcloud.mpi-klsb.mpg.de/index.php/s/dNtecaSTPkYoKey/download" -O scene_face_uvmap.npy
wget "https://nextcloud.mpi-klsb.mpg.de/index.php/s/a2SYDcoPc5FoCwe/download" -O animation_data.json