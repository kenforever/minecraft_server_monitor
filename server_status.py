import logging
from os import getgrouplist
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
from add_server import *
from verify import *

timezone = pytz.timezone("Asia/Taipei")

detail= range(1)
ALL,BACK = range(2)

def get_ping_avg(target):
    try:
        conn = sqlite3.connect('./database/ping_data.db',check_same_thread=False)
        c = conn.cursor()
        cursor = c.execute("SELECT one_min_avg,five_mins_avg,ten_mins_avg from ping_avg where server = '"+target+"';")
        for row in cursor:
            one_min_avg= row[0]
            five_mins_avg= row[1]
            ten_mins_avg= row[2]
        ping_data = [one_min_avg,five_mins_avg,ten_mins_avg]
        return ping_data
    except Exception as e:
        print(e)

def status(update: Update, context: CallbackContext) :
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    permission = get_permission_group(chat_id)
    user_group = get_user_group(chat_id)
    if permission == "admin":
        conn = sqlite3.connect('./database/user.db',check_same_thread=False)
        c = conn.cursor()
        data = c.execute('select * from server')
        data = data.fetchall()
        if data == []:
            update.message.reply_text("ERROR: NoServerInDatabase")
            return ConversationHandler.END
        keyboard = []
        keyboard_temp =[]
        for i in range(len(data)):
            servername = data[i][0]
            nickname = data[i][2]
            keyboard_data = InlineKeyboardButton(nickname, callback_data=servername)
            keyboard_temp.insert(0,keyboard_data)
            if (i%2 == 0):
                keyboard.insert(0,keyboard_temp)
                keyboard_temp = []
        keyboard_all = [InlineKeyboardButton("all", callback_data=str(ALL))]
        keyboard.insert(0,keyboard_all)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('選擇欲查詢之伺服器:', reply_markup=reply_markup)
        return detail




def server_detail_all(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    query.answer()
    target =query.data
    time = str(datetime.datetime.now(timezone))

    conn = sqlite3.connect('./database/ping_data.db',check_same_thread=False)
    c = conn.cursor()
    texts_temp = []
    texts = ""
    data = c.execute("select * from ping_avg")
    data = data.fetchall()
    for row in data:
        server = str(row[0])
        one_min_avg = str(round(row[1],3))
        five_mins_avg = str(round(row[2],3))
        ten_mins_avg = str(round(row[3],3))
        status = str(row[4])
        text_temp = "server: "+server+"\n status: "+status+"\n ping avg:\n 1min       5mins      10mins \n"+one_min_avg+"     "+five_mins_avg+"     "+ten_mins_avg+"\n\n"
        texts_temp.append(text_temp)
    
    for text in texts_temp:
        texts = texts+text

    if texts == "":
        texts = "No server in database right now!"
        
    text = ""
    text = "["+time+"]\n"+texts
    conn.close()
    query.edit_message_text(text)
    return ConversationHandler.END

def server_detail(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    target =query.data

    conn = sqlite3.connect('./database/ping_data.db',check_same_thread=False)
    c = conn.cursor()

    status = c.execute("SELECT status from ping_avg where server = '"+target+"';")
    
    for row in status:
        status = row[0]
    time = str(datetime.datetime.now(timezone))
    ping_avg = get_ping_avg(target)
    one_min_avg = str(round(ping_avg[0],3))
    five_mins_avg = str(round(ping_avg[1],3))
    ten_mins_avg = str(round(ping_avg[2],3))
    text = "["+time+"] \n" +"server:"+target+"\nstatus:"+status+"\nping avg:\n 1min       5mins      10mins \n"+one_min_avg+"     "+five_mins_avg+"     "+ten_mins_avg     #text going to send
    conn.close()
    query.edit_message_text(text)
    return ConversationHandler.END

