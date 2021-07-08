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
