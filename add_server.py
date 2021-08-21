from typing import final
from mcstatus import server
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, chat, user
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import sqlite3
import datetime
import pytz
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from verify import *
import json
import os


server_name, user_group, nickname = range(3)
server_temp = "./tmp/temp_"



def add_server(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        update.message.reply_text('please give me the server url or ip.')
        return server_name
    else:
        update.message.reply_text("ERROR: UnauthorizedException")


def add_server_servername(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    servername = update.message.text
    data = {'server_name':servername,'user_group':"default","nickname":servername}
    try:
        status = server.MinecraftServer.lookup(servername).status()    # get ping from minecraft server
    except Exception as e:         
        e = str(e)
        update.message.reply_text("ERROR: "+str(e))
        return ConversationHandler.END
    else:
        have_record = check_history(servername)
        print(have_record)
        if have_record == True:
            update.message.reply_text("ERROR: ServerAlreadyExist")
            return ConversationHandler.END
        else:
            try:
                with open(server_temp+username, "w") as f:
                    data = json.dumps(data)
                    print(data,file=f)
            except Exception as e:
                update.message.reply_text("ERROR: "+str(e))
                return ConversationHandler.END
            else:
                update.message.reply_text('Great! now tell me what group you want it in. /skip if you want it in default group.')
                return user_group

def add_server_usergroup(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    usergroup = update.message.text
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
        data["user_group"] = usergroup
        with open(server_temp+username,"w") as f:
            data = json.dumps(data)
            print(data,file=f)
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        return ConversationHandler.END
    else:
        update.message.reply_text('Great! Now give me the nickname of this server. /skip to keep it empty.')
        return nickname

def add_server_skip_usergroup(update: Update, context: CallbackContext):
    update.message.reply_text('Skip! Now give me the nickname of this server. /skip to keep it empty.')
    return nickname

def add_server_nickname(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    nickname = update.message.text
    servername = ""
    user_group = ""
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
            servername = data["server_name"]
            usergroup = data["user_group"]
    except Exception as e:
        update.message.reply_text("ERROR: of json"+str(e))
        return ConversationHandler.END
    try:
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        c.execute("insert into server(server_name,user_group,nickname,monitoring) values(?,?,?,0)",(servername,usergroup,nickname))
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        return ConversationHandler.END
    else:
        update.message.reply_text('Great! everything set!')
        return ConversationHandler.END
    finally:
        conn.commit()
        conn.close()


def add_server_skip_nickname(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    temp_file = server_temp+username
    servername = ""
    usergroup = ""
    nickname = ""
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
        servername = data["server_name"]
        usergroup = data["user_group"]
        nickname = data["nickname"]
    except Exception as e:
        os.remove(temp_file)
        update.message.reply_text("ERROR: "+str(e))
        return ConversationHandler.END
    try:
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        c.execute("insert into server(server_name,user_group,nickname,monitoring) values(?,?,?,0)",(servername,usergroup,nickname))
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        os.remove(temp_file)
        return ConversationHandler.END
    else:
        os.remove(temp_file)
        update.message.reply_text('skip! everything set!')
        return ConversationHandler.END
    finally:
        conn.commit()
        conn.close()


def add_server_cancel(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    temp_file = server_temp+username
    try:
        os.remove(temp_file)
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
    else:
        update.message.reply_text('Don`t worry, nothing change!')