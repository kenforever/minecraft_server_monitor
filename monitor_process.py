import logging
import os, signal
import re

from mcstatus import server
from setup import monitor_process_test
from typing import Text
from warnings import catch_warnings
from telegram import *
from telegram.ext import *
import sqlite3
import datetime
import pytz
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from verify import *
from ping_record import *

ALL,BACK,START_ALL,STOP_ALL,CONTROL,MENU,STOP,START = range(8)


def monitor_menu(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        monitors_data = get_monitors_data()
        if monitors_data == "ERROR: NoServerInDatabase":
            return ConversationHandler.END

        texts = ""
        keyboard = []
        keyboard_temp =[]
        for i in range(len(monitors_data)):
            server_name = monitors_data[i][0]
            user_group = monitors_data[i][1]
            nickname = monitors_data[i][2]
            monitoring = monitors_data[i][3]
            text_temp = nickname+"\nserver: "+server_name+"\nmonitoring? "+str(monitoring)+"\nuser_group: "+user_group+"\n\n"
            texts = texts + text_temp
            keyboard_data = InlineKeyboardButton(nickname, callback_data=server_name)
            keyboard_temp.insert(0,keyboard_data)
            if (i%2 == 0):
                keyboard.insert(0,keyboard_temp)
                keyboard_temp = []

        keyboard_all = [InlineKeyboardButton("start all", callback_data=str(START_ALL)),InlineKeyboardButton("stop all", callback_data=str(STOP_ALL))]
        keyboard.insert(0,keyboard_all)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("all monitor status\n\n"+texts+"\nuse button to control them.", reply_markup=reply_markup)
        return CONTROL
    else:
        update.message.reply_text("ERROR: UnauthorizedException")

def monitor_callback_menu(update:Update, context:CallbackContext):
    username = update.callback_query.message.from_user.username
    chat_id = update.callback_query.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        monitors_data = get_monitors_data()
        if monitors_data == "ERROR: NoServerInDatabase":
            return ConversationHandler.END

        texts = ""
        keyboard = []
        keyboard_temp =[]
        for i in range(len(monitors_data)):
            server_name = monitors_data[i][0]
            user_group = monitors_data[i][1]
            nickname = monitors_data[i][2]
            monitoring = monitors_data[i][3]
            server_data = [server_name,user_group,nickname,monitoring]
            text_temp = nickname+"\nserver: "+server_name+"\npid: "+str(monitoring)+"\nuser_group: "+user_group+"\n\n"
            texts = texts + text_temp
            keyboard_data = InlineKeyboardButton(nickname, callback_data=server_data)
            keyboard_temp.insert(0,keyboard_data)
            if (i%2 == 0):
                keyboard.insert(0,keyboard_temp)
                keyboard_temp = []

        keyboard_all = [InlineKeyboardButton("start all", callback_data=str(START_ALL)),InlineKeyboardButton("stop all", callback_data=str(STOP_ALL))]
        keyboard.insert(0,keyboard_all)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text("all monitor status\n\n"+texts+"\nuse button to control them.", reply_markup=reply_markup)
        return CONTROL
    else:
        update.callback_query.message.edit_text("ERROR: UnauthorizedException")

def monitor_start_all(update:Update, context:CallbackContext):
    try:
        conn = sqlite3.connect('./database/user.db',check_same_thread=False)
        c = conn.cursor()
        servers = c.execute('select * from server where monitoring = 0')
        servers = servers.fetchall()
        if servers == []:
            update.callback_query.message.edit_text("ERROR: NoMonitorStop")
            conn.close()
            return ConversationHandler.END
        server = []
        for servernames in servers:
            servername = servernames[0]
            server.append(servername)
            print(server)
            monitor_process_test(server)
        keyboard = [[InlineKeyboardButton("back to manu", callback_data=str(MENU))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        conn.close()
        update.callback_query.message.edit_text('all monitor started.', reply_markup=reply_markup)
        return CONTROL
    except Exception as e:
        update.callback_query.message.edit_text("ERROR: "+str(e))

def monitor_stop_all(update:Update, context:CallbackContext):
    keyboard = [[InlineKeyboardButton("back to manu", callback_data=str(MENU))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        texts = "start to stop...\n\n"
        update.callback_query.message.edit_text(texts)
        try:
            conn = sqlite3.connect('./database/user.db',check_same_thread=False)
            c = conn.cursor()
            servers = c.execute('select * from server where monitoring != 0')
            servers = servers.fetchall()
            if servers == []:
                update.callback_query.message.edit_text("ERROR: NoMonitorStarted",reply_markup=reply_markup)
                conn.close()
                return ConversationHandler.END
            for server in servers:
                servername = server[0]
                pid = server[3]
                texts = texts+servername+"stopping...\n"
                update.callback_query.message.edit_text(texts)
                os.kill(pid,signal.SIGINT)
                time.sleep(2)
                os.kill(pid,signal.SIGINT)
                
                lock.acquire(True)
                pid = os.getpid()
                conn = sqlite3.connect('./database/user.db')
                c = conn.cursor()
                c.execute("update server set monitoring = '0' where server_name = '"+servername+"'")
                conn.commit()
                conn.close()
                lock.release()
                
                texts = texts+servername+" stopped.\n\n"
                update.callback_query.message.edit_text(texts)
        except Exception as e:
            print(e)
        texts = texts+"every monitor stopped."
        update.callback_query.message.edit_text(texts,reply_markup=reply_markup)
        return CONTROL
    except Exception as e:
        update.callback_query.message.edit_text("ERROR: "+str(e))

def monitor_control(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    texts = ""
    server_data = query.data
    server_name = server_data[0]
    user_group = server_data[1]
    nickname = server_data[2]
    monitoring = server_data[3]
    text_temp = nickname+"\n\nserver: "+server_name+"\npid: "+str(monitoring)+"\nuser_group: "+user_group+"\n\n"
    texts = texts + text_temp
    texts = texts + "use button to control."
    keyboard= [
        [InlineKeyboardButton("start", callback_data=[str(START),server_name]),
        InlineKeyboardButton("stop", callback_data=str(STOP))]
        [InlineKeyboardButton("back to manu", callback_data=str(MENU))]
                    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(texts,reply_markup=reply_markup)
    return CONTROL

def monitor_start(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    server_data = query.data
    print(server_data)
    pass

def monitor_stop(update:Update, context:CallbackContext):
    pass

# def process_start(update:Update, context:CallbackContext):
#     username = update.message.from_user.username
#     chat_id = update.message.chat_id
#     accept_permission = {"admin"}
#     have_permission = verify(chat_id,accept_permission)
#     if have_permission == True:
#         conn = sqlite3.connect('./database/user.db')
#         c = conn.cursor()
#         server_temp = c.execute("SELECT server_name from server")
#         server_temp = server_temp.fetchall()
#         server = []
#         for servernames in server_temp:
#             servername = servernames[0]
#             server.append(servername)
#         print(server)
#         try:
#             monitor_process_test(server)
#             print(all_monitor)
#         except Exception as e:
#             update.message.reply_text("ERROR: "+str(e))
#         else:
#             update.message.reply_text('start monitoring')
#     else:
#         update.message.reply_text("ERROR: UnauthorizedException")
    

# def process_stop(update:Update, context:CallbackContext):
#     query = update.callback_query
#     query.answer()
#     target =query.data
#     try:
#         for monitor in all_monitor:
#             monitor = list(monitor.values())[0]
#             print(monitor)
#             if monitor == target:
#                 monitor.terminate()
#                 update.message.reply_text('stoped')
#     except Exception as e:
#         print(e)

def fallback():
    pass