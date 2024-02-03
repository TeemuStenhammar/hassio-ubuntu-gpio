import sys
import time
import paho.mqtt.client as mqtt

args = sys.argv[1:]
if len(args) < 1:
  print('Usage: python3 mqtt-sub.py <topic>>')
  sys.exit(1)

topic = args[0]


def on_connect(client, userdata, flags, rc):
  if rc == 0:
    print('Connected to broker')

    global topic
    print(f'Subscribing to {topic}')
    client.subscribe(topic)
  else:
    print('Connection failed')
    client.loop_stop()
    sys.exit(1)


def on_message(client, userdata, message):
  print(f'Message received: {message.topic} - {message.payload}')


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect('localhost')

client.loop_forever()
