# coding=utf-8
"""
Test Models
"""

import collections
import os

from models.elections import Election
from models.votes import Vote


def save_model(model):
    """ Save model """
    if os.path.isfile(model.__dict__.get('_filename')):
        os.remove(model.__dict__.get('_filename'))
    try:
        model.save()
    except Exception as e:
        print(e)
        assert False
    else:
        assert True


def get_election(index):
    """ Returns  """
    return [
        Election(2021, 'PE', 1, 10, 116, 12000, 1),
        Election(2021, 'AP', 2, 11, 117, 12000, 1),
        Election(2021, 'PE', 3, 12, 118, 12000, 1),
        Election(2021, 'PE', 4, 13, 119, 12000, 1),
    ][index]


def test_election_instance():
    election = get_election(0)
    assert collections.Counter(election.data) == collections.Counter(['2021', 'PE', '1', '10', '116', '12000', '1'])


def test_vote_instance():
    election = get_election(0)
    vote = Vote(1, 14, 1477, 'DF', election)
    vote_data = vote.data
    test = ['1', '14', '1477', 'DF', '2021', 'PE', '1', '10', '116', '12000', '1']
    assert collections.Counter(vote_data) == collections.Counter(test)


def test_election_save():
    election = get_election(0)
    save_model(election)


def test_election_save_exists():
    election = get_election(1)
    try:
        election.save()
    except Exception as e:
        print(e)
        assert False
    else:
        if os.path.isfile(election._filename):
            os.remove(election._filename)
        assert True
