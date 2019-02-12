from database_functions import *
from random import randrange

def init_plan():
    global plan
    plan = GameNight()

class GameNight(object):
    def __init__(self):
        self.date = None
        self.poll = None
        self.participants = []

    def get_participants(self):
        result = ""
        for p in self.participants:
            result = result + p + "\n"
        return result

    def set_date(self, date):
        if self.date is None:
            self.date = date
            return 0
        else:
            return -1

    def set_poll(self):
        if self.poll is None and self.date is not None:
            self.poll = Poll(self.participants)
            return 0
        else:
            return -1

    def clear(self):
        self.__init__()

    def add_participant(self, user_id):
        if self.date is not None:
            self.participants.append(user_id)
            if self.poll is not None:
                self.poll.add_voter(user_id)            

    # Caution: the player only gets removed from game night. He can still vote because it's too much overhead to handle it differently.
    def remove_participant(self, user_id):
        self.participants.remove(user_id)

class Poll(object):
    def __init__(self, participants):
        self.options = self.generate_options(participants)
        self.current_votes = []
        for p in participants:
            self.current_votes.append([p, None])
        self.result = []
        for o in self.options:
            self.result.append([o, 0])

    def add_voter(self, user_id):
        self.current_votes.append([user_id, None])

    def generate_options(self, participants):
        games = set()
        for p in participants:
            games.update(search_entries_by_user(choose_database("testdb"), "games", p).split(","))
        games = list(games)
        options = []
        for _ in range(4):
            options.append(games[randrange(len(games))])
        return options

    # who is the username, what is the option they voted for (i.e. text)
    # returns -1 if voter wasn't allowed to vote, 0 if they voted for the same, else 1
    def register_vote(self, who, what):
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
                # has already voted & changed his vote
                else:
                    # remember this person's current vote
                    row[1] = what
                    for o in self.result:
                        if o == old_vote:
                            o[1] -= 1
                        elif o == what:
                            o[1] += 1
                    return 1
            else:
                row[1] = what
                for o in self.result:
                    if o == what:
                        o[1] += 1
                return 1
        else:
            return -1