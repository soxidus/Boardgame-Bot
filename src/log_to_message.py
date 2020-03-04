import io

debug_chat = None
log_capture_string = io.StringIO()


print(log_capture_string.getvalue())


def log_to_message(bot, logging_message):
    if type(debug_chat) == int:
        bot.send_message(debug_chat, logging_message)
