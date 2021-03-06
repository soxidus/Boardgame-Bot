from icalendar import Calendar, Event
from datetime import datetime
from os import remove

from parse_strings import generate_uuid_32


def create_ics_file(title, date):
    calendar = Calendar()
    calendar.add('prodid', '-//Meeple - Auto-Ical//')
    calendar.add('version', '2.0')
    gamenight_event = Event()
    gamenight_event.add('dtstamp', datetime.now())
    gamenight_event.add('summary', title)
    gamenight_event.add('description', 'Created by Meeple the boardgame bot')
    gamenight_event.add('dtstart', datetime.strptime(str(date) + " 19", "%Y-%m-%d 00:00:00 %H"))
    gamenight_event.add('dtend',  datetime.strptime(str(date) + " 23", "%Y-%m-%d 00:00:00 %H"))
    calendar.add_component(gamenight_event)
    filename = 'cal-' + generate_uuid_32() + '.ics'

    with open(filename, 'wb') as my_file:
        my_file.write(calendar.to_ical())

    return filename


def delete_ics_file(filename):
    try:
        remove(filename)
    except OSError:
        pass
