cd finetune \
    && python3 beat.py --audio ../audio/test_beat_short_1.wav --plot \
    --len-hop 512 --len-frame 300 --min-tempo 30 --max-tempo 300 \
    && cd ..
