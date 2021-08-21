import datetime
import time
from telegram import *
from telegram.ext import *
import requests
from mcstatus import MinecraftServer
from numpy import mean
import sqlite3
from threading import Lock
import pytz
import os
import json

timezone = pytz.timezone("Asia/Taipei")
global lock
lock= Lock()
global all_monitor
all_monitor = []

try:
    os.mkdir("./database")
    os.mkdir("./logs")
    os.mkdir("./tmp")
except FileExistsError:
    pass
except Exception as e:
    print(e)    

conn = sqlite3.connect('./database/ping_data.db',check_same_thread=False)
c = conn.cursor()
offline = False
ping_record = []
stop = False


def get_current_ping(ip) -> float:
    try:
        status = MinecraftServer.lookup(ip).status()    # get ping from minecraft server
    except Exception as e:          # return any error except time out
        e = str(e)
        if e == "timed out":
            return "timeout"
        else:
            return e
    else:
        return status.latency

def get_ping_avg(target):
    lock.acquire(True)
    cursor = c.execute("SELECT one_min_avg,five_mins_avg,ten_mins_avg from ping_avg where server = '"+target+"';")
    lock.release()
    for row in cursor:
        one_min_avg= row[0]
        five_mins_avg= row[1]
        ten_mins_avg= row[2]
    ping_avg = [one_min_avg,five_mins_avg,ten_mins_avg]
    return ping_avg
    
def send_msg(status,target): 
    time = datetime.datetime.today()
    today = str(datetime.datetime.now(timezone)).split(" ")[0]
    log = "./logs/"+target+"_"+today+".log"         #log file name
    chat_ids = []
    with open("config.json","r") as f:
        data = json.load(f) 
    token = data["telegram_token"]
    try:
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        user_group = c.execute("select user_group from server where server_name = '"+str(target)+"'")
        user_group = user_group.fetchall()[0][0]
        chat_ids_temp = c.execute("select chat_id from user where user_group = '"+str(user_group)+"'")
        chat_ids_temp = chat_ids_temp.fetchall()
        for chat_id in chat_ids_temp:
            chat_ids.append(chat_id[0])
    except Exception as e:
        with open(log, 'a+') as f:
            print(str(e), file=f) 
    
    time = str(datetime.datetime.now(timezone))
    ping_avg = get_ping_avg(target)
    one_min_avg = str(round(ping_avg[0],3))
    five_mins_avg = str(round(ping_avg[1],3))
    ten_mins_avg = str(round(ping_avg[2],3))
    for chat_id in chat_ids:
        text = "["+time+"] \n" +"server:"+target+"\n"+"status:"+status+"\nping avg:\n 1min       5mins      10mins \n"+one_min_avg+"     "+five_mins_avg+"     "+ten_mins_avg     #text going to send
        url_req = "https://api.telegram.org/bot" + token + "/sendMessage" + "?chat_id=" + str(chat_id) + "&text=" + text 
    results = requests.get(url_req)   #send alert 
    # print("[{time}] message sent server:{target}".format(time=datetime.datetime.now(timezone),target=target))
    with open(log, 'a+') as f:
        print(results.json(), file=f) 

def clear_database(target):
    for i in range(0,60):
        temp = str(i)
        lock.acquire(True)
        c.execute("UPDATE '"+target+"' set ping = 1 where ID="+temp)
        conn.commit()
        lock.release()

def ping_avg(target,i,ping_record) -> None:
    lock.acquire(True)
    ping_data = c.execute("SELECT ping from '"+target+"'")
    ping_temp = []
    for row in ping_data:
        if row[0] == "None":
            ping_temp.append(0)
            continue
        ping_temp.append(row[0])
    lock.release()    
    ping_record= ping_temp
    one_min_avg = 0
    five_mins_avg = 0
    ten_mins_avg = 0
    
    if i<6 and i >0:
        one_min_avg_back = mean(ping_record[i-6:len(ping_record)])
        one_min_avg_front = mean(ping_record[:6-i])
        one_min_avg = mean(one_min_avg_back+one_min_avg_front)
    elif i >=6:
        one_min_avg = mean(ping_record[i-6:i])
    if i<36 and i> 0:
        five_mins_avg_back = mean(ping_record[i-36:len(ping_record)])
        five_mins_avg_front = mean(ping_record[:36-i])
        five_mins_avg = mean(five_mins_avg_back+five_mins_avg_front)
    elif i>=36:
        five_mins_avg = mean(ping_record[i-36:i])
    ten_mins_avg = mean(ping_record)
    lock.acquire(True)
    c.execute("UPDATE ping_avg set one_min_avg = "+str(one_min_avg)+" where server = '"+target+"';")
    c.execute("UPDATE ping_avg set five_mins_avg = "+str(five_mins_avg)+" where server = '"+target+"';")
    c.execute("UPDATE ping_avg set ten_mins_avg = "+str(ten_mins_avg)+" where server = '"+target+"';")
    conn.commit()
    lock.release()

def loop(target,offline,ping_record) -> None:
    today = str(datetime.datetime.now(timezone)).split(" ")[0]
    log = "./logs/"+target+"_"+today+".log"
    for i in range(0,60):

        ping = get_current_ping(target)

        if offline == True:
            if type(ping) == str:

                clear_database(target)

                for i in range(len(ping_record)):
                    ping_record[i] = 0

                # print("[{time}] status:offline server:{target}".format(time=datetime.datetime.now(timezone),target=target))
                with open(log, 'a+') as f:
                    print("[{time}] status:offline server:{target}".format(time=datetime.datetime.now(timezone),target=target), file=f)    
                time.sleep(10)
                continue

            if type(ping) == float or type(ping) == int:
                send_msg("online",target)
                # print("[{time}] status:online server:{target}".format(time=datetime.datetime.now(timezone),target=target))
                
                with open(log, 'a+') as f:
                    print("[{time}] status:online server:{target}".format(time=datetime.datetime.now(timezone),target=target), file=f)    
                offline = False

                lock.acquire(True)
                c.execute("UPDATE ping_avg set status = 'online' where server = '"+target+"';")
                conn.commit()
                lock.release()
                break

        if type(ping) ==str and offline == False:
            time.sleep(2)
            ping = get_current_ping(target)
            if type(ping) ==str:
                ping = 0
                send_msg("timeout",target)
            
                lock.acquire(True)
                c.execute("UPDATE ping_avg set status = 'offline' where server = '"+target+"';")
                conn.commit()
                lock.release()
            
                offline = True
                continue
        
        # print("[{time}] ping:{ping}ms server:{server}".format(time=datetime.datetime.now(timezone),server=target,ping=ping))
        with open(log, 'a+') as f:
            print("[{time}] ping:{ping}ms server:{server}".format(time=datetime.datetime.now(timezone),server=target,ping=ping), file=f) 
            
        ID = str(i)
        ping = str(ping)
        lock.acquire(True)
        c.execute("UPDATE '"+target+"' set ping = "+ping+" where ID="+ID)
        c.execute("UPDATE ping_avg set status = 'online' where server = '"+target+"';")
        conn.commit()
        lock.release()
        if i == 59:
            i = 0
        ping_avg(target,i,ping_record)
        time.sleep(10)

def start_monitoring(target):
    lock.acquire(True)
    pid = os.getpid()
    conn = sqlite3.connect('./database/user.db')
    c = conn.cursor()
    c.execute("update server monitoring = '?' where server = '?'",(pid,target))
    conn.commit()
    conn.close()
    lock.release()
    
    while offline != True:
        loop(target,offline,ping_record)
