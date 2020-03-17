# coding=utf-8

import configparser
import os
from telegram import (ForceReply, ReplyKeyboardMarkup, KeyboardButton,
                      ReplyKeyboardRemove)
from telegram.error import BadRequest, Unauthorized
from re import match
from random import randrange
from datetime import datetime
from calendarkeyboard import telegramcalendar
from database_functions import (choose_database, check_user,
                                search_entries_by_user, check_household,
                                get_playable_entries,
                                check_notify)
from parse_strings import (parse_db_entries_to_messagestring, single_db_entry_to_string)
from reply_handler import ForceReplyJobs
from calendar_export import delete_ics_file
from planning_functions import GameNight
from inline_handler import (generate_findbycategory, generate_pollbycategory, generate_settings)
from query_buffer import QueryBuffer
from error_handler import (handle_bot_not_admin, handle_bot_unauthorized)

"""
Commands registered with BotFather:
[DO NOT PRETTIFY THIS FORMAT, OTHERWISE IT CAN'T BE COPY-PASTED TO BOTFATHER!]
    key                         - Authentifiziere dich!
    neuer_termin                - Wir wollen spielen! (nur in Gruppen)
    ende_termin                 - Der Spieleabend ist vorbei, alle Planung verschwindet. (nur in Gruppen)
    ich                         - Nimm am nächsten Spieleabend teil!
    nichtich                    - Melde dich vom Spieleabend ab.
    wer                         - Finde heraus, wer alles am Spieleabend teilnimmt (nur im Privatchat)
    start_umfrage_spiel         - Wähle, welches Spiel du spielen möchtest! (nur in Gruppen)
    start_umfrage_erweiterung   - Stimmt ab, welche Erweiterung eines Spiels ihr spielen wollt. (nur in Gruppen)
    start_umfrage_genrespiel    - Stimmt ab, welches Spiel einer bestimmten Kategorie ihr spielen wollt. (nur in Gruppen)
    ende_umfrage                - Beende die Abstimmung. (nur in Gruppen)
    ergebnis                    - Lass dir die bisher abgegebenen Stimmen anzeigen.
    spiele                      - Ich sage dir, welche Spiele du bei mir angemeldet hast. (nur im Privatchat)
    erweiterungen               - Ich sage dir, welche Erweiterungen du bei mir angemeldet hast. (nur im Privatchat)
    neues_spiel                 - Trag dein neues Spiel ein! (nur im Privatchat)
    neue_erweiterung            - Trag deine neue Erweiterung ein. (nur im Privatchat)
    zufallsspiel                - Lass dir vom Bot ein Spiel vorschlagen. (nur im Privatchat)
    genrespiel                  - Lass dir vom Bot ein Spiel einer bestimmten Kategorie vorschlagen. (nur im Privatchat)
    leeren                      - Lösche alle laufenden Pläne und Abstimmungen (laufende Spiel-Eintragungen etc. sind davon nicht betroffen) (nur in Gruppen)
    einstellungen               - Verändere deine Einstellungen (Benachrichtigungen etc.)
    help                        - Was kann ich alles tun?
"""


def start(update, context):
    context.bot.send_message(update.message.chat_id,
                             'Hi! Bitte authentifiziere dich zuerst, '
                             'um mit mir zu reden:')
    key(update, context)


def key(update, context):
    if check_user(update.message.chat_id):
        update.message.reply_text('Du musst dich nicht authentifizieren. '
                                  'Ich weiß schon, wer du bist!')
    else:
        if not update.message.from_user.username:
            context.bot.send_message('So wird das mit uns nichts. '
                                     'Bitte lege zunächst deinen Alias unter '
                                     'Einstellungen > Username fest!\n'
                                     'Authentifiziere dich dann mit /key.')
        else:
            msg = context.bot.send_message(update.message.chat_id,
                                           'Wie lautet das Passwort?',
                                           reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "auth")


