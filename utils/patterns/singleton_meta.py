# coding=utf-8
"""
Singleton Pattern Module.
Marcus Vinicius Braga, 2021.
"""


class Singleton(type):
    """ Singleton Pattern. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
