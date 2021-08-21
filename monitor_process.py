import logging
import os, signal
import re
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

ALL,BACK,START_ALL,STOP_ALL,CONTROL,MENU = range(6)
STOP = range(1)

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
    username = update.callback_query.from_user.username
    chat_id = update.callback_query.chat_id
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
            print(all_monitor)
        keyboard = [[InlineKeyboardButton("back to manu", callback_data=str(MENU))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        conn.close()
        print(all_monitor)
        update.callback_query.message.edit_text('all monitor started.', reply_markup=reply_markup)
        return CONTROL
    except Exception as e:
        update.callback_query.message.edit_text("ERROR: "+str(e))

def monitor_stop_all(update:Update, context:CallbackContext):
    try:
        texts = "start to stop...\n"
        update.callback_query.message.edit_text(texts)
        print("all"+all_monitor)
        for monitor in all_monitor:
            servername = monitor[0]
            pid = monitor[1]
            texts = texts+servername+"stopping...\n"
            update.callback_query.message.edit_text(texts)
            os.kill(pid,signal.SIGINT)
            texts = texts+servername+"stopped.\n"
            update.callback_query.message.edit_text(texts)
        texts = texts+"every monitor stopped."
        keyboard = [[InlineKeyboardButton("back to manu", callback_data=str(MENU))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text(texts,reply_markup=reply_markup)
        return MENU
    except Exception as e:
        update.callback_query.message("ERROR: "+str(e))
    return CONTROL

def monitor_control(update:Update, context:CallbackContext):
    pass

def process_start_list(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        conn = sqlite3.connect('./database/user.db',check_same_thread=False)
        c = conn.cursor()
        data = c.execute('select * from server where monitor != 0')
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
        update.message.reply_text('選擇欲start之伺服器:', reply_markup=reply_markup)
    else:
        update.message.reply_text("ERROR: UnauthorizedException")
    


def process_start(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        server_temp = c.execute("SELECT server_name from server")
        server_temp = server_temp.fetchall()
        server = []
        for servernames in server_temp:
            servername = servernames[0]
            server.append(servername)
        print(server)
        try:
            monitor_process_test(server)
            print(all_monitor)
        except Exception as e:
            update.message.reply_text("ERROR: "+str(e))
        else:
            update.message.reply_text('start monitoring')
    else:
        update.message.reply_text("ERROR: UnauthorizedException")
    

def process_stop_list(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        conn = sqlite3.connect('./database/user.db',check_same_thread=False)
        c = conn.cursor()
        if all_monitor == []:
            update.message.reply_text("ERROR: NoServerInDatabase")
            return ConversationHandler.END
        keyboard = []
        keyboard_temp =[]
        for i in range(len(all_monitor)):
            monitor = list(all_monitor[i].keys())[0]
            data = c.execute('select nickname from server where server_name = "'+monitor+'"')
            nickname = data.fetchall()[0][0]
            keyboard_data = InlineKeyboardButton(nickname, callback_data=monitor)
            keyboard_temp.insert(0,keyboard_data)
            if (i%2 == 0):
                keyboard.insert(0,keyboard_temp)
                keyboard_temp = []
        keyboard_all = [InlineKeyboardButton("all", callback_data=str(ALL))]
        keyboard.insert(0,keyboard_all)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('選擇欲stop之伺服器:', reply_markup=reply_markup)
        return STOP
    else:
        update.message.reply_text("ERROR: UnauthorizedException")
        return ConversationHandler.END

def process_stop(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    target =query.data
    try:
        for monitor in all_monitor:
            monitor = list(monitor.values())[0]
            print(monitor)
            if monitor == target:
                monitor.terminate()
                update.message.reply_text('stoped')
    except Exception as e:
        print(e)

def fallback():
    pass