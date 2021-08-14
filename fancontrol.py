#!/usr/bin/env python3
"""
Fancontrol v2.0.0  @Davide

"""
import os
import signal
import json
import time
import bottleneck as bn
import numpy as np
import paho.mqtt.client as mqtt
#from gpiozero import OutputDevice
datafile = '/etc/fancontrol.conf'
pidfile = '/tmp/fancontrol.pid'


def get_json_param():
    """
    read the config param file and load environment variables

    """
    # read file
    with open(datafile, 'r') as myfile:
        data=myfile.read()
    # parse file
    try:
        return json.loads(str(data))
    except (IndexError, ValueError,) as e:
        raise RuntimeError('Could not parse the param file') from e

def rollavg_bottlneck(a,n):
    return bn.move_mean(a, window=n,min_count = None)

def mqttConnect(obj):
    #def on_connect(client, userdata, flags, rc):
    #    if rc == 0:
    #        print("Connected to MQTT Broker!")
    #    else:
    #        print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID

    client = mqtt.Client(obj['clientID'])
    client.username_pw_set(obj['username'], obj['password'])
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.will_set(nodeStatus, payload="Offline", qos=0, retain=False)
    client.connect(obj['mqttBroker'])
    client.loop_start()

    return client


def on_connect(client, userdata, flags, rc):
    if rc == False:
     print("Connected with result code "+str(rc))
     client.publish(nodeStatus, payload="Online", qos=0, retain=True)
    else:
     print("Connected with result code "+str(rc))
     print("retry")

def on_publish(client, userdata, mid):
    if rc != false:
        print("mid_last: "+str(mid))
        print("disconnected")
        handle_killpid
    else:
        print("mid: "+str(mid))

def get_temperature():
    """Get the core temperature.

    Read file from /sys to get CPU temp in temp in C *1000

    Returns:
        int: The core temperature in thousanths of degrees Celsius.
    """
    with open('/sys/class/thermal/thermal_zone0/temp') as f:
        temp_str = f.read()

    try:
        return int(temp_str) / 1000
    except (IndexError, ValueError,) as e:
        raise RuntimeError('Could not parse temperature output.') from e

if __name__ == '__main__':

    obj = get_json_param()
    print(obj['clientID'] + ' fancontrol started')
    i= 0
    x = np.zeros( obj['MOBILE_AVG'])
    tValue = get_temperature()
    while i < ( obj['MOBILE_AVG'] - 1):
        x[i] = tValue
        i = i+1

    topicmsg = obj['topicClass'] +"/"+ obj['clientID'] +"/"+  obj['tdata']
    topicFanStatus = obj['topicClass'] +"/"+ obj['clientID'] +"/"+  obj['fanstat    us']
    nodeStatus = obj['topicClass'] +"/"+ obj['clientID'] +"/"+  obj['nodestatus'    ]

    # Validate the on and off thresholds
    if obj['OFF_THRESHOLD'] >= obj['ON_THRESHOLD']:
        raise RuntimeError('OFF_THRESHOLD must be less than ON_THRESHOLD')

    #fan = OutputDevice(obj['GPIO_PIN'] )
    fan = 0
    client = mqttConnect(obj)

    temp_old = 0
    mid=0

    while True:

        x[i] = get_temperature()
#        print(i,x[i])

        if i < ( obj['MOBILE_AVG'] - 1):
          i = i+1
        else:  i= 0

#        print (x)

        tempS = rollavg_bottlneck(x, obj['MOBILE_AVG'])
        temp = round(tempS[(obj['MOBILE_AVG'] -1)],1)


        # Start the fan if the temperature has reached the limit and the fan
        # isn't already running.
        # NOTE: `fan.value` returns 1 for "on" and 0 for "off"
        #if temp > obj['ON_THRESHOLD'] and not fan.value:
        if temp > obj['ON_THRESHOLD'] and not fan:
            #fan.on()
            fan=1
            (rc, mid) = client.publish(topicmsg, temp, qos=1)
            (rc, mid) = client.publish(topicFanStatus, "ON", qos=1)
        #elif fan.value and temp < obj['OFF_THRESHOLD']:
        elif fan        and temp < obj['OFF_THRESHOLD']:
            #fan.off()
            fan = 0
            (rc, mid) = client.publish(topicmsg, temp, qos=1)
            (rc, mid) = client.publish(topicFanStatus, "OFF", qos=1)
        elif temp != temp_old:
            (rc, mid) = client.publish(topicmsg, temp, qos=1)
            temp_old =temp

        time.sleep(obj['SLEEP_INTERVAL'])
