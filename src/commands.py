# coding=utf-8

from telegram import (ForceReply, ReplyKeyboardMarkup, KeyboardButton,
                      ReplyKeyboardRemove)
from telegram.error import BadRequest
from random import randrange
from calendarkeyboard import telegramcalendar
from database_functions import (choose_database, check_user,
                                search_entries_by_user, check_household,
                                get_playable_entries,
                                check_notify)
from parse_strings import (to_messagestring, single_db_entry_to_string)
from reply_handler import ForceReplyJobs
from planning_functions import GameNight
from inline_handler import (generate_findbycategory, generate_pollbycategory, generate_settings)
from query_buffer import QueryBuffer

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
    einstellungen               - Verändere deine Einstellungen (Benachrichtigungen etc.) (nur im Privatchat)
    help                        - Was kann ich alles tun?
"""


def start(bot, update):
    bot.send_message(update.message.chat_id,
                     'Hi! Bitte authentifiziere dich zuerst, '
                     'um mit mir zu reden.')
    key(bot, update)


def key(bot, update):
    if check_user(update.message.chat_id):
        update.message.reply_text('Du musst dich nicht authentifizieren. '
                                  'Ich weiß schon, wer du bist!')
    else:
        if not update.message.from_user.username:
            bot.send_message('So wird das mit uns nichts. '
                             'Bitte lege zunächst deinen Alias unter '
                             'Einstellungen > Username fest!\n'
                             'Authentifiziere dich dann mit /key.')
        else:
            msg = bot.send_message(update.message.chat_id,
                                   'Wie lautet das Passwort?',
                                   reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "auth")


def csv_import(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            # maybe add some waiting here at some point
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Gib die Daten ein, die du im CSV-Format '
                                   'in die Spiele-Datenbank importieren '
                                   'möchtest.\n'
                                   'Importiere zur Sicherheit max. 75 Einträge'
                                   ' über den Chat auf einmal!\n'
                                   'Format: Besitzer, Titel, Max. Spielerzahl'
                                   'Pro Zeile ein Spiel',
                                   reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "csv")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def neuertermin(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            msg = update.message.reply_text('Okay, wann wollt ihr spielen?',
                                            reply_markup=telegramcalendar.create_calendar())
            # ForceReplyJobs().add(msg.message_id, "date")
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


# The bot does not really respond to this message:
# the user can still see a reaction since the bot changes the title.
# However, it does send a message because a poll's keyboard cannot
# be reset, otherwise this message is deleted immediately


def endetermin(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            plan.clear()
            try:
                bot.set_chat_description(update.message.chat_id, "")
            except BadRequest:
                pass
            bot.set_chat_title(update.message.chat.id, 'Spielwiese')
            msg = update.message.reply_text(
                        'Ich habe alles zurückgesetzt.',
                        reply_markup=ReplyKeyboardRemove())
            bot.delete_message(update.message.chat_id, msg.message_id)
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def ich(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.add_participant(update.message.from_user.username)
            send_message = check_notify(update.message.from_user.username, "notify_participation")
            if check < 0:
                update.message.reply_text(
                    'Das war leider nichts. Vereinbart erst einmal einen '
                    'Termin mit /neuertermin.')
            else:
                if send_message:
                    bot.send_message(update.message.from_user.id,
                                    'Danke für deine Zusage zum Spieleabend ' +
                                    plan.date + ', ' +
                                    update.message.from_user.first_name + '!')
                bot.set_chat_description(update.message.chat_id,
                                         plan.get_participants())
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')

    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def nichtich(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.remove_participant(update.message.from_user.username)
            if check < 0:
                bot.send_message(update.message.from_user.id, 'Das war leider '
                                 'nichts. Du warst nicht angemeldet.')
            else:
                bot.send_message(update.message.from_user.id,
                                 'Schade, dass du doch nicht '
                                 'teilnehmen kannst, ' +
                                 update.message.from_user.first_name + '.')
                bot.set_chat_description(update.message.chat_id,
                                         plan.get_participants())
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def wer(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        else:
            participants = GameNight().get_participants()
            update.message.reply_text(participants)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def start_umfrage_spiel(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.set_poll(update.message.from_user.username)
            if check < 0:
                update.message.reply_text('Das war leider nichts. \n'
                                          'Habt ihr kein Datum festgelegt? '
                                          'Holt das mit /neuertermin nach.\n'
                                          'Vielleicht hast du dich auch '
                                          'einfach nicht angemeldet? Hole das '
                                          'mit /ich nach.')
            else:
                keys = []
                for o in plan.poll.options:
                    keys.append([KeyboardButton(o)])
                update.message.reply_text('Welches Spiel wollt ihr spielen?',
                                          reply_markup=ReplyKeyboardMarkup(
                                              keys, one_time_keyboard=True))
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage '
                                      'im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def start_erweiterung(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            msg = update.message.reply_text('Für welches Spiel soll über '
                                            'Erweiterungen abgestimmt werden?',
                                            reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "expansion_poll_game")
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage '
                                      'im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def start_umfrage_genrespiel(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            update.message.reply_text('Auf welche Kategorie habt ihr denn '
                                      'heute Lust?',
                                      reply_markup=generate_pollbycategory())
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage '
                                      'im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def ende_umfrage(bot, update):
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
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def ergebnis(bot, update):
    if check_user(update.message.chat_id):
        plan = GameNight()
        try:
            votes = plan.poll.print_votes()
        except AttributeError:  # poll doesn't exist
            try:
                votes = plan.old_poll.print_votes()  # poll was ended
            except AttributeError:
                update.message.reply_text('Leider gibt es derzeit kein '
                                          'Ergebnis, was ich dir zeigen kann.')
            else:
                update.message.reply_text('Das Ergebnis ist: \n' + votes)
        else:
            update.message.reply_text('Das Ergebnis ist: \n' + votes)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def spiele(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            gamestring = to_messagestring(
                search_entries_by_user(choose_database("testdb"), 'games',
                                       update.message.from_user.username))
            if len(gamestring) == 0:
                bot.send_message(update.message.chat_id,
                                 text="Dass du Spiele hast, wäre mir neu. "
                                 "Wenn das der Fall ist, sag mir das mit /neuesspiel!")
            else:
                update.message.reply_text('Du hast folgende Spiele:')
                bot.send_message(update.message.chat_id, text=gamestring)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def erweiterungen(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Um welches Grundspiel geht es dir gerade?\n'
                                   'Antwort mit /stop, um abzubrechen.',
                                   reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "expansions_list")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def neues_spiel(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
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


def neue_erweiterung(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Für welches Spiel hast du eine neue '
                                   'Erweiterung gekauft?\n'
                                   'Antworte mit /stop, um abzubrechen!!',
                                   reply_markup=ForceReply())
            user_or_household_id = check_household(
                                    update.message.from_user.username)
            ForceReplyJobs().add_with_query(msg.message_id, "expansion_for",
                                            "new_expansion," +
                                            user_or_household_id)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def zufallsspiel(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            opt = []
            entries = get_playable_entries(
                choose_database("testdb"), 'games', 'title',
                update.message.from_user.username)
            for e in entries:
                opt.append(single_db_entry_to_string(e))
            game = opt[randrange(len(opt))]
            update.message.reply_text('Wie wäre es mit ' + game + '?')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def genrespiel(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            update.message.reply_text(
                'Auf welche Kategorie hast du denn heute Lust?',
                reply_markup=generate_findbycategory())
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def leeren(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            plan.clear()
            try:  # raises error when no modification
                bot.set_chat_description(update.message.chat_id, "")
            except BadRequest:
                pass
            bot.set_chat_title(update.message.chat.id, 'Spielwiese')
            update.message.reply_text('Ich habe alle Termine und '
                                      'Umfragen zurückgesetzt.',
                                      reply_markup=ReplyKeyboardRemove())
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen!\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')


def einstellungen(bot, update):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            bot.delete_message(update.message.chat_id,
                               update.message.message_id)
            pass
        if update.message.chat.type == "private":
            init_settings = []
            msg = bot.send_message(update.message.chat_id,
                                   'Ändere hier deine Einstellungen.\n'
                                   'Antworte mit /stop, um abzubrechen.',
                                   reply_markup=generate_settings(
                                       first=True,
                                       user=update.message.from_user.username,
                                       init_array=init_settings))
            query = "settings," + update.message.from_user.username + ","
            for init_val in init_settings:
                query = query + init_val + "/"
            QueryBuffer().add(msg.message_id, query)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')                                      


def help(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "private":
            bot.send_message(update.message.chat_id,
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
                             '(Benachrichtigungen etc.)'
                             '/help - Was kann ich alles tun?\n\n'
                             'Weitere Funktionen stehen dir im Gruppenchat '
                             'zur Verfügung.'
                             'Solltest du im Gruppenchat Funktionen nutzen, '
                             'die dort nicht erlaubt sind, '
                             'wird deine Nachricht sofort gelöscht.\n'
                             )
        if "group" in update.message.chat.type:
            bot.send_message(update.message.chat_id,
                             'Folgende Funktionen stehen dir im Gruppenchat '
                             'zur Verfügung:\n\n'
                             '/key - Authentifiziere dich!\n'
                             '/neuertermin - Wir wollen spielen! '
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
                             '/help - Was kann ich alles tun?\n\n'
                             'Solltest du im Gruppenchat Funktionen nutzen, '
                             'die dort nicht erlaubt sind,'
                             ' wird deine Nachricht sofort gelöscht.\n'
                             'Weitere Funktionen stehen dir im Privatchat '
                             'zur Verfügung.')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst '
                                  'mit /key.')
