# coding=utf-8

from telegram.error import BadRequest
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardRemove)
from calendarkeyboard import telegramcalendar
from planning_functions import GameNight
from query_buffer import QueryBuffer
import reply_handler as rep
import database_functions as dbf
import parse_strings as ps


def handle_inline(bot, update):
    if "CALENDAR" in update.callback_query.data:
        handle_calendar(bot, update)
    elif "CATEGORY" in update.callback_query.data:
        handle_category(bot, update)


def handle_calendar(bot, update):
    selected, date, user_inp_req = telegramcalendar.process_calendar_selection(bot, update)
    if selected:
        if user_inp_req:
            msg = bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text='Okay, wann wollt ihr spielen?',
                reply_markup=ForceReply())
            rep.ForceReplyJobs().add(msg.message_id, "date")
        elif date:
            check = GameNight(chat_id=update.callback_query.message.chat_id).set_date(date.strftime("%d/%m/%Y"))
            if check < 0:
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Melde dich doch einfach mit /ich "
                         "beim festgelegten Termin an.",
                    reply_markup=ReplyKeyboardRemove())
            else:
                bot.set_chat_title(
                    update.callback_query.message.chat_id,
                    'Spielwiese: ' + date.strftime("%d/%m/%Y"))
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, schrei einfach /ich, wenn du "
                         "teilnehmen willst!",
                    reply_markup=ReplyKeyboardRemove())


def handle_category(bot, update):
    update.callback_query.answer()
    category = update.callback_query.data.split(" ")[1]
    if category == "none":
        end_of_categories(bot, update, no_category=True)
    elif category == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Okay, hier ist nichts passiert.',
            reply_markup=ReplyKeyboardRemove())
    elif category == "done":
        end_of_categories(bot, update)
    elif category == "IGNORE":
        pass
    else:  # we actually got a category, now register it
        query = QueryBuffer().get_query(update.callback_query.message.message_id) + category + "/"
        categories_so_far = ps.parse_csv(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
        QueryBuffer().edit_query(update.callback_query.message.message_id, query)
        # change keyboard layout
        try:
            bot.edit_message_text(text=update.callback_query.message.text,
                                  chat_id=update.callback_query.message.chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  reply_markup=generate_categories(pressed=categories_so_far))
        except BadRequest:
            pass


def end_of_categories(bot, update, no_category=False):
    if no_category:
        query = QueryBuffer().get_query(update.callback_query.message.message_id) + " ," + ps.generate_uuid_32()
    else:  # user pressed "Done"
        query = QueryBuffer().get_query(update.callback_query.message.message_id) + "," + ps.generate_uuid_32()

    if ps.parse_csv(query)[0] == "new_game":
        known_games = dbf.search_entries_by_user(
            dbf.choose_database("testdb"), 'games',
            update.callback_query.from_user.username)
        for _ in range(len(known_games)):
            # check whether this title has already been added for this user
            if known_games[_][0] == ps.parse_csv(query)[2]:
                bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Wusste ich doch: Das Spiel hast du schon "
                         "einmal eingetragen. Viel Spaß noch damit!",
                    reply_markup=ReplyKeyboardRemove())
                return
        dbf.add_game_into_db(ps.parse_values_from_array(
                                ps.remove_first_string(query)))
        bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Okay, das Spiel wurde hinzugefügt \\o/",
                    reply_markup=ReplyKeyboardRemove())
    else:
        pass
    QueryBuffer().clear_query(
        update.callback_query.message.message_id)


def generate_categories(first=False, pressed=None):
    keyboard = []
    categories = ['groß', 'klein', 'Würfel', 'Rollenspiel', 'Karten', 'Worker Placement']
    for cat in categories:
        row = []
        data = "CATEGORY " + cat
        if pressed and (cat in pressed):
            label = cat + " ✓"
            row.append(InlineKeyboardButton(label, callback_data="CATEGORY IGNORE"))
        else:
            row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []
    if first:
        data = "CATEGORY none"
        row.append(InlineKeyboardButton('keine Angabe', callback_data=data))
    else:
        data = "CATEGORY done"
        row.append(InlineKeyboardButton('Fertig', callback_data=data))        
    data = "CATEGORY stop"
    row.append(InlineKeyboardButton('Abbrechen', callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)
