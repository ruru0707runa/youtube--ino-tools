#!/bin/bash
# 9本の最終確認: 長さ15-40秒・音声あり・1080x1920・フレーム抽出
cd ~/workspace/reel_shiba_test/out
for f in A1_final B1_final C1_final A2_final B2_final C2_final A3_final B3_final C3_final; do
  echo "== $f =="
  ffprobe -v error -select_streams v:0 -show_entries stream=width,height,codec_name -show_entries format=duration -show_entries stream=codec_type -of default=noprint_wrappers=1 "$f.mp4" | grep -E "codec_name|width|height|duration|codec_type"
done
mkdir -p ../work/verify
# フレーム抽出: 1.0秒(音声ON推奨表示中)と各本の中盤(テロップ確認)
ffmpeg -y -v error -ss 1.0 -i A1_final.mp4 -frames:v 1 ../work/verify/A1_t1.png
ffmpeg -y -v error -ss 1.0 -i B1_final.mp4 -frames:v 1 ../work/verify/B1_t1.png
ffmpeg -y -v error -ss 1.0 -i C1_final.mp4 -frames:v 1 ../work/verify/C1_t1.png
ffmpeg -y -v error -ss 6 -i A1_final.mp4 -frames:v 1 ../work/verify/A1_t6.png
ffmpeg -y -v error -ss 8 -i B2_final.mp4 -frames:v 1 ../work/verify/B2_t8.png
ffmpeg -y -v error -ss 5 -i C3_final.mp4 -frames:v 1 ../work/verify/C3_t5.png
ffmpeg -y -v error -ss 12 -i B3_final.mp4 -frames:v 1 ../work/verify/B3_t12.png
ffmpeg -y -v error -ss 4 -i A2_final.mp4 -frames:v 1 ../work/verify/A2_t4.png
ffmpeg -y -v error -ss 6 -i C2_final.mp4 -frames:v 1 ../work/verify/C2_t6.png
echo "frames done"; ls ../work/verify/
