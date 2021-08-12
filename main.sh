cd finetune \
    && python3 beat.py --audio ../audio/test_beat.wav \
    --len-hop 256 --len-frame 300 --min-tempo 150 --max-tempo 400 \
    && cd ..
