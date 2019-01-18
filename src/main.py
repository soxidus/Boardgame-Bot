from src.database_functions import *
from src.commands import *
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler)


def main():

    # SETUP Database
    setup_database()

    # Create the EventHandler and pass it your bot's token.
#    bot = telegram.bot(token="702260882:AAF3VcoDbf3sSRVDht5xM3JYu-QNywEpgZg")
    updater = Updater("702260882:AAF3VcoDbf3sSRVDht5xM3JYu-QNywEpgZg")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("key", key))
    dp.add_handler(CommandHandler("neuertermin", neuertermin))
    dp.add_handler(CommandHandler("ich", ich))
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

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
