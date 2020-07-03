# coding=utf-8

import configparser
import os
from random import randrange
from mysql.connector.errors import IntegrityError
from telegram.error import BadRequest
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardRemove, ForceReply,
                      KeyboardButton, ReplyKeyboardMarkup)
from calendarkeyboard import telegramcalendar
from planning_functions import GameNight
from query_buffer import QueryBuffer
from parse_strings import parse_single_db_entry_to_string
from error_handler import handle_bot_not_admin
from calendar_export import create_ics_file
from log_to_message import LogToMessageFilter
import reply_handler as rep
import database_functions as dbf
import parse_strings as ps


def handle_inline(update, context):
    if "CALENDAR" in update.callback_query.data:
        handle_calendar(update, context)
    elif "CATEGORY" in update.callback_query.data:
        handle_category(update, context)
    elif "FINDBY" in update.callback_query.data:
        handle_findbycategory(update, context)
    elif "POLLBY" in update.callback_query.data:
        handle_pollbycategory(update, context)
    elif "SETTING" in update.callback_query.data:
        handle_settings(update, context)
    elif "HOUSEHOLD" in update.callback_query.data:
        handle_household(update, context)
    elif "DEBUG" in update.callback_query.data:
        handle_debug(update, context)
    elif "CSV_IMPORT" in update.callback_query.data:
        handle_csv_import(update, context)
    elif "ENDED" in update.callback_query.data:
        # don't do a thing
        update.callback_query.answer()


# used by inlines CATEGORY, FINDBY, POLLBY and SETTING
# CALENDAR does this in telegramcalendar submodule instead
def shrink_keyboard(update, context, label):
    query = update.callback_query
    keyboard = []
    row = []
    row.append(InlineKeyboardButton(label, callback_data="ENDED"))
    keyboard.append(row)
    context.bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                          message_id=query.message.message_id,
                                          reply_markup=InlineKeyboardMarkup(keyboard))


def handle_calendar(update, context):
    selected, date, user_inp_req, stop = telegramcalendar.process_calendar_selection(update, context)
    if stop:
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=ps.read_json(["inline_handler", "stop_interaction"])
        )
    elif selected:
        if user_inp_req:
            msg = context.bot.send_message(
                chat_id=update.callback_query.message.chat_id,
                text=ps.read_json(["inline_handler", "handle_calendar", "ask_date"]),
                reply_markup=ForceReply())
            rep.ForceReplyJobs().add(msg.message_id, "date")
        elif date:
            check = GameNight(chat_id=update.callback_query.message.chat_id).set_date(date.strftime("%d/%m/%Y"))
            if check < 0:
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "handle_calendar", "have_date_already"]),
                    reply_markup=ReplyKeyboardRemove())
            else:
                config = configparser.ConfigParser()
                config_path = os.path.dirname(os.path.realpath(__file__))
                config.read(os.path.join(config_path, "config.ini"))
                title = config['GroupDetails']['title']
                try:
                    context.bot.set_chat_title(
                        update.callback_query.message.chat_id,
                        title + ': ' + date.strftime("%d/%m/%Y"))
                except BadRequest:
                    handle_bot_not_admin(context.bot, update.callback_query.message.chat.id)
                filename = create_ics_file("Spieleabend", date)
                GameNight(chat_id=update.callback_query.message.chat_id).set_cal_file(filename)
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "handle_calendar", "date_set"]),
                    reply_markup=ReplyKeyboardRemove())


