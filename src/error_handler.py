# coding=utf-8

from database_functions import check_notify
from parse_strings import read_json


def handle_bot_not_admin(bot, chat_id):
    bot_is_admin = False
    for _ in bot.get_chat_administrators(chat_id):
        if _.user.username == bot.username:
            bot_is_admin = True  # error was raised because no modification occurs
    notify = check_notify("group_settings", chat_id, "notify_not_admin")
    if not bot_is_admin and notify:
        bot.send_message(chat_id,
                         read_json(["error_handler", "not_admin"]))


def handle_bot_unauthorized(bot, chat_id, user, try_again=None):
    text = (read_json(["error_handler", "not_authorised"]).format(name=user))
    if try_again:
        text += read_json(["error_handler", "try_again"]).format(try_what=try_again)
    notify = check_notify("group_settings", chat_id, "notify_unauthorized")
    if notify:
        bot.send_message(chat_id, text)
