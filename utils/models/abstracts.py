# coding=utf-8
"""
Abstracts Models
"""
from abc import ABCMeta, abstractmethod


class AbstractModel(metaclass=ABCMeta):
    """ Class to abstract model. """

    @abstractmethod
    def save(self, commit=True):
        """
        Save in persistent media.
        :param commit: To commit transaction.
        :return: Self.
        """
        pass

    def _pop_attr(self, dct, name, obj):
        """ Retira atributo do dict. """
        dct.pop(name)
        dct[name] = obj.as_dict()
        return self

    def as_dict(self):
        """ Serialize to Json. """
        return self.__dict__