def handle_category(update, context):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "none":
        end_of_categories(update, context, no_category=True)
    elif category == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=ps.read_json(["inline_handler", "stop_interaction"]),
            reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "stop_shrink"]))
    elif category == "done":
        end_of_categories(update, context)
    elif category == "IGNORE":
        pass
    else:  # we actually got a category, now register it
        if update.callback_query.data.split(";")[2] == "SET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id) + category + "/"
            categories_so_far = ps.parse_csv_to_array(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
            QueryBuffer().edit_query(update.callback_query.message.message_id, query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                              chat_id=update.callback_query.message.chat_id,
                                              message_id=update.callback_query.message.message_id,
                                              reply_markup=generate_categories(pressed=categories_so_far))
            except BadRequest:
                pass
        elif update.callback_query.data.split(";")[2] == "UNSET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id)
            query_csv = ps.parse_csv_to_array(query)
            categories_so_far = query_csv[-1].split('/')[:-1]
            categories_so_far.remove(category)
            categories_string = '/'.join(categories_so_far)
            if len(categories_string) > 0:
                categories_string += '/'
            new_query = ps.parse_array_to_csv(query_csv[:-1]) + ',' + categories_string
            QueryBuffer().edit_query(update.callback_query.message.message_id, new_query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                              chat_id=update.callback_query.message.chat_id,
                                              message_id=update.callback_query.message.message_id,
                                              reply_markup=generate_categories(pressed=categories_so_far))
            except BadRequest:
                pass


def end_of_categories(update, context, no_category=False):
    query = QueryBuffer().get_query(update.callback_query.message.message_id)
    query_csv = ps.parse_csv_to_array(query)
    categories = query_csv[-1].split('/')[:-1]
    # remove categories from query buffer now
    uuid = ps.generate_uuid_32()
    query = ps.parse_array_to_csv(query_csv[:-1]) + "," + uuid

    if query_csv[0] == "new_game":
        if no_category:
            try:
                dbf.add_game_into_db(ps.parse_csv_to_array(
                                        ps.remove_first_string(query)))
                # dbf.add_game_into_db(ps.parse_values_from_query(
                #                         ps.remove_first_string(query)))
            except IntegrityError:
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "category", "known_game"]),
                    reply_markup=ReplyKeyboardRemove())
                inline_text = ps.read_json(["inline_handler", "category", "shrink_known_game"]).format(title=query_csv[2])
                shrink_keyboard(update, context, inline_text)
                return
        else:
            try:
                dbf.add_game_into_db(ps.parse_csv_to_array(
                                        ps.remove_first_string(query)),
                                     cats=categories,
                                     uuid=uuid)
                # dbf.add_game_into_db(ps.parse_values_from_query(
                #                     ps.remove_first_string(query)),
                #                     cats=categories,
                #                     uuid=uuid)
            except IntegrityError:
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "category", "known_game"]),
                    reply_markup=ReplyKeyboardRemove())
                inline_text = ps.read_json(["inline_handler", "category", "shrink_known_game"]).format(title=query_csv[2])
                shrink_keyboard(update, context, inline_text)
                return
        context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "category", "added_game"]),
                    reply_markup=ReplyKeyboardRemove())
        inline_text = ps.read_json(["inline_handler", "category", "shrink_added_game"]).format(title=query_csv[2])
        shrink_keyboard(update, context, inline_text)
    else:
        pass
    QueryBuffer().clear_query(
        update.callback_query.message.message_id)


def generate_categories(first=False, pressed=None):
    keyboard = []
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    categories = config.getlist('GameCategories', 'categories')  # no, this is no error. getlist is created by converter above
    for cat in categories:
        row = []
        if pressed and (cat in pressed):
            data = ";".join(["CATEGORY", cat, "UNSET"])
            label = cat + " ✓"
            row.append(InlineKeyboardButton(label, callback_data=data))
        else:
            data = ";".join(["CATEGORY", cat, "SET"])
            row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []
    if first:
        data = ";".join(["CATEGORY", "none"])
        row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "category", "none"]), callback_data=data))
    else:
        data = ";".join(["CATEGORY", "done"])
        row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "done_keyboard"]), callback_data=data))
    data = ";".join(["CATEGORY", "stop"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "stop_keyboard"]), callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_findbycategory(update, context):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "stop":
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=ps.read_json(["inline_handler", "stop_interaction"]),
            reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "stop_shrink"]))
    elif category == "IGNORE":
        pass
    else:  # got a category
        opt = []
        entries = dbf.get_playable_entries_by_category(
                    'games', 'title',
                    update.callback_query.from_user.username, category)
        for e in entries:
            opt.append(parse_single_db_entry_to_string(e))
        if opt:
            game = opt[randrange(len(opt))]
            context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=ps.read_json(["inline_handler", "handle_findbycategory", "proposal"]).format(title=game),
                        reply_markup=ReplyKeyboardRemove())
        else:
            context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=ps.read_json(["inline_handler", "handle_findbycategory", "none_available"]),
                        reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, category)


