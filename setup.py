import sqlite3
from ping_record import start_monitoring
import threading
import time
import uuid 
import sys
import multiprocessing

def add_database_record(target) -> None:
    conn = sqlite3.connect('./database/ping_data.db')
    c = conn.cursor()
    try:
        c.execute("CREATE TABLE '"+target+"' (ID INT PRIMARY KEY NOT NULL,ping REAL );")
    except Exception as e:
        print(e)
        pass
    else:
        print("create table successfully.")
    
    try:
        cursor = c.execute("SELECT server from ping_avg where server = '"+target+"';")
    except Exception as e:
        print(e)
        pass
    else:
        available = False
        fetch = cursor.fetchall()
        try:
            if fetch[0][0] == target:
                available = True
        except Exception as e:
            print(e)
            pass

        if available == False:
            try:
                c.execute("INSERT INTO ping_avg (server,one_min_avg,five_mins_avg,ten_mins_avg,status) VALUES ('"+target+"',1,1,1,TRUE)")
            except Exception as e:
                print(e)
                pass
            else:
                print("init table ping_avg successfully.")
        else:
            print(target+" exists in ping_avg table.")
    for i in range(0,60):
        temp = str(i)
        try:
            c.execute("INSERT INTO '"+target+"' (ID,ping) VALUES ("+temp+",0 )")
        except Exception as e:
            temp = str(e).split(":")[0]
            if temp == "UNIQUE constraint failed":
                print(str(e)+", data exist.")
                break
        else:
            if i == 59:
                print("init table ping_record successfully.")

    conn.commit()
    conn.close()

def init_database() -> None:
    conn = sqlite3.connect('./database/ping_data.db')
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE ping_avg(server TEXT NOT NULL,one_min_avg REAL ,five_mins_avg REAL , ten_mins_avg REAL ,status TEXT);''')
    except Exception as e:
        print(e)
        pass
    else:
        print("init ping_avg successfully.")
    conn.commit()
    conn.close()

def clear_database(target):
    for i in range(0,60):
        temp = str(i)
        conn = sqlite3.connect('./database/ping_data.db')
        c = conn.cursor()
        c.execute("UPDATE '"+target+"' set ping = 0 where ID="+temp)
        conn.commit()
        conn.close()

class thread_set (threading.Thread):   
    def __init__(self, threadID,target):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.target = target
    def run(self):                   
        print ("threadID: "+str(self.threadID)+" Starting " + self.target)
        start_monitoring(self.target)

def start(target,i) -> None:
    thread_set(i,target).start()

def monitor_start(server:list):
    try:
        init_database()
    except Exception as e :
        print(e)
        pass
    
    for i in range(len(server)):
        try:
            add_database_record(server[i])
        except Exception as e:
            print(e)

    for i in range(len(server)):
        target = server[i]
        start(target,i)
        time.sleep(1)

global all_monitor
all_monitor = []

def monitor_process_test(servers:list):
    try:
        init_database()
    except Exception as e :
        print(e)
        pass
    
    for i in range(len(servers)):
        try:
            add_database_record(servers[i])
        except Exception as e:
            print(e)

    for server in servers:
        monitor = multiprocessing.Process(target=start_monitoring, args=(server,))
        monitor.start()
        monitor_name = {server:monitor}
        all_monitor.append(monitor_name)
