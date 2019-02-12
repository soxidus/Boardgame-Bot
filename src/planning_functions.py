# Singleton pattern implementation from https://www.python.org/download/releases/2.2/descrintro/#__new__
class Singleton(object):
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it
    def init(self, *args, **kwds):
        pass

class GameNight(Singleton):
    def init(self):
        self.date = None
        self.poll = None
        self.participants = []

    def set_date(self, date):
        self.date = date

    def set_poll(self):
        self.poll = Poll(self.participants)

    def clear(self):
        self.init()

    def add_participant(self, user_id):
        self.participants.append(user_id)

    def remove_participant(self,user_id):
        self.participants.remove(user_id)
    

class Poll(object):
    def __init__(self, participants):
        pass