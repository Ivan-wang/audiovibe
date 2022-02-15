sleep_time=1

if [ $# -ne 0 ]
then
	sleep_time=$1
fi

echo "*** signal A ***"
cd ../.. && python backend.py --scale 240:0 --freq 20 --duty 1 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd exp/feeling_exp2

echo "take $sleep_time seconds break"
sleep $sleep_time

echo ""
echo "*** signal B ***"
cd ../.. && python backend.py --scale 80:0 --freq 20 --duty 3 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd exp/feeling_exp2

# whether: equal energy (duty * scale) leads to equal feeling
# under condition: low duty
