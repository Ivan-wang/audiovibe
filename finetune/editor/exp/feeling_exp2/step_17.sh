sleep_time=1

if [ $# -ne 0 ]
then
	sleep_time=$1
fi
curr_dir=$(pwd)

echo "*** signal A ***"
cd ../.. && python backend.py --scale 80:0 --freq 100 --duty 1 --duration 2.0 --mode periodic_rectangle 1>/dev/null 2>&1 && cd $curr_dir

echo "take $sleep_time seconds break"
sleep $sleep_time

echo ""
echo "*** signal B ***"
cd ../.. && python backend.py --scale 80:0 --freq 100 --duty 1 --duration 2.0 \
				--second-scale 80:0 --second-freq 10 --second-duty 3 \
				--mode complex_rectangle 1>/dev/null 2>&1 && cd $curr_dir

# how: energy matters
# under condition: complex rectangle
