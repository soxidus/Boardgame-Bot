# coding=utf-8

def handle_bot_not_admin(bot, chat_id):
    bot_is_admin = False
    for _ in bot.get_chat_administrators(chat_id):
        if _.user.username == bot.username:
            bot_is_admin = True  # error was raised because no modification occurs
    if not bot_is_admin:
        bot.send_message(chat_id, 
                         'Hey Leute, leider bin ich hier kein Admin. '
                         'Deswegen kann ich ein paar meiner Funktionen nicht nutzen:\n'
                         '- Gruppennamen verändern '
                         '(um das Datum des nächsten Spieleabends einzutragen)\n'
                         '- Gruppenbeschreibung verändern '
                         '(um eine Teilnehmerliste zu führen)\n'
                         '- Nachrichten von anderen Gruppenmitgliedern löschen '
                         '(ZENSUR! Nein, im Ernst, es macht alles übersichtlicher.)\n'
                         'Bitte überlegt euch, ob ihr das wirklich verpassen wollt :)')


def handle_bot_unauthorized(update, context):
    context.bot.send_message(update.message.chat_id, 'OH! '
                                                    'scheinbar darf ich nicht privat mit dir Reden.'
                                                    'Versuche dich privat mit start oder key'
                                                    'zu authorisieren und dann probiere /'
                                                    + __name__ +
                                                    ' nochmal'
                                                    )