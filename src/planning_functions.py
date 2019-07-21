from random import randrange
from database_functions import *
from singleton import Singleton

def handle_vote(bot, update):
    plan = GameNight()
    if plan.poll is not None:
        check = plan.poll.register_vote(update.message.from_user.username, update.message.text)
        if check == 0:
            bot.send_message(update.message.from_user.id, "Okay " + update.message.from_user.first_name +
                                      ", du hast erneut für " + update.message.text +
                                      " gestimmt. Du musst mir das nicht mehrmals sagen, ich bin fähig ;)")
        elif check < 0:
            bot.send_message(update.message.from_user.id, "Das hat nicht funktioniert. Vielleicht darfst du gar nicht abstimmen, "
                                      + update.message.from_user.first_name + "?")
        else:
            bot.send_message(update.message.from_user.id, "Okay " + update.message.from_user.first_name +
                                      ", du hast für " + update.message.text + " gestimmt.")

class GameNight(Singleton):
    def init(self):
        self.date = None
        self.poll = None
        self.old_poll = None
        self.participants = []

    def get_participants(self):
        if self.date:
            result = "Beim Spieleabend " + self.date + " nehmen teil:\n"
            for p in self.participants:
                result = result + p + "\n"
        else:
            result = "Derzeit ist kein Spieleabend geplant. Das kannst du mit /neuertermin ändern!"
        return result

    def set_date(self, date):
        if self.date is None:
            self.date = date
            self.old_poll = None
            return 0
        return -1

    def set_poll(self, user_id, game=None):
        if self.poll is None and self.date is not None:
            if user_id in self.participants:
                self.poll = Poll(self.participants, game)
                self.old_poll = None
                return 0
        return -1

    def end_poll(self, user_id):
        check = self.poll.end(user_id)
        if check < 0:
            return check
        self.old_poll = self.poll
        self.poll = None
        return 0

    def clear(self):
        if self.poll:
            self.old_poll = self.poll
        try:
            self.old_poll.running = False # this is important for flushing command
        except AttributeError:
            pass
        self.date = None
        self.poll = None
        self.participants = []

    def add_participant(self, user_id):
        if self.date is not None:
            self.participants.append(user_id)
            if self.poll is not None:
                self.poll.add_voter(user_id)
            return 0
        return -1

    # Caution: the player only gets removed from game night. He can still vote because it's too much overhead
    # to handle it differently.
    def remove_participant(self, user_id):
        try:
            self.participants.remove(user_id)
        except ValueError:
            return -1
        else:
            return 0


class Poll(object):
    def __init__(self, participants, game):
        self.running = True
        if game:
            self.options = self.generate_options_exp(participants, game)
        else:
            self.options = self.generate_options(participants)
        self.current_votes = []
        for p in participants:
            self.current_votes.append([p, None])
        self.result = []
        for o in self.options:
            self.result.append([o, 0])

    def add_voter(self, user_id):
        self.current_votes.append([user_id, None])

    # remove last vote and disable voting for this user
    def remove_voter(self, user_id):
        for row in self.current_votes:
            if row[0] == user_id:
                last_vote = row[1]
                self.current_votes.remove(row)
        # did he even vote?
        if last_vote:
            for o in self.result:
                if o[0] == last_vote:
                    o[1] -= 1

    def generate_options(self, participants):
        games = set() # use a set because it takes care of duplicates immediately
        for p in participants:
            entries = get_playable_entries(choose_database("testdb"), 'games', 'title', p, no_participants=len(participants))
            for e in entries:
                games.add(single_db_entry_to_string(e))
        games = list(games) # convert to list so we can index it randomly

        options = []
        if len(games) < 4:
            no_opts = len(games)
        else:
            no_opts = 4

        i = 0
        while i < no_opts:
            opt = games[randrange(len(games))]
            if opt not in options:
                options.append(opt)
                i += 1

        return options

    def generate_options_exp(self, participants, game):
        exp = set() # use a set because it takes care of duplicates immediately
        for p in participants:
            uuid = search_uuid(p, game)
            entries = get_playable_entries(choose_database("testdb"), 'expansions', 'title', p, uuid=uuid)
            for e in entries:
                exp.add(single_db_entry_to_string(e))
        exp = list(exp) # convert to list so we can index it randomly

        options = []
        no_opts = len(exp)

        i = 0
        while i < no_opts:
            opt = exp[randrange(len(exp))]
            if opt not in options:
                options.append(opt)
                i += 1

        return options        

    # who is the username, what is the option they voted for (i.e. text)
    # returns -1 if voter wasn't allowed to vote, 0 if they voted for the same, else 1
    def register_vote(self, who, what):
        if not self.running:
            return -1
        allowed = False
        for row in self.current_votes:
            if row[0] == who:
                allowed = True
                old_vote = row[1]
                break
        # check whether voter was registered for game night
        if allowed:
            # has voted before
            if old_vote:
                # this person voted for the same thing again
                if old_vote == what:
                    return 0
                # has already voted & changed his vote:
                row[1] = what
                for o in self.result:
                    if o[0] == old_vote:
                        o[1] -= 1
                    elif o[0] == what:
                        o[1] += 1
                return 1
            # first vote
            row[1] = what
            for o in self.result:
                if o[0] == what:
                    o[1] += 1
            return 1
        return -1

    def print_votes(self):
        out = ""
        for row in self.result:
            out += row[0] + ": " + str(row[1]) + "\n"
        return out

    # stops people from voting
    def end(self, user_id):
        if not self.running:
            return 0
        allowed = False
        for row in self.current_votes:
            if row[0] == user_id:
                allowed = True
                break
        if allowed:
            self.running = False
            return 0
        return -1
