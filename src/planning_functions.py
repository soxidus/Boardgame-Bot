# coding=utf-8

import datetime
import re
from telegram.error import BadRequest
from random import randrange
from database_functions import (get_playable_entries, choose_database,
                                search_uuid, update_game_date)
from singleton import Singleton
from parse_strings import single_db_entry_to_string


def handle_vote(bot, update):
    plan = GameNight()
    if plan.poll is not None:
        check = plan.poll.register_vote(
            update.message.from_user.username, update.message.text)
        if check == 0:
            bot.send_message(update.message.from_user.id,
                             "Okay " + update.message.from_user.first_name +
                             ", du hast erneut für " + update.message.text +
                             " gestimmt. Du musst mir das nicht mehrmals "
                             "sagen, ich bin fähig ;)")
        elif check < 0:
            bot.send_message(update.message.from_user.id,
                             "Das hat nicht funktioniert. "
                             "Vielleicht darfst du gar nicht abstimmen, " +
                             update.message.from_user.first_name + "?")
        else:
            bot.send_message(update.message.from_user.id,
                             "Okay " + update.message.from_user.first_name +
                             ", du hast für " + update.message.text +
                             " gestimmt.")


def test_termin(bot):
    now = datetime.datetime.now()
    plan = GameNight()
    if plan:
        r = re.compile('.{2}/.{2}/.{4}')
        if r.match(plan.date) is not None:
            d = datetime.datetime.strptime(plan.date, '%d/%m/%Y')
            if d < now:
                plan = GameNight()
                try:
                    bot.set_chat_description(plan.chat_id, "")
                except BadRequest:
                    pass
                bot.set_chat_title(plan.chat_id, 'Spielwiese')
                plan.clear()


class GameNight(Singleton):
    def init(self, chat_id=None):
        self.date = None
        self.poll = None
        self.old_poll = None
        self.participants = []
        self.chat_id = chat_id

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
                try:
                    self.poll = Poll(self.participants, game)
                except ValueError as v:
                    print(v)
                    self.poll = None
                    return -1
                self.old_poll = None
                return 0
        return -1

    def end_poll(self, user_id):
        check = self.poll.end(user_id)
        if check < 0:
            return check
        self.register_poll_winner()
        self.old_poll = self.poll
        self.poll = None
        return 0

    def clear(self):
        if self.poll:
            self.old_poll = self.poll
        try:
            self.old_poll.running = False  # this is important for /leeren
        except AttributeError:
            pass
        self.date = None
        self.poll = None
        self.participants = []
        self.chat_id = None

    def add_participant(self, user_id):
        if self.date is not None:
            self.participants.append(user_id)
            if self.poll is not None:
                self.poll.add_voter(user_id)
            return 0
        return -1

    def remove_participant(self, user_id):
        try:
            self.participants.remove(user_id)
            self.poll.remove_voter(user_id)
        except ValueError:
            return -1
        else:
            return 0

    def register_poll_winner(self):
        max_votes = 0
        winner_so_far = None
        more_than_one_winner = False
        for row in self.poll.result:
            if row[1] > max_votes:
                max_votes = row[1]
                winner_so_far = row[0]
                more_than_one_winner = False
            elif row[1] == max_votes:
                more_than_one_winner = True

        if winner_so_far is not None:  # at least one vote was given
            winners = []

            if more_than_one_winner:
                for row in self.poll.result:
                    if row[1] == max_votes:
                        winners.append(row[0])
            else:
                winners.append(winner_so_far)

            for w in winners:
                r = re.compile('.{2}/.{2}/.{4}')
                if r.match(self.date) is not None:
                    d = datetime.datetime.strptime(self.date, '%d/%m/%Y')
                    update_game_date(w, d)


class Poll(object):
    def __init__(self, participants, game):
        self.running = True
        if game:
            self.options = self.generate_options_exp(participants, game)
            if self.options is None:
                raise ValueError
        else:
            self.options = self.generate_options(participants)
            if self.options is None:
                raise ValueError
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
        categories = {'groß': 0, 'klein': 1, 'Würfel': 2, 'Rollenspiel': 3,
                      'Karten': 4, 'Worker Placement': 5, 'keine': 6}
        games_by_category = []
        games_general_set = set()
        for _ in categories:
            games_by_category.append(set())  # use a set because it takes care of duplicates
        plan = GameNight()
        if plan:
            r = re.compile('.{2}/.{2}/.{4}')
            if r.match(plan.date) is not None:
                d = datetime.datetime.strptime(plan.date, '%d/%m/%Y')
        else: d = None
        for p in participants:
            entries = get_playable_entries(
                choose_database("testdb"), 'games', 'title, categories', p,
                no_participants=len(participants), planned_date=d)
            for _ in range(len(entries)):
                cats = entries[_][1].split("/")[:-1]  # ignore last entry since it's empty
                if not cats:
                    games_by_category[categories['keine']].add(single_db_entry_to_string(entries[_][0]))
                for cat in cats:
                    games_by_category[categories[cat]].add(single_db_entry_to_string(entries[_][0]))
                games_general_set.add(single_db_entry_to_string(entries[_][0]))  # keeps track of actual amount of games available this evening

        available_games_count = len(games_general_set)
        for _ in range(len(games_by_category)):
            games_by_category[_] = list(games_by_category[_])  # convert to list so we can index it randomly

        options = []
        if available_games_count < 6:
            no_opts = available_games_count
        else:
            no_opts = 6

        if no_opts < 2:
            if no_opts < 1:
                # there's no games to play! Shame.
                return None
            # exactly one game
            for _ in games_by_category:
                if len(_) > 0:
                    options.append(_[0])
                    break

        else:            
            i = 0
            # select one small game
            small_set = games_by_category[categories['klein']]
            if len(small_set) > 0:
                opt = small_set[randrange(len(small_set))]
                options.append(opt)
                i += 1

            # select one big game
            big_set = games_by_category[categories['groß']]
            if len(big_set) > 0:
                while i < 2:
                    opt = big_set[randrange(len(big_set))]
                    if opt not in options:
                        options.append(opt)
                        i += 1
                        break  # make sure only one big game is added
                    elif len(big_set) == 1:
                        # big game is the small game already added - does this even make sense?
                        break
            
            # fill the rest of options up
            while i < no_opts:
                category = randrange(len(games_by_category))
                category_set = games_by_category[category]
                if len(category_set) > 0:
                    opt = category_set[randrange(len(category_set))]
                    if opt not in options:
                        options.append(opt)
                        i += 1

        return options

    def generate_options_exp(self, participants, game):
        exp = set()  # use a set because it takes care of duplicates
        for p in participants:
            uuid = search_uuid(p, game)
            if uuid:
                entries = get_playable_entries(
                    choose_database("testdb"), 'expansions', 'title',
                    p, uuid=uuid)
                for e in entries:
                    exp.add(single_db_entry_to_string(e))
        exp = list(exp)  # convert to list so we can index it randomly

        if len(exp) == 0:  # no participant owns an expansion for this game
            return None
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
    # returns -1 if voter wasn't allowed to vote,
    # 0 if they voted for the same, else 1
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
