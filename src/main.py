# coding=utf-8

import configparser
import logging
import os
import sys

import schedule
from telegram.ext import (Updater, CommandHandler, Filters, MessageHandler,
                          CallbackQueryHandler)

import commands
import log_to_message
from filters import Vote
from planning_functions import (handle_vote, test_termin)
from reply_handler import handle_reply
from inline_handler import handle_inline


def main(log=False, log_mode=None, log_file=None):

    if log:
        if log_mode:
            if log_mode == "file":
                if log_file:
                    logging.basicConfig(level=logging.DEBUG,
                                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                        filename=log_file)
                else:
                    logging.basicConfig(level=logging.DEBUG,
                                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                        filename='tg_bot_log.txt')
            elif log_mode == "private":
                log_to_message.debug_chat = "private"
                logging.basicConfig(level=logging.DEBUG,
                                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                    stream=log_to_message.log_capture_string)
                # TODO: something something logging
            elif log_mode == "group":
                log_to_message.debug_chat = "group"
                # TODO: something something logging
            else:
                logging.basicConfig(level=logging.DEBUG,
                                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

    schedule.every().day.at("12:00:00").do(test_termin, dp.bot)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "-d":
            if len(sys.argv) > 2:
                if sys.argv[2] == "file":
                    if len(sys.argv) > 4 and sys.argv[3] == "-f":
                        main(log=True, log_mode=sys.argv[2], log_file=sys.argv[4])
                elif sys.argv[2] in ["group", "private", "file"]:
                    main(log=True, log_mode=sys.argv[2])
                else:
                    print("Invalid debug mode specified. Your options are group, private or file.")
                    exit(0)
            else:
                main(log=True)
    else:
        main()
