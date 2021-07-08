# coding=utf-8
"""
Test Models
"""

import collections
import os

from models.elections import Election
from models.votes import Vote


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
    vote_date = vote_data[4]
    test = ['1', '14', '1477', 'DF', vote_date, '2021', 'PE', '1', '10', '116', '12000', '1']
    assert collections.Counter(vote_data) == collections.Counter(test)


def test_election_save():
    election = get_election(0)
    if os.path.isfile(election._filename):
        os.remove(election._filename)
    try:
        election.save()
    except:
        assert False
    else:
        assert True


def test_election_save_exists():
    election = get_election(1)
    try:
        election.save()
    except:
        assert False
    else:
        if os.path.isfile(election._filename):
            os.remove(election._filename)
        assert True
