# coding=utf-8

from singleton import Singleton


class QueryBuffer(Singleton):
    def init(self):
        # self.queries is a table of mid's we're waiting on, and the query
        # that has been collected so far
        # (used for neues_spiel and neue_erweiterung)
        self.queries = []

    def add(self, reply_to_id, query):
        if len(self.queries) >= 100:  # maybe 100 elements are too many?
            self.queries = self.queries[50:]
        self.queries.append([reply_to_id, query])

    def get_query(self, reply_to_id):
        for entry in self.queries:
            if entry[0] == reply_to_id:
                return entry[1]
        return None

    def clear_query(self, reply_to_id):
        for entry in self.queries:
            if entry[0] == reply_to_id:
                self.queries.remove(entry)

    def edit_query(self, reply_to_id, query):
        for entry in self.queries:
            if entry[0] == reply_to_id:
                entry[1] = query
