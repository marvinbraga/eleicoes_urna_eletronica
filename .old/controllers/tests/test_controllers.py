# coding=utf-8
"""
Test Controllers
"""
import random

from old.controllers.ballot_boxes import BallotBoxesController
from models.ballot_boxes import BallotBoxModel
from models.tests.test_models import get_election, save_model
from models.votes import Vote
from utils.blockchain.hash import ConferenceIdGen
from utils.blockchain.manager import BlockchainManager


def test_ballot_box_add_vote():
    """
    Teste que cria 20 votos e utiliza o controlador de urna com segurança de block chain.
    Salva arquivo com informações da urna (controlador de urna).
    Salva arquivo de votos (controlador de urna).
    :return:
    """
    election = get_election(0)
    votes = [Vote(
        ConferenceIdGen(i + 1).execute(), random.randint(1, 34), random.randint(1, 7), 1, election
    ) for i in range(0, 20)]
    ballot_box = BallotBoxModel(99, election, [])
    controller = BallotBoxesController(ballot_box, blockchain=BlockchainManager())
    for vote in votes:
        controller.add_vote(vote)
    controller.execute()
    save_model(ballot_box)
