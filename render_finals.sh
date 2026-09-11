#!/bin/zsh
cd "/Users/yosh/work/Video AI/ad-prototype"
npx remotion render src/index.ts MiraiCM out/final_A.mp4 2>&1 | tail -1
npx remotion render src/index.ts MiraiCM-B out/final_B.mp4 2>&1 | tail -1
npx remotion render src/index.ts MiraiCM-C out/final_C.mp4 2>&1 | tail -1
for v in A B C; do
  npx remotion ffmpeg -y -i "out/final_$v.mp4" -c:v libx264 -crf 33 -preset veryfast -c:a aac -b:a 96k "out/final_${v}_preview.mp4" 2>/dev/null | tail -0
done
ls -la out/final_*
echo DONE
