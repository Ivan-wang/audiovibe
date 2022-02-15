sleep_time=3

if [ $# -ne 0 ]
then
	sleep_time=$1
fi

echo "*** signal A ***"
cd ../.. && python backend.py --scale 100:0 --freq 5 --duty 1 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd exp/feeling_exp1

echo "take $sleep_time seconds break"
sleep $sleep_time

echo ""
echo "*** signal B ***"
cd ../.. && python backend.py --scale 100:0 --freq 10 --duty 1 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd exp/feeling_exp1
