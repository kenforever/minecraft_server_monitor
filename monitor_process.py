import logging
import os, signal
from server_status import server_detail_all
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
import copy

ALL,BACK,START_ALL,STOP_ALL,CONTROL,MENU,STOP,START,CONTROL_ALL,PANEL = range(10)
accept_permission = {"admin"}


def monitor_menu(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id
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
            text_temp = nickname+"\nserver: "+server_name+"\npid: "+str(monitoring)+"\nuser_group: "+user_group+"\n\n"
            texts = texts + text_temp
            callback_data = {"server_name":server_name}
            callback_data = json.dumps(callback_data)
            keyboard_data = InlineKeyboardButton(nickname, callback_data=callback_data)
            keyboard_temp.insert(0,keyboard_data)
            if (i%2 == 0):
                keyboard.insert(0,keyboard_temp) 
                keyboard_temp = []

        keyboard_all = [InlineKeyboardButton("start all", callback_data=str(START_ALL)),InlineKeyboardButton("stop all", callback_data=str(STOP_ALL))]
        keyboard.insert(0,keyboard_all)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("all monitor status\n\n"+texts+"\nuse button to control them.", reply_markup=reply_markup)
        return CONTROL_ALL
    else:
        update.message.reply_text("ERROR: UnauthorizedException")
        return ConversationHandler.END

def monitor_callback_menu(update:Update, context:CallbackContext):
    chat_id = update.callback_query.message.chat_id
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
            callback_data = {"server_name":server_name}
            callback_data = json.dumps(callback_data)
            keyboard_data = InlineKeyboardButton(nickname, callback_data=callback_data)
            keyboard_temp.insert(0,keyboard_data)
            if (i%2 == 0):
                keyboard.insert(0,keyboard_temp) 
                keyboard_temp = []

        keyboard_all = [InlineKeyboardButton("start all", callback_data=str(START_ALL)),InlineKeyboardButton("stop all", callback_data=str(STOP_ALL))]
        keyboard.insert(0,keyboard_all)
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text("all monitor status\n\n"+texts+"\nuse button to control them.", reply_markup=reply_markup)
        return CONTROL_ALL
    else:
        update.callback_query.message.edit_text("ERROR: UnauthorizedException")
        return ConversationHandler.END

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
            update.callback_query.message.edit_text(servername+' starting...\n')
            server.append(servername)
            monitor_process_test(server)
            update.callback_query.message.edit_text(servername+" started!\n")
        keyboard = [[InlineKeyboardButton("back to manu", callback_data=str(MENU))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        conn.close()
        update.callback_query.message.edit_text('all monitor started.', reply_markup=reply_markup)
        return CONTROL_ALL
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
                return CONTROL_ALL
            for server in servers:
                servername = server[0]
                pid = server[3]
                texts = texts+servername+" stopping...\n"
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
        return CONTROL_ALL
    except Exception as e:
        update.callback_query.message.edit_text("ERROR: "+str(e))

def monitor_control_panel(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()
    texts = ""
    server_data = query.data
    server_data = json.loads(server_data)
    keyboard = []
    server_name = server_data["server_name"]

    conn = sqlite3.connect('./database/user.db',check_same_thread=False)
    c = conn.cursor()
    server_data = c.execute('select * from server where server_name = "'+server_name+'"')
    server_data = server_data.fetchall()
    if server_data == []:
        conn.close()
        keyboard = [[InlineKeyboardButton("back to manu", callback_data=str(MENU))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text("ERROR: NoMonitorStarted",reply_markup=reply_markup)
        return ConversationHandler.END

    user_group = server_data[0][1]
    nickname = server_data[0][2]
    monitoring = server_data[0][3]
    callback_data = {"operation":"","server_name":server_name}
    text_temp = nickname+"\n\nserver: "+server_name+"\npid: "+str(monitoring)+"\nuser_group: "+user_group+"\n\n"
    texts = texts + text_temp
    texts = texts + "use button to control."

    if monitoring == False:
        callback_data_start = copy.deepcopy(callback_data)
        callback_data_start["operation"] ="start"
        callback_data_start = json.dumps(callback_data_start)
        keyboard_temp = [InlineKeyboardButton("start", callback_data=callback_data_start)]
        keyboard.append(keyboard_temp)


    else:
        callback_data_stop = copy.deepcopy(callback_data)
        callback_data_stop["operation"] ="stop"
        callback_data_stop = json.dumps(callback_data_stop)
        keyboard_temp = [InlineKeyboardButton("stop", callback_data=callback_data_stop)]
        keyboard.append(keyboard_temp)
    
    callback_data_edit = copy.deepcopy(callback_data)
    callback_data_delete = copy.deepcopy(callback_data)
    callback_data_edit["operation"] = "edit"
    callback_data_delete["operation"] = "delete"
    callback_data_edit = json.dumps(callback_data_edit)
    callback_data_delete = json.dumps(callback_data_delete)
    
    keyboard_end = [
            InlineKeyboardButton("edit this monitor", callback_data=callback_data_edit),
            InlineKeyboardButton("DELETE this monitor", callback_data=callback_data_delete)
        ]

    keyboard_menu = [
            InlineKeyboardButton("back to manu", callback_data=str(MENU))
        ]
    keyboard.append(keyboard_end)
    keyboard.append(keyboard_menu)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.edit_text(texts,reply_markup=reply_markup)
    return CONTROL
    

def monitor_control(update:Update, context:CallbackContext):
    query = update.callback_query
    query.answer()

    server_data = query.data
    server_data = json.loads(server_data)
    operation = server_data["operation"]
    

    if operation == "start":
        monitor_start(update,context,server_data)
    elif operation == "stop":
        monitor_stop(update,context,server_data)
    elif operation == "edit":
        monitor_edit(update,context,server_data)
    elif operation == "delete":
        monitor_delete(update,context,server_data)
    return CONTROL_ALL

def monitor_edit(update:Update, context:CallbackContext,data):
    update.callback_query.message.edit_text(data)
    return ConversationHandler.END


def monitor_delete(update:Update, context:CallbackContext,data):
    chat_id = update.message.chat_id
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        update.callback_query.message.edit_text(data)            
        return ConversationHandler.END
    else:
        update.message.reply_text("ERROR: UnauthorizedException")
        return ConversationHandler.END

def monitor_start(update:Update, context:CallbackContext,server_data):
        server_name = server_data["server_name"]
        texts = server_name+" starting...\n"
        update.callback_query.message.edit_text(texts)
        server = [server_name]
        monitor_process_test(server)
        texts = texts +" started!"
        callback_data = {"server_name":server_name}
        callback_data = json.dumps(callback_data)
        keyboard= [[InlineKeyboardButton("back", callback_data=callback_data)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text(texts,reply_markup=reply_markup)
        return CONTROL_ALL

def monitor_stop(update:Update, context:CallbackContext,server_data):
        server_name = server_data["server_name"]
        texts = ""
        conn = sqlite3.connect('./database/user.db',check_same_thread=False)
        c = conn.cursor()
        data = c.execute('select * from server where server_name = "'+server_name+'"')
        data = data.fetchall()
        if data == []:
            conn.close()
            return "ERROR: NoServerInDatabase"
        
        server_name = data[0][0]
        pid = data[0][3]

        texts = texts+server_name+" stopping...\n"
        update.callback_query.message.edit_text(texts)
        os.kill(pid,signal.SIGINT)
        time.sleep(2)
        os.kill(pid,signal.SIGINT)
        
        lock.acquire(True)
        pid = os.getpid()
        conn = sqlite3.connect('./database/user.db')
        c = conn.cursor()
        c.execute("update server set monitoring = '0' where server_name = '"+server_name+"'")
        conn.commit()
        conn.close()
        lock.release()
        
        texts = texts+server_name+" stopped.\n\n"   
        server_data["operation"] = ""    
        callback_data = {"server_name":server_name}
        callback_data = json.dumps(callback_data)
        keyboard= [[InlineKeyboardButton("back", callback_data=callback_data)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text(texts,reply_markup=reply_markup)
        return CONTROL_ALL

def fallback():
    pass