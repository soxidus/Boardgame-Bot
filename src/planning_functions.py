# coding=utf-8

import datetime
import re
import configparser
import os
from telegram.error import (BadRequest, Unauthorized)
from random import randrange
from database_functions import (get_playable_entries, choose_database,
                                search_uuid, update_game_date,
                                get_playable_entries_by_category,
                                check_notify)
from singleton import Singleton
from calendar_export import delete_ics_file
from parse_strings import single_db_entry_to_string


def handle_vote(update, context):
    plan = GameNight()
    if plan.poll is not None:
        check = plan.poll.register_vote(
            update.message.from_user.username, update.message.text)
        send_message = check_notify(update.message.from_user.username, "notify_vote")
        if check == 0 and send_message:
            try:
                context.bot.send_message(update.message.from_user.id,
                                         "Okay " + update.message.from_user.first_name +
                                         ", du hast erneut für " + update.message.text +
                                         " gestimmt. Du musst mir das nicht mehrmals "
                                         "sagen, ich bin fähig ;)")
            except Unauthorized:
                context.bot.send_message(update.message.chat_id, 'OH! '
                                         'scheinbar darf ich nicht mit dir Reden.'
                                         'Versuche dich privat mit start oder key'
                                         'zu authorisieren und dann probiere /'
                                         + __name__ +
                                         ' nochmal')
        elif check < 0:
            try:
                context.bot.send_message(update.message.from_user.id,
                                         "Das hat nicht funktioniert. "
                                         "Vielleicht darfst du gar nicht abstimmen, " +
                                         update.message.from_user.first_name + "?")
            except Unauthorized:
                context.bot.send_message(update.message.chat_id, 'OH! '
                                         'scheinbar darf ich nicht mit dir Reden.'
                                         'Versuche dich privat mit start oder key'
                                         'zu authorisieren und dann probiere /'
                                         + __name__ +
                                         ' nochmal')
        else:
            try:
                context.bot.send_message(update.message.from_user.id,
                                         "Okay " + update.message.from_user.first_name +
                                         ", du hast für " + update.message.text +
                                         " gestimmt.")
            except Unauthorized:
                context.bot.send_message(update.message.chat_id, 'OH! '
                                         'scheinbar darf ich nicht mit dir Reden.'
                                         'Versuche dich privat mit start oder key'
                                         'zu authorisieren und dann probiere /'
                                         + __name__ +
                                         ' nochmal')


def test_termin(context):
    now = datetime.datetime.now()
    plan = GameNight()
    if plan:
        r = re.compile('.{2}/.{2}/.{4}')
        if r.match(plan.date) is not None:
            d = datetime.datetime.strptime(plan.date, '%d/%m/%Y')
            if d < now:
                plan = GameNight()
                try:
                    context.bot.set_chat_description(plan.chat_id, "")
                except BadRequest:
                    pass
                context.bot.set_chat_title(plan.chat_id, 'Spielwiese')
                plan.clear()


class GameNight(Singleton):
    def init(self, chat_id=None):
        self.date = None
        self.poll = None
        self.old_poll = None
        self.participants = []
        self.chat_id = chat_id
        self.cal_file = None

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

    def set_poll(self, user_id, game=None, category=None):
        if self.poll is None and self.date is not None:
            if user_id in self.participants:
                try:
                    self.poll = Poll(self.participants, game, category)
                except ValueError:
                    self.poll = None
                    return -1
                self.old_poll = None
                return 0
        return -1

    def set_cal_file(self, cal_file):
        if self.cal_file is None:
            self.cal_file = cal_file
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
        delete_ics_file(self.cal_file)
        self.date = None
        self.poll = None
        self.chat_id = None
        self.cal_file = None
        self.participants = []

    def add_participant(self, user_id):
        if self.date is not None:
            if user_id not in self.participants:
                self.participants.append(user_id)
            else:
                return 1
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
    def __init__(self, participants, game, category):
        self.running = True
        if game:  # expansion poll
            self.options = self.generate_options_exp(participants, game)
            if self.options is None:
                raise ValueError
        elif category:  # game poll by category
            self.options = self.generate_options_cat(participants, category)
            if self.options is None:
                raise ValueError
        else:  # simple game poll
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
        # create dictionary of categories
        config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        config_path = os.path.dirname(os.path.realpath(__file__))
        config.read(os.path.join(config_path, "config.ini"))
        categories_list = config.getlist('GameCategories', 'categories')  # no, this is no error. getlist is created by converter above
        categories_list.append('keine')
        categories = {categories_list[i]: i for i in range(len(categories_list))}  # {'groß' : 0, ...}

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
            categories_used = []  # record what kinds of games we already have
            i = 0
            # select one small game
            small_set = games_by_category[categories['klein']]
            if len(small_set) > 0:
                opt = small_set[randrange(len(small_set))]
                options.append(opt)
                categories_used.append(categories['klein'])
                i += 1

            # select one big game
            big_set = games_by_category[categories['groß']]
            if len(big_set) > 0:
                while i < 2:
                    opt = big_set[randrange(len(big_set))]
                    if opt not in options:
                        options.append(opt)
                        i += 1
                        categories_used.append(categories['groß'])
                        break  # make sure only one big game is added
                    elif len(big_set) == 1:
                        # big game is the small game already added - does this even make sense?
                        break

            # fill the rest of options up
            while i < no_opts:
                category = randrange(len(games_by_category))
                # already went through all categories
                if len(categories_used) == len(categories):
                    category_set = games_by_category[category]
                    if len(category_set) > 0:
                        opt = category_set[randrange(len(category_set))]
                        if opt not in options:
                            options.append(opt)
                            i += 1
                # try distributing categories as uniformly as possible
                elif category not in categories_used:
                    categories_used.append(category)
                    category_set = games_by_category[category]
                    if len(category_set) > 0:
                        opt = category_set[randrange(len(category_set))]
                        if opt not in options:
                            options.append(opt)
                            i += 1

        return options

    def generate_options_cat(self, participants, category):
        plan = GameNight()
        if plan:
            r = re.compile('.{2}/.{2}/.{4}')
            if r.match(plan.date) is not None:
                d = datetime.datetime.strptime(plan.date, '%d/%m/%Y')
        else: d = None

        games = set()
        for p in participants:
            entries = get_playable_entries_by_category(
                choose_database("testdb"), 'games', 'title', p, category,
                no_participants=len(participants), planned_date=d)
            for e in entries:
                games.add(single_db_entry_to_string(e))

        games = list(games)  # convert to list so we can index it randomly
        if len(games) == 0:  # no participant owns a game of this category
            return None
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