def generate_findbycategory():
    keyboard = []
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    categories = config.getlist('GameCategories', 'categories')  # no, this is no error. getlist is created by converter above
    for cat in categories:
        row = []
        data = ";".join(["FINDBY", cat])
        row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []
    data = ";".join(["FINDBY", "IGNORE"])
    row.append(InlineKeyboardButton(' ', callback_data=data))
    data = ";".join(["FINDBY", "stop"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "stop_keyboard"]), callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_pollbycategory(update, context):
    update.callback_query.answer()
    category = update.callback_query.data.split(";")[1]
    if category == "stop":
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=ps.read_json(["inline_handler", "stop_interaction"]),
            reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "stop_shrink"]))
    elif category == "IGNORE":
        pass
    else:  # got a category
        plan = GameNight()
        check = plan.set_poll(update.callback_query.from_user.username,
                              category=category)
        if check < 0:
            context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=ps.read_json(["inline_handler", "handle_pollbycategory", "no_poll"]),
                        reply_markup=ReplyKeyboardRemove())
        else:
            keys = []
            for o in plan.poll.options:
                keys.append([KeyboardButton(o)])
            context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=ps.read_json(["inline_handler", "handle_pollbycategory", "what_game"]),
                        reply_markup=ReplyKeyboardMarkup(
                                        keys, one_time_keyboard=True))
        shrink_keyboard(update, context, category)


def generate_pollbycategory():
    keyboard = []
    config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
    config_path = os.path.dirname(os.path.realpath(__file__))
    config.read(os.path.join(config_path, "config.ini"))
    categories = config.getlist('GameCategories', 'categories')  # no, this is no error. getlist is created by converter above
    for cat in categories:
        row = []
        data = ";".join(["POLLBY", cat])
        row.append(InlineKeyboardButton(cat, callback_data=data))
        keyboard.append(row)
    # last row: no statement and /stop button
    row = []
    data = ";".join(["POLLBY", "IGNORE"])
    row.append(InlineKeyboardButton(' ', callback_data=data))
    data = ";".join(["POLLBY", "stop"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "stop_keyboard"]), callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_settings(update, context):
    update.callback_query.answer()
    setting = update.callback_query.data.split(";")[1]
    if setting == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=ps.read_json(["inline_handler", "stop_interaction"]),
            reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, "Abbruch.")
    elif setting == "done":
        query = QueryBuffer().get_query(update.callback_query.message.message_id)
        settings_type = ps.parse_csv_to_array(query)[0]
        end_of_settings(update, context, settings_type)
    else:  # we actually got a setting, now register it
        if update.callback_query.data.split(";")[2] == "SET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id) + setting + "/"
            settings_so_far = ps.parse_csv_to_array(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
            QueryBuffer().edit_query(update.callback_query.message.message_id, query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                              chat_id=update.callback_query.message.chat_id,
                                              message_id=update.callback_query.message.message_id,
                                              reply_markup=generate_settings(ps.parse_csv_to_array(query)[0], to_set=settings_so_far))
            except BadRequest:
                pass
        elif update.callback_query.data.split(";")[2] == "UNSET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id)
            query_csv = ps.parse_csv_to_array(query)
            settings_so_far = query_csv[-1].split('/')[:-1]
            settings_so_far.remove(setting)
            settings_string = '/'.join(settings_so_far)
            if len(settings_string) > 0:
                settings_string += '/'
            new_query = ps.parse_array_to_csv(query_csv[:-1]) + ',' + settings_string
            QueryBuffer().edit_query(update.callback_query.message.message_id, new_query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                              chat_id=update.callback_query.message.chat_id,
                                              message_id=update.callback_query.message.message_id,
                                              reply_markup=generate_settings(ps.parse_csv_to_array(query)[0], to_set=settings_so_far))
            except BadRequest:
                pass


def end_of_settings(update, context, settings_type):
    query = QueryBuffer().get_query(update.callback_query.message.message_id)
    # query looks like: settings_private,username,notify_participation/notify_vote/
    # or: settings_group,title,notify_not_admin/notify_unauthorized
    if "settings" in ps.parse_csv_to_array(query)[0]:
        to_set = ps.parse_csv_to_array(query)[-1].split('/')[:-1]
        to_unset = []
        if ps.parse_csv_to_array(query)[0] == "settings_private":
            possible_settings = ['notify_participation', 'notify_vote']
            table = "settings"
        else:  # ps.parse_csv_to_array(query)[0] == "settings_group":
            possible_settings = ['notify_not_admin', 'notify_unauthorized']
            table = "group_settings"
        for _ in possible_settings:
            if _ not in to_set:
                to_unset.append(_)
        who = ps.parse_csv_to_array(query)[1]
        dbf.update_settings(table, who, to_set, to_unset)
        context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "settings", "set"]),
                    reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "settings", "shrink_set"]))
    else:
        pass
    QueryBuffer().clear_query(
        update.callback_query.message.message_id)


