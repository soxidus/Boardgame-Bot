from ics import Calendar, Event
from os import remove
import datetime
from parse_strings import generate_uuid_32


def create_ics_file(title, date):
    calendar = Calendar()
    gn = GameNight()
    gamenight_event = Event()
    gamenight_event.name = title
    gamenight_event.begin = date.datetime.isoformat()
    calendar.events.add(gamenight_event)
    filename = 'cal-' + generate_uuid_32() + '.ics'
    gn(chat_id=update.callback_query.message.chat_id).set_cal_file(filename)
    gamenight_event.make_all_day()
    with open(filename, 'w+') as my_file:
        my_file.writelines(c)


def delete_ics_file(filename):
    try:
        remove(filename)
    except OSError:
        pass
