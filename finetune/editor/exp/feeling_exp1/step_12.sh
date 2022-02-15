echo "*** signal A ***"
cd ../.. && python backend.py --scale 100:0 --freq 100 --duty 1 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd exp/feeling_exp1

# take 7 seconds break
sleep 7

echo ""
echo "*** signal B ***"
cd ../.. && python backend.py --scale 100:0 --freq 75 --duty 1 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd exp/feeling_exp1
