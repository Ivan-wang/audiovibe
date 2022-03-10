curr_path=`pwd`

echo "python demo.py --audio ${curr_path}/../audio/m1_22k.wav --task run --vibmode hrps_split \
--audmode stft,pitchpyin --config configs/hrps_split_demo.py"

python demo.py --audio "${curr_path}/../audio/m1_22k.wav" --task run --vibmode hrps_split --audmode stft,pitchpyin \
--config configs/hrps_split_demo.py

#cd finetune \
#    && python3 rmse.py --audio ../audio/test_beat_short_1.wav --task build --plot \
#    --len-window 2048 && cd ..

# cd finetune \
#     && python3 melspec.py --audio ../audio/test_beat_short_1.wav --task build --plot \
#     --len-hop 512 --len-window 2048 --n-mels 128 --fmax 512 \
#     && cd ..
# cd finetune \
#     && python3 beat.py --audio ../audio/test_beat_short_0.wav --plot \
#     --len-hop 512 --len-frame 50 --min-tempo 30 --max-tempo 300 \
#     && cd ..

# To finetune pitch extraction
# Note: --pitch-alg == {pyin, yin}
# Note: --yin-thres doesn't work when --pitch-alg == pyin
# cd finetune \
#     && python3 pitch.py --task run --audio "../audio/Liangzhu .wav" --plot \
#     --pitch --pitch-alg pyin --fmin C2 --fmax C7 --yin-thres 0.8 \
#     --len-window 2048 \
#     && cd ..

# To finetune chroma extraction
# Note: --chroma-alg == {stft, cqt}
# Note: when --chroma-alg == stft, no finetuning parameters
# Note: when --chroma-alg == cqt, finetune --fmin,
# cd finetune \
#     && python3 pitch.py --task run --audio "../audio/Liangzhu .wav" \
#     --chroma --chroma-alg cqt --fmin C1 \
#     --len-window 2048 \
#     && cd ..
