#!/bin/bash
#
# Check_MK Plugin to Monitor and Grpah Vivarium Temperatures.
# Darren Gibbard - 4th Jan 2014
#
if [ ! `id -un` = "root" ]; then
	echo Must run as root.
	exit 1 
fi

# Set Alert Levels [ temperature (.C) ]
Low=27.5
High=29.4

# Aquire stats
USER=dalgibbard
HOST=192.168.0.32

DATA=$(ssh -o ConnectTimeout=2 ${USER}@${HOST} "cat /sys/bus/w1/devices/28-0000053cb08d/w1_slave" 2>/dev/null | sed -e 's/\n/ /g')
if [ "x$DATA" = "x" ];then
	echo "3 Viv_Temp temp=0;0;0;0; UNKNOWN - Viv Temp is UNKNOWN"
elif [[ "$DATA" =~ "YES" ]]; then
	if [[ "$DATA" =~ t=[0-9] ]]; then
		temp=$(echo "scale=3; `echo $DATA | awk '{print$22}' | awk -F= '{print$2}'` / 1000" | bc -l)
		if (( $(echo "scale=3; $temp < $Low" | bc -l) )); then
			echo "2 Viv_Temp temp=$temp;0;0;0; CRITICAL - Viv Temp is too low - $temp"
		elif (( $(echo "scale=3; $temp > $High" | bc -l) )); then
			echo "2 Viv_Temp temp=$temp;0;0;0; CRITICAL - Viv Temp is too high - $temp"
		else
			echo "0 Viv_Temp temp=$temp;0;0;0; OK - Viv Temp is OK - $temp"
		fi
	else
		echo "3 Viv_Temp temp=0;0;0;0; UNKNOWN - Viv Temp is UNKNOWN"
	fi
else
	echo "3 Viv_Temp temp=0;0;0;0; UNKNOWN - Viv Temp is UNKNOWN"
fi

