#! /bin/bash

mkdir ffmpegDownload
cd ffmpegDownload
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz

cd ..
mkdir -p ffmpeg/bin
cp ffmpegDownload/ffmpeg-4.4.1-amd64-static/ffmpeg ffmpeg/bin/
cd ffmpeg
zip -r ../ffmpeg.zip .
cd ..

rm -r ffmpegDownload
rm -r ffmpeg