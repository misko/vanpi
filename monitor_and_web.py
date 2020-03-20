import os
import can
import struct
import threading
from flask import Flask
from flask import jsonify
import redis
import json
from datetime import timezone 
import datetime 
import time
min_ts_delta = 20

def timestamp():
    dt = datetime.datetime.now() 
    utc_time = dt.replace(tzinfo = timezone.utc) 
    return utc_time.timestamp() 

app = Flask(__name__)

redisClient = redis.StrictRedis(host='localhost',
                                port=6379,
                                db=0)

#set up global
current_stats = {}

@app.route('/current_stats')
def get_current_stats():
    return jsonify(current_stats)

@app.route('/past_stats/<l>')
def get_past_stats(l):
    l=int(l)
    ts=int(timestamp())
    r=redisClient.zrangebyscore("battery_stats",ts-l,ts)
    return jsonify( [ json.loads(x) for x in r ] )

@app.route('/')
def root():
    return app.send_static_file('index.html')

def monitor_can_bus():
    os.system('sudo ifconfig can0 down')
    os.system('sudo ip link set can0 type can bitrate 250000')
    os.system('sudo ifconfig can0 up')
    can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan_ctypes', bitrate=250000)# socketcan_native
    global current_stats
    last_ts=0
    while True:
        msg = can0.recv()
        ts=timestamp()
        if msg.arbitration_id==0x150:
            data=bytes(msg)
            amps=struct.unpack('<h', data[:2])[0]
            voltage=struct.unpack('<H',data[2:4])[0]/10.0
            ah_left=struct.unpack('<H',data[4:6])[0]/10.0
            max_temp,min_temp=struct.unpack('<bb',data[6:8])
            current_stats['amps']=amps
            current_stats['v']=voltage
            current_stats['ah_left']=ah_left
            current_stats['max_temp']=max_temp
            current_stats['min_temp']=min_temp
            current_stats['ts']=ts
        elif msg.arbitration_id==0x650:
            data=bytes(msg)
            soc=struct.unpack('<B', data[0:1])[0]/2.0
            current_stats['soc']=soc
            current_stats['ts']=ts
        if ts-last_ts>min_ts_delta and ('soc' in current_stats and 'v' in current_stats):
            #add to redis
            redisClient.zadd("battery_stats", {json.dumps(current_stats):ts})
            print(json.dumps(current_stats))
            last_ts=ts
    os.system('sudo ifconfig can0 down')

if __name__ == '__main__':
    t=threading.Thread(target=monitor_can_bus)
    t.start()
    print("running app")
    app.run(host='0.0.0.0', port=80)


