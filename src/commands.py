from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
from telegram import *
from src.database_functions import *

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
    bot.send_message(update.message.chat_id,
                     'Hi! Authentifizier dich bitte erst um mit mir zu reden')
    key(bot, update)


def key(bot, update):
    passphrase = "Minze"

    msg = bot.send_message(update.message.chat_id,
                           'Wie ist das Passwort?',
                           reply_markup=ForceReply())

    print(update.message)

#    if :


def neuertermin(bot, update):
    update.message.reply_text('Erstellt einen neuen Temrin!')


def ich(bot, update):
    update.message.reply_text('OK du hast zugesagt!')


def start_umfrage_spiel(bot, update):
    update.message.reply_text('Welches Spiel wollt ihr Spielen')


def start_erweiterung(bot, update):
    update.message.reply_text('Welche Erweiterung?')


def ende_umfrage(bot, update):
    update.message.reply_text('Umfrage Vorbei!!')


def ergebnis(bot, update):
    update.message.reply_text('Das Ergebnis ist...')


def spiele(bot, update):
    update.message.reply_text('Du hast folgende Spiele:')


def erweiterungen(bot, update):
    update.message.reply_text('Du hast folgende Erweiterungen:')


def neues_spiel(bot, update):
    update.message.reply_text('Wie heißt das Spiel?')


def neue_erweiterung(bot, update):
    update.message.reply_text('Wie heißt die Erweiterung?')


def leeren(bot, update):
    update.message.reply_text('Alles zurückgesetzt')


def help(bot, update):
    update.message.reply_text('Folgende Funktionen stehen Zur Verfügung: ...')
