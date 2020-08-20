#!/usr/bin/python3
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
import pyscreenshot as ImageGrab
import smtplib
from os.path import basename
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import schedule
import time
import datetime
import bles
whos_here = []

min_ts_delta = 20

def timestamp():
    dt = datetime.datetime.now() 
    return dt.timestamp() 

app = Flask(__name__)

redisClient = redis.StrictRedis(host='localhost',
                                port=6379,
                                db=0)

redis_online=False
while not redis_online:
    try:
        redisClient.zrangebyscore("battery_stats",0,1)
    except redis.exceptions.BusyLoadingError:
        print("wait for redis to load")
        time.sleep(1)
        continue
    redis_online=True
    break

#set up global
current_stats = {}

def get_creds():
    f=open("smtp.creds",'r')
    user,password=f.readline().strip().split(',')
    f.close()
    return user,password

def send_email(subject,body,pngfiles=[]):
    sender,passwd = get_creds()
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender,passwd)
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = 'mouse9911@gmail.com'
    msg.preamble = 'Not sure what goes here'
    msg.attach(MIMEText(body))
    for file in pngfiles:
        with open(file, 'rb') as fp:
            img = MIMEImage(fp.read())
        msg.attach(img)
    server.send_message(msg)
    server.quit()

def send_report(tag=""):
    im = ImageGrab.grab()
    im.save('/home/pi/vanpi/screenshot.png')
    dt = datetime.datetime.now()
    subject="%sCFO - %s report" % (tag,str(dt))
    body=str(current_stats)
    send_email(subject,body,['/home/pi/vanpi/screenshot.png'])
    print("SENT MAIL")

def schedule_thread():
    time.sleep(60)
    send_report('start')
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule.every().day.at("21:00").do(send_report)
schedule.every().day.at("09:00").do(send_report)
schedule.every().day.at("22:00").do(send_report)
schedule.every(10).minutes.do(send_report)
schedule.every().hour.do(send_report)

@app.route('/current_stats')
def get_current_stats():
    return jsonify(current_stats)

@app.route('/past_stats/<l>')
def get_past_stats(l):
    l=int(l)
    ts=int(timestamp())
    r=redisClient.zrangebyscore("battery_stats",ts-l,ts)
    return jsonify( [ json.loads(x) for x in r ] )

@app.route('/whos_here')
def get_whos_here():
    return jsonify( whos_here )

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

def ble_scanner():
    global whos_here
    while True:
        try:
            whos_here = bles.scan()
        except:
            print("ERROR")
    

if __name__ == '__main__':
    t=threading.Thread(target=monitor_can_bus)
    t.start()
    t=threading.Thread(target=schedule_thread)
    t.start()
    t=threading.Thread(target=ble_scanner)
    t.start()
    #screen_grab()
    app.run(host='0.0.0.0', port=80)