def csv_import(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /csv_import kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           'Gib die Daten ein, die du im CSV-Format '
                                           'in die Spiele-Datenbank importieren '
                                           'möchtest.\n'
                                           'Importiere zur Sicherheit max. 75 Einträge'
                                           ' über den Chat auf einmal!\n'
                                           'Format: Besitzer, Titel, Max. Spielerzahl, '
                                           'Kategorie_1, Kategorie_2, ... '
                                           'Pro Zeile ein Spiel',
                                           reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "csv")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def neuertermin(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            update.message.reply_text('Okay, wann wollt ihr spielen?',
                                      reply_markup=telegramcalendar.create_calendar())
        elif "private" in update.message.chat.type:
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


# The bot does not really respond to this message:
# the user can still see a reaction since the bot changes the title.
# However, it does send a message because a poll's keyboard cannot
# be reset, otherwise this message is deleted immediately
def endetermin(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            plan.clear()
            config = configparser.ConfigParser()
            config_path = os.path.dirname(os.path.realpath(__file__))
            config.read(os.path.join(config_path, "config.ini"))
            title = config['GroupDetails']['title']
            try:
                context.bot.set_chat_title(update.message.chat.id, title)
                context.bot.set_chat_description(update.message.chat_id, "")
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat.id)
            # since we can delete the Keyboard only via reply
            # this call is necessary
            msg = update.message.reply_text(
                        'Ich habe alles zurückgesetzt.',
                        reply_markup=ReplyKeyboardRemove())
            try:
                context.bot.delete_message(update.message.chat_id, msg.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
        elif "private" in update.message.chat.type:
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def ich(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.add_participant(update.message.from_user.username)
            send_message = check_notify("settings", update.message.from_user.username, "notify_participation")
            handled_unauthorized = False
            if send_message < 0:  # no entry in table, user hasn't talked to bot yet
                handled_unauthorized = True
                handle_bot_unauthorized(context.bot, update.message.chat_id, update.message.from_user.first_name)
            if check < 0:
                update.message.reply_text(
                    'Das war leider nichts. Vereinbart erst einmal einen '
                    'Termin mit /neuer_termin.')
            else:
                try:
                    context.bot.set_chat_description(update.message.chat_id,
                                                     plan.get_participants())
                except BadRequest:
                    handle_bot_not_admin(context.bot, update.message.chat.id)
                if send_message:
                    if check > 0:
                        text = ('Alles gut, ' + update.message.from_user.first_name + ', '
                                'ich weiß schon, dass du am ' + plan.date + ' teilnimmst.')
                    else:  # check = 0
                        text = ('Danke für deine Zusage zum Spieleabend ' + plan.date + ', '
                                + update.message.from_user.first_name + '!')
                    try:
                        context.bot.send_message(update.message.from_user.id,
                                                 text)

                        if check == 0 and match('\\d\\d[\\/]\\d\\d[\\/]\\d\\d\\d\\d', str(plan.date)) is not None:
                            context.bot.send_document(update.message.from_user.id,
                                                      document=open(plan.cal_file, 'rb'),
                                                      filename=("Spieleabend " + str(plan.date).replace('/', '-') + ".ics"))
                    except Unauthorized:
                        if not handled_unauthorized:  # don't send two warnings within the same command
                            handle_bot_unauthorized(context.bot, update.message.chat.id,
                                                    update.message.from_user.first_name, try_again="/ich")
                            handled_unauthorized = True
        elif "private" in update.message.chat.type:
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def nichtich(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.remove_participant(update.message.from_user.username)
            send_message = check_notify("settings", update.message.from_user.username, "notify_participation")
            handled_unauthorized = False
            if send_message < 0:  # no entry in table, user hasn't talked to bot yet
                handle_bot_unauthorized(context.bot, update.message.chat_id, update.message.from_user.first_name)
                handled_unauthorized = True
            if check < 0 and send_message:
                try:
                    context.bot.send_message(update.message.from_user.id, 'Danke für deine Absage. '
                                             'Schade, dass du nicht teilnehmen kannst.')
                except Unauthorized:
                    if not handled_unauthorized:
                        handle_bot_unauthorized(context.bot, update.message.chat_id,
                                                update.message.from_user.first_name,
                                                try_again="/nichtich")
                        handled_unauthorized = True
            elif check >= 0:
                try:
                    context.bot.set_chat_description(update.message.chat_id,
                                                     plan.get_participants())
                except BadRequest:
                    handle_bot_not_admin(context.bot, update.message.chat.id)
                if send_message:
                    try:
                        context.bot.send_message(update.message.from_user.id,
                                                 'Schade, dass du doch nicht '
                                                 'teilnehmen kannst, ' +
                                                 update.message.from_user.first_name + '.')
                    except Unauthorized:
                        if not handled_unauthorized:
                            handle_bot_unauthorized(context.bot, update.message.chat_id,
                                                    update.message.from_user.first_name,
                                                    try_again="/nichtich")
                            handled_unauthorized = True
        elif "private" in update.message.chat.type:
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def wer(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /wer kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            participants = GameNight().get_participants()
            update.message.reply_text(participants)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def start_umfrage_spiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.set_poll(update.message.from_user.username)
            if check < 0:
                update.message.reply_text('Das war leider nichts. '
                                          'Dies könnte verschiedene Gründe haben:\n'
                                          '(1) Ihr habt kein Datum festgelegt.  '
                                          'Holt das mit /neuer_termin nach.\n'
                                          '(2) Du bist nicht zum Spieleabend angemeldet. '
                                          'Hole das mit /ich nach.\n'
                                          '(3) Euch steht kein einziges Spiel zur Verfügung. '
                                          'Tragt neue Spiele mit /neues_spiel ein!')
            else:
                keys = []
                for o in plan.poll.options:
                    keys.append([KeyboardButton(o)])
                update.message.reply_text('Welches Spiel wollt ihr spielen?',
                                          reply_markup=ReplyKeyboardMarkup(
                                              keys, one_time_keyboard=True))
        elif "private" in update.message.chat.type:
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage '
                                      'im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def start_umfrage_erweiterung(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            msg = update.message.reply_text('Für welches Spiel soll über '
                                            'Erweiterungen abgestimmt werden?\n'
                                            'Antwortet mit /stop, um abzubrechen.',
                                            reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "expansion_poll_game")
        elif "private" in update.message.chat.type:
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage '
                                      'im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def start_umfrage_genrespiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            update.message.reply_text('Auf welche Kategorie habt ihr denn '
                                      'heute Lust?',
                                      reply_markup=generate_pollbycategory())
        elif "private" in update.message.chat.type:
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage '
                                      'im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def ende_umfrage(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            try:
                check = plan.end_poll(update.message.from_user.username)
            except AttributeError:
                update.message.reply_text(
                    'Das hat leider nicht funktioniert. Scheinbar gibt es '
                    'keine Umfrage, die ich beenden könnte.')
            else:
                if check < 0:
                    update.message.reply_text(
                        'Das hat leider nicht funktioniert. Du hast wohl '
                        'nicht das Recht zu dieser Aktion.')
                else:
                    update.message.reply_text(
                        'Die Umfrage ist beendet. Mit /ergebnis könnt ihr '
                        'sehen, wie sie ausgegangen ist.',
                        reply_markup=ReplyKeyboardRemove())
        elif "private" in update.message.chat.type:
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def ergebnis(update, context):
    if check_user(update.message.chat_id):
        plan = GameNight()
        try:
            votes = plan.poll.print_votes()
        except AttributeError:  # poll doesn't exist
            try:
                votes = plan.old_poll.print_votes()  # poll was ended
            except AttributeError:
                update.message.reply_text('Leider gibt es derzeit kein '
                                          'Ergebnis, was ich zeigen kann.')
            else:
                update.message.reply_text('Das Ergebnis ist: \n' + votes)
        else:
            update.message.reply_text('Das Ergebnis ist: \n' + votes)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def spiele(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /spiele kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            gamestring = parse_db_entries_to_messagestring(
                search_entries_by_user(choose_database("datadb"), 'games',
                                       update.message.from_user.username))
            if len(gamestring) == 0:
                context.bot.send_message(update.message.chat_id,
                                         text="Dass du Spiele hast, wäre mir neu. "
                                         "Wenn es doch der Fall ist, sag mir das mit /neues_spiel!")
            else:
                update.message.reply_text('Du hast folgende Spiele:')
                context.bot.send_message(update.message.chat_id, text=gamestring)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def erweiterungen(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /erweiterungen kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           'Für welches Grundspiel fragst du?\n'
                                           'Antworte mit /stop, um abzubrechen.',
                                           reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "expansions_list")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def neues_spiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /neues_spiel kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           'Wie heißt dein neues Spiel?\n'
                                           'Antworte mit /stop, um abzubrechen.',
                                           reply_markup=ForceReply())
            user_or_household_id = check_household(
                                    update.message.from_user.username)
            ForceReplyJobs().add_with_query(msg.message_id, "game_title",
                                            "new_game," +
                                            user_or_household_id + ",")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def neue_erweiterung(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /neue_erweiterung kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           'Für welches Spiel hast du eine neue '
                                           'Erweiterung?\n'
                                           'Antworte mit /stop, um abzubrechen.',
                                           reply_markup=ForceReply())
            user_or_household_id = check_household(
                                    update.message.from_user.username)
            ForceReplyJobs().add_with_query(msg.message_id, "expansion_for",
                                            "new_expansion," +
                                            user_or_household_id)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def zufallsspiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /zufallsspiel kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            opt = []
            entries = get_playable_entries(
                choose_database("datadb"), 'games', 'title',
                update.message.from_user.username)
            for e in entries:
                opt.append(single_db_entry_to_string(e))
            game = opt[randrange(len(opt))]
            update.message.reply_text('Wie wäre es mit ' + game + '?')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def genrespiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            try:
                context.bot.delete_message(update.message.chat_id,
                                           update.message.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
            try:
                context.bot.send_message(update.message.from_user.id,
                                         'Hey, /genrespiel kannst du im Gruppenchat '
                                         'nicht verwenden. Hier schon!')
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            update.message.reply_text(
                'Auf welche Kategorie hast du denn heute Lust?',
                reply_markup=generate_findbycategory())
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def leeren(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            plan.clear()
            config = configparser.ConfigParser()
            config_path = os.path.dirname(os.path.realpath(__file__))
            config.read(os.path.join(config_path, "config.ini"))
            title = config['GroupDetails']['title']
            try:  # raises error when no modification or bot not Admin
                context.bot.set_chat_title(update.message.chat.id, title)
                context.bot.set_chat_description(update.message.chat_id, "")
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat.id)
            update.message.reply_text('Ich habe alle Termine und '
                                      'Umfragen zurückgesetzt.',
                                      reply_markup=ReplyKeyboardRemove())
        elif "private" in update.message.chat.type:
            update.message.reply_text('Stopp, das hat hier nichts zu suchen!\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def einstellungen(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            init_settings = []
            msg = context.bot.send_message(update.message.chat_id,
                                           'Ändert hier die Gruppeneinstellungen. '
                                           'Bei welchen Problemen soll ich euch '
                                           'eine Warnung senden?',
                                           reply_markup=generate_settings(
                                                "settings_group",
                                                first=True,
                                                who=update.message.chat_id,
                                                init_array=init_settings))
            query = "settings_group," + str(update.message.chat_id) + ","
            # init_settings was initialised in generate_settings
            for init_val in init_settings:
                query = query + init_val + "/"
            QueryBuffer().add(msg.message_id, query)
        elif "private" in update.message.chat.type:
            init_settings = []
            msg = context.bot.send_message(update.message.chat_id,
                                           'Ändere hier deine Einstellungen. '
                                           'Bei welchen Ereignissen soll ich '
                                           'dich benachrichtigen?',
                                           reply_markup=generate_settings(
                                                "settings_private",
                                                first=True,
                                                who=update.message.from_user.username,
                                                init_array=init_settings))
            query = "settings_private," + update.message.from_user.username + ","
            # init_settings was initialised in generate_settings
            for init_val in init_settings:
                query = query + init_val + "/"
            QueryBuffer().add(msg.message_id, query)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def help(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            context.bot.send_message(update.message.chat_id,
                                     'Folgende Funktionen stehen dir im Gruppenchat '
                                     'zur Verfügung:\n\n'
                                     '/key - Authentifiziere dich!\n'
                                     '/neuer_termin - Wir wollen spielen! '
                                     '(nur in Gruppen)\n'
                                     '/ich - Nimm am nächsten Spieleabend teil! '
                                     '(nur in Gruppen)\n'
                                     '/nichtich - Melde dich vom Spieleabend ab '
                                     '(nur in Gruppen)\n'
                                     '/start_umfrage_spiel - Wähle, welches Spiel du '
                                     'spielen möchtest! (nur in Gruppen)\n'
                                     '/start_erweiterung - Stimmt ab, welche '
                                     'Erweiterung eines Spiels ihr spielen wollt. '
                                     '(nur in Gruppen)\n '
                                     '/start_umfrage_genrespiel - Stimmt ab, welches '
                                     'Spiel einer bestimmten Kategorie ihr '
                                     'spielen wollt.\n'
                                     '/ende_umfrage - Beende die Abstimmung. '
                                     '(nur in Gruppen)\n'
                                     '/ergebnis - Lass dir die bisher abgegebenen '
                                     'Stimmen anzeigen.\n'
                                     '/leeren - Lösche alle laufenden Pläne und '
                                     'Abstimmungen (laufende Spiel-Eintragungen '
                                     'etc. sind davon nicht betroffen)\n '
                                     '/einstellungen - Verändere die Gruppeneinstellungen '
                                     '(Benachrichtigungen etc.)\n'
                                     '/help - Was kann ich alles tun?\n\n'
                                     'Solltest du im Gruppenchat Funktionen nutzen, '
                                     'die dort nicht erlaubt sind,'
                                     ' wird deine Nachricht sofort gelöscht.\n'
                                     'Weitere Funktionen stehen dir im Privatchat '
                                     'zur Verfügung.')
        elif "private" in update.message.chat.type:
            context.bot.send_message(update.message.chat_id,
                                     'Folgende Funktionen stehen dir im Privatchat '
                                     'zur Verfügung:\n\n'
                                     '/key - Authentifiziere dich!\n'
                                     '/wer - Finde heraus, wer alles am Spieleabend '
                                     'teilnimmt\n'
                                     '/ergebnis - Lass dir die bisher abgegebenen '
                                     'Stimmen anzeigen.\n'
                                     '/spiele - Ich sage dir, welche Spiele du bei '
                                     'mir angemeldet hast.\n'
                                     '/erweiterungen - Ich sage dir, welche '
                                     'Erweiterungen du bei mir angemeldet hast.\n'
                                     '/neues_spiel - Trag dein neues Spiel ein!\n'
                                     '/neue_erweiterung - Trag deine neue '
                                     'Erweiterung ein.\n'
                                     '/zufallsspiel - Ich schlage dir ein Spiel vor.\n'
                                     '/genrespiel - Ich schlage dir ein Spiel einer '
                                     'bestimmten Kategorie vor.\n'
                                     '/einstellungen - Verändere deine Einstellungen '
                                     '(Benachrichtigungen etc.)\n'
                                     '/help - Was kann ich alles tun?\n\n'
                                     'Weitere Funktionen stehen dir im Gruppenchat '
                                     'zur Verfügung. '
                                     'Solltest du im Gruppenchat Funktionen nutzen, '
                                     'die dort nicht erlaubt sind, '
                                     'wird deine Nachricht sofort gelöscht.\n'
                                     )
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')
