import sys
import time
import paho.mqtt.client as mqtt

args = sys.argv[1:]
if len(args) < 2:
  print('Usage: python3 mqtt-pub.py <topic> <message>')
  sys.exit(1)

topic = args[0]
message = args[1]


def on_connect(client, userdata, flags, rc):
  if rc == 0:
    print('Connected to broker')

    global topic
    global message
    print(f'Sending {message} to {topic}')
    client.publish(topic, message)
  else:
    print('Connection failed')
    client.loop_stop()
    sys.exit(1)


client = mqtt.Client('MQTT-Tool-Pub')
client.on_connect = on_connect
client.connect('localhost')

client.loop_start()
time.sleep(1)
