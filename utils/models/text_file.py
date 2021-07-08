# coding=utf-8
"""
Model Text File Module.
"""
import json
import os

from utils.models.abstracts import AbstractModel


class TextFileModel(AbstractModel):
    """ Persistence in Text File """

    def __init__(self, *args, **kwargs):
        filename = kwargs.get('filename')
        self._filename = filename if filename else f'{self.__class__.__name__}_model.json'
        self._args = args
        self._kwargs = kwargs

    def _load_from_file(self):
        """ Load from persistence file. """
        result = None
        if os.path.isfile(self._filename):
            with open(self._filename, 'r', encoding='utf-8') as f:
                try:
                    data = f.readlines()
                    print(type(data), data)
                finally:
                    f.close()
                result = json.loads(''.join(data))
        return result

    def save(self, commit=True):
        """ Save in Text File. """
        data = self._load_from_file()
        if data:
            data.append(self.__dict__)
        else:
            data = [self.__dict__]
        with open(self._filename, 'w', encoding='utf-8') as f:
            try:
                if commit:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            finally:
                f.close()
        return self
