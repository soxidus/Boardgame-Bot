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
from parse_strings import (parse_db_entries_to_messagestring, parse_single_db_entry_to_string, read_json)
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
                             read_json(["commands", "start"]))
    key(update, context)


def key(update, context):
    if check_user(update.message.chat_id):
        update.message.reply_text(read_json(["commands", "key", "no_auth_needed"]))
    else:
        if not update.message.from_user.username:
            context.bot.send_message(read_json(["commands", "key", "no_alias"]))
        else:
            msg = context.bot.send_message(update.message.chat_id,
                                           read_json(["commands", "key", "password"]),
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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/csv_import"))
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           read_json(["commands", "csv_import"]),
                                           reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "csv")
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def neuertermin(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "neuertermin"]),
                                      reply_markup=telegramcalendar.create_calendar())
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                        read_json(["commands", "endetermin"]),
                        reply_markup=ReplyKeyboardRemove())
            try:
                context.bot.delete_message(update.message.chat_id, msg.message_id)
            except BadRequest:
                handle_bot_not_admin(context.bot, update.message.chat_id)
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                update.message.reply_text(read_json(["commands", "ich", "error_no_date"]))
            else:
                try:
                    context.bot.set_chat_description(update.message.chat_id,
                                                     plan.get_participants())
                except BadRequest:
                    handle_bot_not_admin(context.bot, update.message.chat.id)
                if send_message:
                    if check > 0:
                        text = read_json(["commands", "ich", "previously_registered"]).format(name=update.message.from_user.first_name,
                                                                                              date=plan.date)
                    else:  # check = 0
                        text = read_json(["commands", "ich", "newly_registered"]).format(name=update.message.from_user.first_name, date=plan.date)
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
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                    context.bot.send_message(update.message.from_user.id, read_json(["commands", "nichtich", "declined"]))
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
                                                 read_json(["commands", "nichtich", "unregistered"]).format(name=update.message.from_user.first_name))
                    except Unauthorized:
                        if not handled_unauthorized:
                            handle_bot_unauthorized(context.bot, update.message.chat_id,
                                                    update.message.from_user.first_name,
                                                    try_again="/nichtich")
                            handled_unauthorized = True
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/wer"))
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            participants = GameNight().get_participants()
            update.message.reply_text(participants)
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def start_umfrage_spiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            check = plan.set_poll(update.message.from_user.username)
            if check < 0:
                update.message.reply_text(read_json(["commands", "start_umfrage_spiel", "error_poll_game"]))
            else:
                keys = []
                for o in plan.poll.options:
                    keys.append([KeyboardButton(o)])
                update.message.reply_text(read_json(["commands", "start_umfrage_spiel", "what_game"]),
                                          reply_markup=ReplyKeyboardMarkup(
                                            keys, one_time_keyboard=True))
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def start_umfrage_erweiterung(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            msg = update.message.reply_text(read_json(["commands", "start_umfrage_erweiterung"]),
                                            reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "expansion_poll_game")
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def start_umfrage_genrespiel(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "start_umfrage_genrespiel"]),
                                      reply_markup=generate_pollbycategory())
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def ende_umfrage(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            plan = GameNight()
            try:
                check = plan.end_poll(update.message.from_user.username)
            except AttributeError:
                update.message.reply_text(read_json(["commands", "ende_umfrage", "no_poll"]))
            else:
                if check < 0:
                    update.message.reply_text(read_json(["commands", "ende_umfrage", "not_authorised"]))
                else:
                    update.message.reply_text(read_json(["commands", "ende_umfrage", "ended_poll"]),
                                              reply_markup=ReplyKeyboardRemove())
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def ergebnis(update, context):
    if check_user(update.message.chat_id):
        plan = GameNight()
        try:
            votes = plan.poll.print_votes()
        except AttributeError:  # poll doesn't exist
            try:
                votes = plan.old_poll.print_votes()  # poll was ended
            except AttributeError:
                update.message.reply_text(read_json(["commands", "ergebnis", "no_results"]))
            else:
                update.message.reply_text(read_json(["commands", "ergebnis", "results"]) + votes)
        else:
            update.message.reply_text(read_json(["commands", "ergebnis", "results"]) + votes)
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/spiele"))
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
                                         text=read_json(["commands", "spiele", "no_games"]))
            else:
                update.message.reply_text(read_json(["commands", "spiele", "games_list"]))
                context.bot.send_message(update.message.chat_id, text=gamestring)
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/erweiterungen"))
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           read_json(["commands", "erweiterungen"]),
                                           reply_markup=ForceReply())
            ForceReplyJobs().add(msg.message_id, "expansions_list")
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/neues_spiel"))
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           read_json(["commands", "neues_spiel"]),
                                           reply_markup=ForceReply())
            user_or_household_id = check_household(
                                    update.message.from_user.username)
            ForceReplyJobs().add_with_query(msg.message_id, "game_title",
                                            "new_game," +
                                            user_or_household_id + ",")
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/neue_erweiterung"))
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            msg = context.bot.send_message(update.message.chat_id,
                                           read_json(["commands", "neue_erweiterung"]),
                                           reply_markup=ForceReply())
            user_or_household_id = check_household(
                                    update.message.from_user.username)
            ForceReplyJobs().add_with_query(msg.message_id, "expansion_for",
                                            "new_expansion," +
                                            user_or_household_id)
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/zufallsspiel"))
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
                opt.append(parse_single_db_entry_to_string(e))
            game = opt[randrange(len(opt))]
            update.message.reply_text(read_json(["commands", "zufallsspiel"]).format(title=game))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
                                         read_json(["commands", "general", "not_in_group"]).format(command="/genrespiel"))
            except Unauthorized:
                handle_bot_unauthorized(context.bot, update.message.chat_id,
                                        update.message.from_user.username,
                                        try_again='das Ganze im Privatchat')
        elif "private" in update.message.chat.type:
            update.message.reply_text(
                read_json(["commands", "genrespiel"]),
                reply_markup=generate_findbycategory())
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


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
            update.message.reply_text(read_json(["commands", "leeren"]),
                                      reply_markup=ReplyKeyboardRemove())
        elif "private" in update.message.chat.type:
            update.message.reply_text(read_json(["commands", "general", "not_in_private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def einstellungen(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            init_settings = []
            msg = context.bot.send_message(update.message.chat_id,
                                           read_json(["commands", "einstellungen", "group"]),
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
                                           read_json(["commands", "einstellungen", "private"]),
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
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))


def help(update, context):
    if check_user(update.message.chat_id):
        if "group" in update.message.chat.type:
            context.bot.send_message(update.message.chat_id,
                                     read_json(["commands", "help", "group"]))
        elif "private" in update.message.chat.type:
            context.bot.send_message(update.message.chat_id,
                                     read_json(["commands", "help", "private"]))
    else:
        update.message.reply_text(read_json(["commands", "general", "please_auth"]))
