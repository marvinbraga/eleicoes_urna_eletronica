# coding=utf-8
"""
Vote Controller
Marcus Vinicius Braga, 2021.
"""
from abc import ABCMeta, abstractmethod


class AbstractController(metaclass=ABCMeta):
    """ Abstract class to controller. """

    @abstractmethod
    def execute(self):
        """ Strategy pattern to controller class. """
        pass
