# coding=utf-8

from telegram import (ForceReply, ReplyKeyboardMarkup, KeyboardButton)
from database_functions import *
import reply_handler
from planning_functions import (GameNight, Poll)

"""
Commands registered with BotFather:
    key                 - Authentifiziere dich!
    neuertermin         - Wir wollen spielen! (nur in Gruppen)
    ich                 - Nimm am nächsten Spieleabend teil!
    nichtich            - Melde dich vom Spieleabend ab.
    wer                 - Finde heraus, wer alles am Spieleabend teilnimmt
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
                     'Hi! Bitte authentifiziere dich zuerst, um mit mir zu reden.')
    key(bot, update)


def key(bot, update):
    if check_user(update.message.chat_id):
        update.message.reply_text('Du musst dich nicht authentifizieren. Ich weiß schon, wer du bist!')
    else:
        msg = bot.send_message(update.message.chat_id,
                               'Wie lautet das Passwort?',
                               reply_markup=ForceReply())
        reply_handler.reply_jobs.add(msg.message_id, "auth")


def csv_import(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Gib die Daten ein, die du im CSV-Format in die Spiele-Datenbank importieren '
                                   'möchtest.\n '
                                   'Importiere zur Sicherheit max. 75 Einträge über den Chat auf einmal!\n'
                                   'Format: Besitzer, Titel, Max. Spielerzahl'
                                   'Pro Zeile ein Spiel',
                                   reply_markup=ForceReply())
            reply_handler.reply_jobs.add(msg.message_id, "csv")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def neuertermin(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            msg = update.message.reply_text('Okay, wann wollt ihr spielen?',
                                            reply_markup=ForceReply())
            reply_handler.reply_jobs.add(msg.message_id, "date")
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def ich(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            plan = GameNight()
            check = plan.add_participant(update.message.from_user.username)
            if check < 0:
                update.message.reply_text(
                    'Das war leider nichts. Vereinbart erst einmal einen Termin mit /neuertermin.')
            else:
                update.message.reply_text('OK du hast zugesagt!')
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')

    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def wer(bot, update):
    if check_user(update.message.chat_id):
        participants = GameNight().get_participants()
        if participants == "":
            update.message.reply_text("Bisher nimmt niemand am Spieleabend teil.")
        else:
            update.message.reply_text(participants + 'nehmen teil.')

def nichtich(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            plan = GameNight()
            check = plan.remove_participant(update.message.from_user.username)
            if check < 0:
                update.message.reply_text('Das war leider nichts. Du warst nicht angemeldet.')
            else:
                update.message.reply_text('Schade, dass du doch nicht teilnehmen kannst.')
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def start_umfrage_spiel(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            plan = GameNight()
            check = plan.set_poll()
            if check < 0:
                update.message.reply_text(
                    'Das war leider nichts. Habt ihr kein Datum festgelegt? Holt das mit /neuertermin nach.')
            else:
                keys = []
                for o in plan.poll.options:
                    keys.append([KeyboardButton(o)])
                update.message.reply_text('Welches Spiel wollt ihr spielen?',
                                          reply_markup=ReplyKeyboardMarkup(keys, one_time_keyboard=True))
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def start_erweiterung(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            msg = update.message.reply_text('Für welches Spiel soll über Erweiterungen abgestimmt werden?',
                                            reply_markup=ForceReply())
            reply_handler.reply_jobs.add(msg.message_id, "expansion_poll_game")
        if update.message.chat.type == "private":
            update.message.reply_text('Wirklich?! Eine Umfrage nur für dich?\n'
                                      'Starte doch bitte eine Umfrage im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def ende_umfrage(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text(
                'Die Umfrage ist beendet. Mit /ergebnis könnt ihr sehen, wie sie ausgegangen ist.')
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def ergebnis(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Das Ergebnis ist...')
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen.\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


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
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def erweiterungen(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            update.message.reply_text('Du hast folgende Erweiterungen:')
            gamestring = to_messagestring(
                search_entries_by_user(choose_database("testdb"), 'expansions', update.message.from_user.username))
            bot.send_message(update.message.chat_id, text=gamestring)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def neues_spiel(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Wie heißt dein neues Spiel?\n'
                                   'Antworte mit /stop, um abzubrechen.',
                                   reply_markup=ForceReply())
            user_or_household_id = check_household(update.message.from_user.username)
            reply_handler.reply_jobs.add_with_query(msg.message_id, "game_title",
                                                    "new_game," + user_or_household_id + ",")
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def neue_erweiterung(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            pass
        if update.message.chat.type == "private":
            msg = bot.send_message(update.message.chat_id,
                                   'Für welches Spiel hast du eine neue Erweiterung gekauft?\n'
                                   'Antworte mit /stop, um abzubrechen!!',
                                   reply_markup=ForceReply())
            user_or_household_id = check_household(update.message.from_user.username)
            reply_handler.reply_jobs.add_with_query(msg.message_id, "expansion_for",
                                                    "new_expansion," + user_or_household_id)
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def leeren(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "group":
            update.message.reply_text('Ich habe alles zurückgesetzt.')
        if update.message.chat.type == "private":
            update.message.reply_text('Stopp, das hat hier nichts zu suchen!\n'
                                      'Bitte versuche es im Gruppenchat...')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')


def stop(bot, update):
    reply_handler.reply_jobs.clear_query()
    update.message.reply_text("Okay, hier ist nichts passiert.")


def help(bot, update):
    if check_user(update.message.chat_id):
        if update.message.chat.type == "private":
            bot.send_message(update.message.chat_id,
                            'Folgende Funktionen stehen dir im Privatchat zur Verfügung:\n'
                            '/key - Authentifiziere dich!\n'
                            '/wer - Finde heraus, wer alles am Spieleabend teilnimmt\n'
                            '/ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.\n'
                            '/spiele - Ich sage dir, welche Spiele du bei mir angemeldet hast.\n'
                            '/erweiterungen - Ich sage dir, welche Erweiterungen du bei mir angemeldet hast.\n'
                            '/neues_spiel - Trag dein neues Spiel ein!\n'
                            '/neue_erweiterung - Trag deine neue Erweiterung ein.\n'
                            '/help - Was kann ich alles tun?')
        if update.message.chat.type == "group":
            bot.send_message(update.message.chat_id,
                            'Folgende Funktionen stehen dir im Gruppenchat zur Verfügung:\n'
                            '/key - Authentifiziere dich!\n'
                            '/neuertermin - Wir wollen spielen! (nur in Gruppen)\n'
                            '/ich - Nimm am nächsten Spieleabend teil! (nur in Gruppen)\n'
                            '/nichtich - Melde dich vom Spieleabend ab (nur in Gruppen)\n'
                            '/wer - Finde heraus, wer alles am Spieleabend teilnimmt\n'
                            '/start_umfrage_spiel - Wähle, welches Spiel du spielen möchtest! (nur in Gruppen)\n'
                            '/start_erweiterung - Stimmt ab, welche Erweiterung eines Spiels ihr spielen wollt. (nur '
                            'in Gruppen)\n '
                            '/ende_umfrage - Beende die Abstimmung. (nur in Gruppen)\n'
                            '/ergebnis - Lass dir die bisher abgegebenen Stimmen anzeigen.\n'
                            '/leeren - Lösche alle laufenden Pläne und Abstimmungen (laufende Spiel-Eintragungen '
                            'etc. sind davon nicht betroffen)\n '
                            '/help - Was kann ich alles tun?')
    else:
        update.message.reply_text('Bitte authentifiziere dich zunächst mit /key.')