# when generated the first time, set "first" and "user" to look up the current settings
# also, store in init_array the settings already set to initialize query buffer
# later, just keep track of what the user selected up until now
def generate_settings(settings_type, to_set=None, first=None, who=None, init_array=None):
    if settings_type == "settings_group":
        table = "group_settings"
        entry = "id"
        settings = {ps.read_json(["inline_handler", "settings", "not_admin"]): 'notify_not_admin',
                    ps.read_json(["inline_handler", "settings", "no_privatechat"]): 'notify_unauthorized'}
    else:  # settings_type == "settings_private"
        table = "settings"
        entry = "user"
        settings = {ps.read_json(["inline_handler", "settings", "participation"]): 'notify_participation',
                    ps.read_json(["inline_handler", "settings", "votes"]): 'notify_vote'}
    if first:
        current_settings = dbf.search_column_with_constraint(dbf.choose_database("datadb"), table, "*", entry, who)[0][1:]
        # current_settings = dbf.search_single_entry(dbf.choose_database("datadb"), table, entry, who)[0][1:]
    keyboard = []
    if first:
        index = 0
        for (key, value) in settings.items():
            row = []
            if current_settings[index] == 1:
                data = ";".join(["SETTING", value, "UNSET"])
                label = key + " ✓"
                row.append(InlineKeyboardButton(label, callback_data=data))
                # init query buffer
                init_array.append(value)
            else:
                data = ";".join(["SETTING", value, "SET"])
                row.append(InlineKeyboardButton(key, callback_data=data))
            keyboard.append(row)
            index += 1
    else:
        for (key, value) in settings.items():
            row = []
            if to_set and (value in to_set):
                data = ";".join(["SETTING", value, "UNSET"])
                label = key + " ✓"
                row.append(InlineKeyboardButton(label, callback_data=data))
            else:
                data = ";".join(["SETTING", value, "SET"])
                row.append(InlineKeyboardButton(key, callback_data=data))
            keyboard.append(row)
    # last row: done and /stop button
    row = []
    data = ";".join(["SETTING", "done"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "done_keyboard"]), callback_data=data))
    data = ";".join(["SETTING", "stop"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "stop_keyboard"]), callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_household(update, context):
    update.callback_query.answer()
    member = update.callback_query.data.split(";")[1]
    if member == "stop":
        QueryBuffer().clear_query(update.callback_query.message.message_id)
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=ps.read_json(["inline_handler", "stop_interaction"]),
            reply_markup=ReplyKeyboardRemove())
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "no_keyboard"]))
        if LogToMessageFilter().ask_chat_type == "private":
            context.bot.send_message(chat_id=update.callback_query.message.chat_id,
                                     text=ps.read_json(["inline_handler", "household", "ask_debug"]),
                                     reply_markup=generate_debug())
    elif member == "done":
        end_of_household(update, context)
    else:  # got a household member
        if update.callback_query.data.split(";")[2] == "SET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id) + member + "/"
            members_so_far = ps.parse_csv_to_array(query)[-1].split('/')[:-1]  # last one is empty since set ends on /
            remove = ps.parse_csv_to_array(query)[1]  # don't let user select himself...
            QueryBuffer().edit_query(update.callback_query.message.message_id, query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                              chat_id=update.callback_query.message.chat_id,
                                              message_id=update.callback_query.message.message_id,
                                              reply_markup=generate_household(remove, to_set=members_so_far))
            except BadRequest:
                pass
        elif update.callback_query.data.split(";")[2] == "UNSET":
            query = QueryBuffer().get_query(update.callback_query.message.message_id)
            query_csv = ps.parse_csv_to_array(query)
            remove = query_csv[1]
            members_so_far = query_csv[-1].split('/')[:-1]
            members_so_far.remove(member)
            members_string = '/'.join(members_so_far)
            if len(members_string) > 0:
                members_string += '/'
            new_query = ps.parse_array_to_csv(query_csv[:-1]) + ',' + members_string
            QueryBuffer().edit_query(update.callback_query.message.message_id, new_query)
            # change keyboard layout
            try:
                context.bot.edit_message_text(text=update.callback_query.message.text,
                                              chat_id=update.callback_query.message.chat_id,
                                              message_id=update.callback_query.message.message_id,
                                              reply_markup=generate_household(remove, to_set=members_so_far))
            except BadRequest:
                pass


