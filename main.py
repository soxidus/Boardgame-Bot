import time
import telepot
from telepot.loop import MessageLoop

"""
Commands:
    key                 - Authentifiziere dich!
    neuertermin         - Wir wollen spielen! (nur in Gruppen)
    ich                 - Nimm am nächsten Spieleabend teil!
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


def commands(msg):
    chat_id = msg['chat']['id']
    command = msg['text']

    print('Got command: %s' % command)

    if command == '/key':
        bot.sendMessage(chat_id, "Authenticate!!")
    elif command.startswith('/'):
        bot.sendMessage(chat_id, command)
        bot.sendMessage(chat_id, "So far this does nothing else!")


# Run stuff

# chris temp test bot
# bot = telepot.Bot('745861447:AAFgmej56K8weT-dpaxe97A6Ak-pTOptk-s')

# real test bot
bot = telepot.Bot('702260882:AAF3VcoDbf3sSRVDht5xM3JYu-QNywEpgZg')

MessageLoop(bot, commands).run_as_thread()

print('I am listening ...')

while 1:
    time.sleep(10)
