# coding=utf-8

import logging
from telegram.ext import (Updater, CommandHandler, Filters, MessageHandler)
from reply_handler import handle_reply
from commands import *
from filters import Vote
from planning_functions import handle_vote


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create the EventHandler and pass it your bot's token.

    # Kara Webhook
    updater = Updater("702260882:AAF3VcoDbf3sSRVDht5xM3JYu-QNywEpgZg")
    # Chris Webhook
    # updater = Updater("745861447:AAFgmej56K8weT-dpaxe97A6Ak-pTOptk-s")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # init some custom stuff
    vote_filter = Vote()

    # This order is crucial! DO NOT CHANGE IT!
    dp.add_handler(MessageHandler(vote_filter, handle_vote))
    dp.add_handler(MessageHandler(Filters.reply, handle_reply))

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("key", key))
    dp.add_handler(CommandHandler("neuertermin", neuertermin))
    dp.add_handler(CommandHandler("csv_import", csv_import))
    dp.add_handler(CommandHandler("ich", ich))
    dp.add_handler(CommandHandler("nichtich", nichtich))
    dp.add_handler(CommandHandler("wer", wer))
    dp.add_handler(CommandHandler("start_umfrage_spiel", start_umfrage_spiel))
    dp.add_handler(CommandHandler("start_erweiterung", start_erweiterung))
    dp.add_handler(CommandHandler("ende_umfrage", ende_umfrage))
    dp.add_handler(CommandHandler("ergebnis", ergebnis))
    dp.add_handler(CommandHandler("spiele", spiele))
    dp.add_handler(CommandHandler("erweiterungen", erweiterungen))
    dp.add_handler(CommandHandler("neues_spiel", neues_spiel))
    dp.add_handler(CommandHandler("neue_erweiterung", neue_erweiterung))
    dp.add_handler(CommandHandler("leeren", leeren))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("stop", stop))
    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