def end_of_household(update, context):
    query = QueryBuffer().get_query(update.callback_query.message.message_id)
    # query looks like: household,username,member1/member2
    query_csv = ps.parse_csv_to_array(query)
    members = query_csv[-1].split('/')[:-1]
    if "household" in query_csv[0]:
        household = [query_csv[1]] + members
        dbf.add_household(household)
        context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=ps.read_json(["inline_handler", "household", "ok"]),
                    reply_markup=ReplyKeyboardRemove())
        shrink_label = " ".join(household)
        shrink_keyboard(update, context, shrink_label)
        if LogToMessageFilter().ask_chat_type == "private":
            update.message.bot.send_message(chat_id=update.callback_query.message.chat_id,
                                            text=ps.read_json(["inline_handler", "household", "ask_debug"]),
                                            reply_markup=generate_debug())
    else:
        pass
    QueryBuffer().clear_query(
        update.callback_query.message.message_id)


def generate_household(remove, first=False, to_set=None):
    usernames_db = dbf.select_columns(dbf.choose_database("datadb"), "settings", "user")
    usernames = list()
    for _ in usernames_db:
        usernames.append(_[0])
    usernames.remove(remove)
    keyboard = []
    # if this is the first user we meet, there is no need to ask!
    if len(usernames) == 0:
        raise IndexError
    for name in usernames:
        row = []
        if to_set and name in to_set:
            label = name + " ✓"
            data = ";".join(["HOUSEHOLD", name, "UNSET"])
        else:
            label = name
            data = ";".join(["HOUSEHOLD", name, "SET"])
        row.append(InlineKeyboardButton(label, callback_data=data))
        keyboard.append(row)
    # last row: done and /stop button
    row = []
    if not first:
        data = ";".join(["HOUSEHOLD", "done"])
        row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "done_keyboard"]), callback_data=data))
    data = ";".join(["HOUSEHOLD", "stop"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "no_keyboard"]), callback_data=data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_debug(update, context):
    update.callback_query.answer()
    answer = update.callback_query.data.split(";")[1]
    if answer == "YES":
        LogToMessageFilter().set_chat_id(update.callback_query.message.chat_id)
        LogToMessageFilter().set_bot(context.bot)
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "debug", "yes"]))
    else:
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "debug", "no"]))


def generate_debug():
    keyboard = []
    row = []
    yes_data = ";".join(["DEBUG", "YES"])
    no_data = ";".join(["DEBUG", "NO"])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "debug", "yes"]), callback_data=yes_data))
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "debug", "no"]), callback_data=no_data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def handle_csv_import(update, context):
    update.callback_query.answer()
    answer = update.callback_query.data.split(";")[1]
    if answer == "YES":
        msg_id = update.callback_query.data.split(";")[2]
        rep.ForceReplyJobs().is_set(msg_id)
        rep.ForceReplyJobs().clear_query(msg_id)
        shrink_keyboard(update, context, ps.read_json(["inline_handler", "csv_import", "shrink_ended"]))


def generate_csv_import(msg_id):
    keyboard = []
    row = []
    yes_data = ";".join(["CSV_IMPORT", "YES", str(msg_id)])
    row.append(InlineKeyboardButton(ps.read_json(["inline_handler", "csv_import", "yes_keyboard"]), callback_data=yes_data))
    keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)
