# coding=utf-8
"""
Candidate Models.
"""
from utils.models.abstracts import AbstractDictSerializer
from utils.models.bases import Model


class CandidateModelDictSerializer(AbstractDictSerializer):
    """ Classe para serializar um Model para Dict.  """

    def __init__(self, model):
        self._model = model

    def as_dict(self):
        """ Converte Model para Dict """
        result = self._model.__dict__.copy()
        return result


class Candidate(Model):
    """ Class Model to Candidates. """

    def __init__(self, code, name, part, photo):
        super().__init__(code, name, part, photo)
        self._photo = photo
        self._part = part
        self._name = name
        self._code = code

    def as_dict(self):
        """ Serialize to JSon. """
        return CandidateModelDictSerializer(self).as_dict()

    @property
    def data(self):
        """ Method for returning vote data. """
        return [str(self._code), str(self._name), str(self._part)]
