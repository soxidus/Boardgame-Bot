# coding=utf-8

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardRemove)
from calendarkeyboard import telegramcalendar
from planning_functions import GameNight
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
    category = update.callback_query.data.split(" ")[1]
    query = rep.ForceReplyJobs().get_query(update.callback_query.message.message_id) + "," + category + "," + ps.generate_uuid_32()

    if ps.parse_csv(query)[0] == "new_game":
        known_games = dbf.search_entries_by_user(
            dbf.choose_database("testdb"), 'games',
            update.callback_query.from_user.username)
        for _ in range(len(known_games)):
            # check whether this title has already been added for this user
            if known_games[_][0] == ps.parse_csv(query)[2]:
                update.callback_query.answer(
                    "Wusste ich doch: Das Spiel hast du schon "
                    "einmal eingetragen. Viel Spaß noch damit!")
                return
        dbf.add_game_into_db(ps.parse_values_from_array(
                                ps.remove_first_string(query)))
        update.callback_query.answer("Okay, das Spiel wurde hinzugefügt \\o/")
    else:
        pass
    rep.ForceReplyJobs().clear_query(
        update.callback_query.message.message_id)


def generate_categories():
    keyboard = []
    categories = ['groß', 'klein', 'Würfel', 'Rollenspiel', 'Karten', 'Worker Placement']
    for cat in categories:
        row = []
        data = "CATEGORY " + cat
        row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)
