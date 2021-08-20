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
