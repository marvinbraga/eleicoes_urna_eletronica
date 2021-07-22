# coding=utf-8
"""
Votes Model Module.
"""
from datetime import datetime

from utils.models.abstracts import AbstractDictSerializer
from utils.models.bases import Model


class VoteModelDictSerializer(AbstractDictSerializer):
    """ Classe para serializar um Model para Dict.  """

    def __init__(self, model):
        self._model = model

    def as_dict(self):
        """ Converte Model para Dict """
        result = self._model.__dict__.copy()
        result.pop('_election')
        result.pop('_date_time')
        return result


class Vote(Model):
    """ Class for vote information. """

    def __init__(self, conf_id, party_number, candidate_number, candidate_type_code, election):
        super().__init__(conf_id, party_number, candidate_number, candidate_type_code, election)
        self._conf_id = conf_id
        self._party_number = party_number
        self._candidate_number = candidate_number
        self._candidate_type_code = candidate_type_code
        self._date_time = datetime.now()
        self._election = election
        self._hash = None

    def as_dict(self):
        """ Serialize to JSon. """
        return VoteModelDictSerializer(self).as_dict()

    def set_hash(self, value):
        """ Save the hash value """
        self._hash = value
        return self

    @property
    def data(self):
        """ Method for returning vote data. """
        return [str(self._conf_id), str(self._party_number), str(self._candidate_number),
                str(self._candidate_type_code), str(self._hash), *self._election.data]
