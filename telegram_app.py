#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards. For an in-depth explanation, check out
 https://git.io/JOmFw.
"""
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
from server_status import *
from setup import *
import multiprocessing as mp
import os
import sys


timezone = pytz.timezone("Asia/Taipei")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def help_command(update: Update, context: CallbackContext) -> None:
    """Displays info on how to use the bot."""
    update.message.reply_text("/status choose which server you want to watch.\n\
                                /get_chat_id get your chat_id.\
                                /setup init database.\
                                /add_server add server to mointor database.")

def setup(update:Update, context:CallbackContext) -> None:
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    conn = sqlite3.connect('./database/user.db')
    c = conn.cursor()

    try: 
        temp = str(chat_id)
        permission = c.execute("select permission_group from user where chat_id = '"+str(chat_id)+"'")
        permission = permission.fetchall()
        try:
            permission = permission[0][0]
        except IndexError:
            update.message.reply_text("ERROR: NotRegister")

    except Exception as e:
        temp = str(e).split(":")
        if temp[0] == "no such table" and temp[1]==" user":
            try:
                c.execute('''CREATE TABLE user(username TEXT NOT NULL, chat_id INT NOT NULL,user_group TEXT,permission_group TEXT)''')
                c.execute("INSERT INTO user(username,chat_id,user_group,permission_group) values(?,?,?,?)",(username,chat_id,"default","admin"))

                c.execute('CREATE TABLE permission_group(group_name TEXT NOT NULL, permission TEXT NOT NULL)')
                c.execute("INSERT INTO permission_group(group_name,permission) values('admin','all')")
                c.execute("INSERT INTO permission_group(group_name,permission) values('viewer','view')")

                c.execute('CREATE TABLE server(server_name TEXT NOT NULL, user_group TEXT ,nickname TEXT)')

            except Exception as e:
                update.message.reply_text("fail with error:"+str(e))
            else:
                update.message.reply_text("user, permission_group and server database setup finish.")
            finally:
                conn.commit()
                conn.close()
        else:
            update.message.reply_text("fail with error:"+str(e))
    else:
        if permission=="admin":
            update.message.reply_text("ERROR: DatabaseAlreadySetup")
        else:
            update.message.reply_text("ERROR: UnauthorizedException")
            

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(':L')

def get_chat_id(update:Update,context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    update.message.reply_text("hello "+username+". your chat_id is: "+str(chat_id))

def allow_user(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    conn = sqlite3.connect('./database/user.db')
    c = conn.cursor()
    users = c.execute("SELECT username,chat_id from user")
    for row in users:
        if username == row[0] and chat_id == row[1]:
            try:
                target_username = context.args[0]
                target_chat_id = context.args[1]
            except Exception as e:
                update.message.reply_text("ERROR: "+str(e))
            else:
                try:
                    c.execute("INSERT INTO user_allow (username,chat_id) values('"+target_username+"',"+str(target_chat_id)+")")
                except Exception as e:
                    update.message.reply_text("ERROR: "+str(e))
                else:
                    update.message.reply_text("allowed user "+target_username)
            finally:
                conn.commit()
                conn.close()
        else:
            update.message.reply_text("ERROR: UnauthorizedException")

def start_monitor(update:Update, context:CallbackContext):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        global minecraft_server_monitor
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
            minecraft_server_monitor = mp.Process(target=monitor_start, args=(server,))
            minecraft_server_monitor.start()
        except Exception as e:
            update.message.reply_text("ERROR: "+str(e))
        else:
            update.message.reply_text('start monitoring')
    else:
        update.message.reply_text("ERROR: UnauthorizedException")

def stop_monitor(update:Update, context:CallbackContext):
    chat_id = update.message.chat_id
    accept_permission = {"admin"}
    have_permission = verify(chat_id,accept_permission)
    if have_permission == True:
        minecraft_server_monitor.terminate()
        time.sleep(1)
        minecraft_server_monitor.terminate()
        minecraft_server_monitor.join()
        update.message.reply_text("stopped monitor")
    else:
        update.message.reply_text("ERROR: UnauthorizedException")

detail= range(1)
ALL,BACK = range(2)
def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    with open("config.json","r") as f:
        data = json.load(f) 
        print(type(data))
    token = data["telegram_token"]
    updater = Updater(token)

    updater.dispatcher.add_handler(CommandHandler('setup', setup))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(CommandHandler('get_chat_id', get_chat_id))
    updater.dispatcher.add_handler(CommandHandler('allow_user', allow_user))
    updater.dispatcher.add_handler(CommandHandler('start_monitor', start_monitor))
    updater.dispatcher.add_handler(CommandHandler('stop_monitor', stop_monitor))
    status_handler = ConversationHandler(
        entry_points=[CommandHandler('status', status)],
        states={
            detail: [
                CallbackQueryHandler(server_detail_all, pattern='^' + str(ALL) + '$'),
                CallbackQueryHandler(status, pattern='^' + str(BACK) + '$'),
                CallbackQueryHandler(server_detail),
            ],
        },
        fallbacks=[CommandHandler('status', status)],
    )

    add_server_handler = ConversationHandler(
        entry_points=[CommandHandler('add_server', add_server)],
        states={
            server_name: [MessageHandler(Filters.text, add_server_servername)],
            user_group: [
                CommandHandler('skip', add_server_skip_usergroup),
                MessageHandler(Filters.text, add_server_usergroup),
            ],
            nickname: [
                CommandHandler('skip', add_server_skip_nickname),
                MessageHandler(Filters.text, add_server_nickname),
            ],
        },
        fallbacks=[CommandHandler('cancel', add_server_cancel)],
    )

    updater.dispatcher.add_handler(add_server_handler)
    updater.dispatcher.add_handler(status_handler)
    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    try:
        os.mkdir("./database")
        os.mkdir("./logs")
        os.mkdir("./tmp")
    except FileExistsError:
        pass
    except Exception as e:
        print(e)
    main()
