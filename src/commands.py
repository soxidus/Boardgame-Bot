# coding=utf-8

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
from telegram import *
from database_functions import *
from parse_strings import *
import reply_handler

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
                     'Hi! Authentifiziere dich bitte erst, um mit mir zu reden')
    key(bot, update)


def key(bot, update):
    msg = bot.send_message(update.message.chat_id,
                           'Wie lautet das Passwort?',
                           reply_markup=ForceReply())

    reply_handler.reply_jobs.add(msg.message_id, "auth")


def csv_import(bot, update):
    msg = bot.send_message(update.message.chat_id,
                           'Gib die Daten ein, die du importieren möchtest im csv Format\n'
                           'Zur Sicherheit über den chat nur max. 50 auf einmal bitte!\n'
                           'Im Format: Besitzer,Titel,Max. Spielerzahl',
                           reply_markup=ForceReply())

    reply_handler.reply_jobs.add(msg.message_id, "csv")


def neuertermin(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Erstellt einen neuen Temrin!')
        if update.message.chat.type == "private":
            update.message.reply_text('NEIN! das hat hier nichts zu suchen!\n'
                                      'versuch s nochmal im Gruppenchat...')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def ich(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('OK du hast zugesagt!')
        if update.message.chat.type == "private":
            update.message.reply_text('NEIN! das hat hier nichts zu suchen!\n'
                                      'versuch s nochmal im Gruppenchat...')

    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def start_umfrage_spiel(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Welches Spiel wollt ihr Spielen')
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'starte doch bitte eine Umfrage im Gruppenchat...')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def start_erweiterung(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Welche Erweiterung?')
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'starte doch bitte eine Umfrage im Gruppenchat...')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def ende_umfrage(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Umfrage Vorbei!!')
        if update.message.chat.type == "private":
            update.message.reply_text('NEIN! das hat hier nichts zu suchen!\n'
                                      'versuch s nochmal im Gruppenchat...')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def ergebnis(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Das Ergebnis ist...')
        if update.message.chat.type == "private":
            update.message.reply_text('NEIN! das hat hier nichts zu suchen!\n'
                                      'versuch s nochmal im Gruppenchat...')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def spiele(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            update.message.reply_text('Du hast folgende Spiele:')
            gamestring = to_messagestring(
                search_entries_by_user(choose_database("testdb"), 'games', update.message.from_user.username))
            bot.send_message(update.message.chat_id, text=gamestring)
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def erweiterungen(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            update.message.reply_text('Du hast folgende Erweiterungen:')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def neues_spiel(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Wie heißt das Spiel?\n'
                                   '/stop ist immer eine Option um abzubrechen!!',
                                   reply_markup=ForceReply())

            user_or_household_id = check_household(update.message.from_user.username)
            reply_handler.reply_jobs.add_with_query(msg.message_id, "game_title",
                                                    "new_game," + user_or_household_id + ",")

    #          val = ("titlegoeshere", user_or_household_id, "playercountgoeshere")
    #        add_game_into_db(val)
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def neue_erweiterung(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Wie heißt die Erweiterung?\n'
                                   '/stop ist immer eine Option um abzubrechen!!',
                                   reply_markup=ForceReply())
            user_or_household_id = check_household(update.message.from_user.username)
            reply_handler.reply_jobs.add_with_query(msg.message_id, "game_title",
                                                    "new_expansion," + user_or_household_id)
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def leeren(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Alles zurückgesetzt')
        if update.message.chat.type == "private":
            update.message.reply_text('NEIN! das hat hier nichts zu suchen!\n'
                                      'versuch s nochmal im Gruppenchat...')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')


def stop(bot, update):
    reply_handler.reply_jobs.clear_query()
    update.message.reply_text("OKAY Hier ist nichts passiert!!")


def help(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "private":
            bot.send_message(update.message.chat_id,
                             'Folgende Funktionen stehen Zur Verfügung:\n'
                             '/key - Authentifiziere dich!\n'
                             '/ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.\n'
                             '/spiele - Ich sage dir, welche Spiele du bei mir angemeldet hast.\n'
                             '/erweiterungen - Ich sage dir, welche Erweiterungen du bei mir angemeldet hast.\n'
                             '/neues_spiel - Trag dein neues Spiel ein!\n'
                             '/neue_erweiterung - Trag deine neue Erweiterung ein.\n'
                             '/help - Was kann ich alles tun?')
        if update.message.chat.type == "group":
            bot.send_message(update.message.chat_id,
                             'Folgende Funktionen stehen Zur Verfügung:\n'
                             '/key - Authentifiziere dich!\n'
                             '/neuertermin - Wir wollen spielen! (nur in Gruppen)\n'
                             '/ich - Nimm am nächsten Spieleabend teil! (nur in Gruppen)\n'
                             '/start_umfrage_spiel - Wähle, welches Spiel du spielen möchtest! (nur in Gruppen)\n'
                             '/start_erweiterung - Stimmt ab, welche Erweiterung eines Spiels ihr spielen wollt. (nur '
                             'in Gruppen)\n '
                             '/ende_umfrage - Beende die Abstimmung. (nur in Gruppen)\n'
                             '/ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.\n'
                             '/leeren - Lösche alle laufenden Pläne und Abstimmungen (laufende Spiel-Eintragungen '
                             'etc. sind davon nicht betroffen)\n '
                             '/help - Was kann ich alles tun?')
    else:
        update.message.reply_text('Bitte Authentifiziere dich zuerst!!')
