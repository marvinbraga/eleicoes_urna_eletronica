# coding=utf-8
"""
Test Models
"""

import collections

from models.elections import Election
from models.votes import Vote


def test_election_instance():
    election = Election(2021, 'PE', 1, 10, 116, 12000, 1)
    assert collections.Counter(election.data) == collections.Counter(['2021', 'PE', '1', '10', '116', '12000', '1'])


def test_vote_instance():
    election = Election(2021, 'PE', 1, 10, 116, 12000, 1)
    vote = Vote(1, 14, 1477, 'DF', election)
    vote_data = vote.data
    vote_date = vote_data[4]
    test = ['1', '14', '1477', 'DF', vote_date, '2021', 'PE', '1', '10', '116', '12000', '1']
    assert collections.Counter(vote_data) == collections.Counter(test)
