# coding=utf-8

from database_functions import check_notify


def handle_bot_not_admin(bot, chat_id):
    bot_is_admin = False
    for _ in bot.get_chat_administrators(chat_id):
        if _.user.username == bot.username:
            bot_is_admin = True  # error was raised because no modification occurs
    notify = check_notify("group_settings", chat_id, "notify_not_admin")
    if not bot_is_admin and notify:
        bot.send_message(chat_id,
                         'Hey Leute, leider bin ich hier kein Admin. '
                         'Das fällt gerade auf, weil ich so ein paar '
                         'meiner Funktionen nicht nutzen kann:\n'
                         '- Gruppennamen verändern '
                         '(um das Datum des nächsten Spieleabends einzutragen)\n'
                         '- Gruppenbeschreibung verändern '
                         '(um eine Teilnehmerliste zu führen)\n'
                         '- Nachrichten von anderen Gruppenmitgliedern löschen '
                         '(ZENSUR! Nein, im Ernst, es macht alles übersichtlicher.)\n'
                         'Bitte überlegt euch, ob ihr das wirklich verpassen wollt :)')


def handle_bot_unauthorized(bot, chat_id, user, try_again=None):
    text = ('OH! Scheinbar darf ich nicht privat mit dir reden, ' +
            user + '. '
            'Versuche, dich in einem Privatchat mit mir '
            'mit /start oder /key zu authentifizieren.')
    if try_again:
        text += ' Danach kannst du ' + try_again + ' nochmal probieren.'
    notify = check_notify("group_settings", chat_id, "notify_unauthorized")
    if notify:
        bot.send_message(chat_id, text)
