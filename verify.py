import sqlite3

def get_permission_group(chat_id) -> str:
    conn = sqlite3.connect('./database/user.db')
    c = conn.cursor()
    permission = c.execute("select permission_group from user where chat_id = '"+str(chat_id)+"'")
    permission = permission.fetchall()
    try:
        permission = permission[0][0]
    except IndexError:
        conn.commit()
        conn.close()
        return "NotRegister"
    else:
        conn.commit()
        conn.close()
        return permission

def get_user_group(chat_id) -> str:
    conn = sqlite3.connect('./database/user.db')
    c = conn.cursor()
    user_group = c.execute("select user_group from user where chat_id = '"+str(chat_id)+"'")
    user_group = user_group.fetchall()
    try:
        user_group = user_group[0][0]
    except IndexError:
        conn.commit()
        conn.close()
        return "NotRegister"
    else:
        conn.commit()
        conn.close()
        return user_group   

def verify(chat_id,target_permission) ->bool:
    permission = get_permission_group(chat_id)
    if permission in target_permission:
        return True
    if permission == "NotRegister":
        return "NotRegister"
    else:
        return False

def check_history(target) -> bool:
    try:
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        data = c.execute("select server_name from server where server_name = '"+target+"';")
        data = data.fetchall()
        conn.commit()
        conn.close()
        try:
            data = data[0][0]

        except IndexError:
            return False
        else:
            return True

    except Exception as e:
        return e


def get_monitors_data():
    conn = sqlite3.connect('./database/user.db',check_same_thread=False)
    c = conn.cursor()
    data = c.execute('select * from server')
    data = data.fetchall()
    if data == []:
        conn.close()
        return "ERROR: NoServerInDatabase"

    monitors = []

    for monitor in data:
        monitor_data = []
        server_name = monitor[0]
        user_group = monitor[1]
        nickname = monitor[2]
        monitoring = monitor[3]
        if monitoring == 0:
            monitoring = False
        monitor_data.append(server_name)
        monitor_data.append(user_group)
        monitor_data.append(nickname)
        monitor_data.append(monitoring)
        monitors.append(monitor_data)
    conn.close()
    return monitors