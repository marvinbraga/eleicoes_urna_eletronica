# coding=utf-8
"""
Elections Model Module.
"""
from utils.models.bases import Model


class Election(Model):
    """ Class for election information. """

    def __init__(self, election_code, state, city, zone, section, polling_place, ballot_box_type_code):
        super().__init__(election_code, state, city, zone, section, polling_place, ballot_box_type_code)
        self._election_code = election_code
        self._state = state
        self._city = city
        self._zone = zone
        self._section = section
        self._polling_place = polling_place
        self._ballot_box_type_code = ballot_box_type_code

    @property
    def data(self):
        """ Method for returning vote data. """
        return [str(self._election_code), str(self._state), str(self._city), str(self._zone), str(self._section),
                str(self._polling_place), str(self._ballot_box_type_code)]
