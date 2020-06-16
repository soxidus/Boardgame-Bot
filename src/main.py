# coding=utf-8

import configparser
import logging
import os
import sys

import schedule
from telegram.ext import (Updater, CommandHandler, Filters, MessageHandler,
                          CallbackQueryHandler)

import commands
from log_to_message import LogToMessageFilter
from filters import Vote
from planning_functions import (handle_vote, test_termin)
from reply_handler import handle_reply
from inline_handler import handle_inline


logger = None


def log(log_mode=None, log_file=None):
    global logger
    logger = logging.getLogger('telegram.ext.dispatcher')
    if log_mode:
        if log_mode == "file":
            if log_file:
                logging.basicConfig(level=logging.ERROR,
                                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    filename=log_file)
            else:
                logging.basicConfig(level=logging.ERROR,
                                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    filename='tg_bot_log.txt')
        elif log_mode == "private":
            log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            LogToMessageFilter().set_chat_type("private")
            LogToMessageFilter().set_formatter(log_formatter)
            logger.addFilter(LogToMessageFilter())
            logging.basicConfig(level=logging.ERROR,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        elif log_mode == "group":
            log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            LogToMessageFilter().set_chat_type("group")
            LogToMessageFilter().set_formatter(log_formatter)
            logger.addFilter(LogToMessageFilter())
            logging.basicConfig(level=logging.ERROR,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    # Create the EventHandler and pass it your bot's token.

    config = configparser.ConfigParser()
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))

    # Set up updater with your bot's token
    updater = Updater(config['Bot']['token'], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # init custom filter
    vote_filter = Vote()

    # This order is crucial! DO NOT CHANGE IT!
    dp.add_handler(MessageHandler(vote_filter, handle_vote))
    dp.add_handler(MessageHandler(Filters.reply, handle_reply))

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", commands.start))
    dp.add_handler(CommandHandler("key", commands.key))
    dp.add_handler(CommandHandler("neuer_termin", commands.neuertermin))
    dp.add_handler(CommandHandler("ende_termin", commands.endetermin))
    dp.add_handler(CommandHandler("csv_import", commands.csv_import))
    dp.add_handler(CommandHandler("ich", commands.ich))
    dp.add_handler(CommandHandler("nichtich", commands.nichtich))
    dp.add_handler(CommandHandler("wer", commands.wer))
    dp.add_handler(CommandHandler("start_umfrage_spiel", commands.start_umfrage_spiel))
    dp.add_handler(CommandHandler("start_umfrage_erweiterung", commands.start_umfrage_erweiterung))
    dp.add_handler(CommandHandler("start_umfrage_genrespiel", commands.start_umfrage_genrespiel))
    dp.add_handler(CommandHandler("zufallsspiel", commands.zufallsspiel))
    dp.add_handler(CommandHandler("genrespiel", commands.genrespiel))
    dp.add_handler(CommandHandler("ende_umfrage", commands.ende_umfrage))
    dp.add_handler(CommandHandler("ergebnis", commands.ergebnis))
    dp.add_handler(CommandHandler("spiele", commands.spiele))
    dp.add_handler(CommandHandler("erweiterungen", commands.erweiterungen))
    dp.add_handler(CommandHandler("neues_spiel", commands.neues_spiel))
    dp.add_handler(CommandHandler("neue_erweiterung", commands.neue_erweiterung))
    dp.add_handler(CommandHandler("leeren", commands.leeren))
    dp.add_handler(CommandHandler("einstellungen", commands.einstellungen))
    dp.add_handler(CommandHandler("help", commands.help))
    dp.add_handler(CallbackQueryHandler(handle_inline))
    # Start the Bot
    updater.start_polling()
    updater.idle()

    #schedule.every().day.at("12:00:00").do(test_termin, dp.bot)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "-d":
            if len(sys.argv) > 2:
                if sys.argv[2] == "file":
                    if len(sys.argv) > 4 and sys.argv[3] == "-f":
                        log(log_mode=sys.argv[2], log_file=sys.argv[4])
                elif sys.argv[2] in ["group", "private", "file"]:
                    log(log_mode=sys.argv[2])
                else:
                    print("Invalid debug mode specified. Your options are group, private or file.")
                    exit(0)
            else:
                log()
            try:
                main()
            except Exception:
                logger.exception("Fatal error running main()")
        elif sys.argv[1] in ("-h", "--help"):
            print(
                "usage: python3 main.py [options]\n\n"
                "options:\n"
                "  -d [mode]    activates debugging\n"
                "               If mode is specified as either group, private or file,\n"
                "               logs of level ERROR will be sent to a telegram group,\n"
                "               private chat or logged into a file named tg_bot_log.txt.\n"
                "               If mode is not specified, logs of level DEBUG will be\n"
                "               sent to the console.\n"
                "  -f <path>    write logs of level ERROR into specified file\n"
                "               caution: can only be used if debugging into file is activated\n"
                "               usage: python3 main.py -d file -f <path>\n"
                "  -h, --help   display this help message"
            )
    else:
        main()
