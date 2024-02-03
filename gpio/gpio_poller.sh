#!/bin/bash

if [ -z $DELAY ]; then
  DELAY="1"
fi

echo "Starting GPIO polling with ${DELAY}s delay"

declare counter="0"
declare pin_0_state="2"
declare pin_1_state="2"
declare pin_2_state="2"
declare pin_3_state="2"
declare pin_4_state="2"
declare pin_5_state="2"
declare pin_6_state="2"
declare pin_7_state="2"

while true
do
  chip_id=`gpiodetect | grep ch341 | sed 's@^[^0-9]*\([0-9]\+\).*@\1@'`

  while [ -z $chip_id ]; do
    echo "CH341 chip not present"
    mosquitto_pub -h mosquitto -t alarm/ch341/status -m "0"
    sleep 5
    chip_id=`gpiodetect | grep ch341 | sed 's@^[^0-9]*\([0-9]\+\).*@\1@'`
  done

  #echo "Chip ID: ${chip_id}"

  for pin_num in 0 1 2 3 4 5 6 7
  do
    pin_val==`gpioget ${chip_id} ${pin_num}`
    pin_state=pin_${pin_num}_state

    if [ ${pin_val} != ${!pin_state} ] || [ $counter == 0 ]; then
      mosquitto_pub -h mosquitto -t alarm/circuit_${pin_num}/status -m "${pin_val}"
    fi

    declare ${pin_state}="${pin_val}"
  done

  counter=$((counter+1))
  if [ $counter -gt 20 ]; then
    #echo "Resetting counter!!"
    counter="0"
    mosquitto_pub -h mosquitto -t alarm/ch341/status -m "1"
  fi

  sleep $DELAY
done
