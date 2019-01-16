from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import telegram
"""
Commands:
    key                 - Authentifiziere dich!
    neuertermin         - Wir wollen spielen! (nur in Gruppen)
    ich                 - Nimm am nächsten Spieleabend teil!
    start_umfrage_spiel - Wähle, welches Spiel du spielen möchtest! (nur in Gruppen)
    start_erweiterung   - Stimmt ab, welche Erweiterung eines Spiels ihr spielen wollt. (nur in Gruppen)
    ende_umfrage        - Beende die Abstimmung. (nur in Gruppen)
    ergebnis            - Lass dir die bisher abgegebenen Stimmen anzeigen.
    spiele              - Ich sage dir, welche Spiele du bei mir angemeldet hast.
    erweiterungen       - Ich sage dir, welche Erweiterungen du bei mir angemeldet hast.
    neues_spiel         - Trag dein neues Spiel ein!
    neue_erweiterung    - Trag deine neue Erweiterung ein.
    leeren              - Lösche alle laufenden Pläne und Abstimmungen (laufende Spiel-Eintragungen etc. sind davon nicht betroffen)
    help                - Was kann ich alles tun?
"""


def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! Authentifizier dich bitte erst um mit mir zu reden')


def key(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Wie ist das Passwort?')


def neuertermin(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Erstellt einen neuen Temrin!')


def ich(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('OK du hast zugesagt!')


def start_umfrage_spiel(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Welches Spiel wollt ihr Spielen')


def start_erweiterung(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Welche Erweiterung?')


def ende_umfrage(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Umfrage Vorbei!!')


def ergebnis(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Das Ergebnis ist...')


def spiele(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Du hast folgende Spiele:')


def erweiterungen(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Du hast folgende Erweiterungen:')


def neues_spiel(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Wie heißt das Spiel?')


def neue_erweiterung(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Wie heißt die Erweiterung?')


def leeren(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Alles zurückgesetzt')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Folgende Funktionen stehen Zur Verfügung: ...')


def main():
    """Start the bot."""

    # ''' chris temp test bot '''
    # updater = Updater("745861447:AAFgmej56K8weT-dpaxe97A6Ak-pTOptk-s")

    # Create the EventHandler and pass it your bot's token.
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

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

