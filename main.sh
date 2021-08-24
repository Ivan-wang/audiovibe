# cd finetune \
#     && python3 beat.py --audio ../audio/test_beat.wav --plot \
#     --len-hop 512 --len-frame 300 --min-tempo 30 --max-tempo 300 \
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
cd finetune \
    && python3 pitch.py --task run --audio "../audio/Liangzhu .wav" --plot \
    --chroma --chroma-alg cqt --fmin C1 \
    --len-window 2048 \
    && cd ..