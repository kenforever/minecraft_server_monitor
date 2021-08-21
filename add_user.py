import logging
import os
from typing import Text
from warnings import catch_warnings
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

USERNAME, CHATID,PERMISSION_GROUP,USER_GROUP = range(4)
server_temp = "./tmp/temp_"

def add_user(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        update.message.reply_text("please give me the username of who you want to add. dont need @.")
        return USERNAME
    else:
        update.message.reply_text("ERROR: UnauthorizedException")

def add_user_username(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    target_username = update.message.text
    temp_file = server_temp+username
    data = {'username':target_username,'chat_id':"",'user_group':"default","permission_group":"viewer"}
    have_record = check_history(username)
    print(have_record)
    if have_record == True:
        update.message.reply_text("ERROR: UserAlreadyExist")
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
            update.message.reply_text('Great! now tell me the chat id.')
            return CHATID

def add_user_chatid(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.text
    temp_file = server_temp+username
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
        data["chat_id"] = chat_id
        print(data)
        with open(server_temp+username,"w") as f:
            data = json.dumps(data)
            print(data,file=f)
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        os.remove(temp_file)
        return ConversationHandler.END
    else:
        update.message.reply_text('Great! now tell me the which group you want this user be. /skip for default group.')
        return USER_GROUP

def add_user_usergroup(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    user_group = update.message.text
    temp_file = server_temp+username
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
        data["user_group"] = user_group
        print(data)
        with open(server_temp+username,"w") as f:
            data = json.dumps(data)
            print(data,file=f)
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        os.remove(temp_file)
        return ConversationHandler.END
    else:
        update.message.reply_text('Great! now tell me the what permission you want to give this user. we have admin and viewer now. admin have full access and viewer is view only. /skip for view only.')
        return PERMISSION_GROUP

def add_user_skip_usergroup(update: Update, context: CallbackContext):
    update.message.reply_text('Skip! now tell me the what permission you want to give this user. we have admin and viewer now. admin have full access and viewer is view only. /skip for view only.')
    return PERMISSION_GROUP

def add_user_permission_group(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    permission_group = update.message.text
    temp_file = server_temp+username
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
        data["permission_group"] = permission_group
        print(data)
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        os.remove(temp_file)
        return ConversationHandler.END
    try:
        target_username = data["username"]
        chat_id = data["chat_id"]
        user_group = data["user_group"]
        permission_group = data["permission_group"]
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        c.execute("insert into user(username,chat_id,user_group,permission_group) values(?,?,?,?)",(target_username,chat_id,user_group,permission_group))
        conn.commit()
        conn.close()
    except Exception as e:
        os.remove(temp_file)
        update.message.reply_text("ERROR: "+str(e))
        return ConversationHandler.END
    else:
        os.remove(temp_file)
        update.message.reply_text('Great! Everything Done!')
        return ConversationHandler.END

def add_user_skip_permission_group(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    permission_group = update.message.text
    temp_file = server_temp+username
    try:
        with open(server_temp+username,"r") as f:
            data = json.load(f)
        print(data)
    except Exception as e:
        os.remove(temp_file)
        update.message.reply_text("ERROR: "+str(e))
        return ConversationHandler.END
    try:
        target_username = data["username"]
        chat_id = data["chat_id"]
        user_group = data["user_group"]
        permission_group = data["permission_group"]
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        c.execute("insert into user(username,chat_id,user_group,permission_group) values(?,?,?,?)",(target_username,chat_id,user_group,permission_group))
        conn.commit()
        conn.close()
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
        os.remove(temp_file)
        return ConversationHandler.END
    else:
        os.remove(temp_file)
        update.message.reply_text('Skip! Everything Done!')
        return ConversationHandler.END

def add_user_cancel(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    temp_file = server_temp+username
    try:
        os.remove(temp_file)
    except Exception as e:
        update.message.reply_text("ERROR: "+str(e))
    else:
        update.message.reply_text('Don`t worry, nothing change!')

