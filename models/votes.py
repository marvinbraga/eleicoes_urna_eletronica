# coding=utf-8
"""
Votes Model Module.
"""
from datetime import datetime

from utils.models.bases import Model


class Vote(Model):
    """ Class for vote information. """

    def __init__(self, order, party_number, candidate_number, candidate_type_code, election):
        super().__init__(order, party_number, candidate_number, candidate_type_code, election)
        self._order = order
        self._party_number = party_number
        self._candidate_number = candidate_number
        self._candidate_type_code = candidate_type_code
        self._date_time = datetime.now()
        self._election = election

    @property
    def data(self):
        """ Method for returning vote data. """
        return [str(self._order), str(self._party_number), str(self._candidate_number),
                str(self._candidate_type_code), str(self._date_time), *self._election.data]
