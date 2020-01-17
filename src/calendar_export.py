from ics import Calendar, Event
from parse_strings import parse_date, generate_uuid_32


def create_ics_file(title, date):
    calendar = Calendar()
    gamenight_event = Event()
    gamenight_event.name = title
    gamenight_event.begin = parse_date(date)
    calendar.events.add(gamenight_event)

    with open(generate_uuid_32(), 'w+') as my_file:
        my_file.writelines(c)
