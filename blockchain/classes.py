import hashlib
import json
from datetime import datetime


class Block:
    def __init__(self, index, timestamp, transactions, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data_string = json.dumps(self.transactions, sort_keys=True)
        return hashlib.sha256(f"{self.index}{self.timestamp}{data_string}{self.previous_hash}".encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []

    def create_genesis_block(self):
        return Block(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), [], "0")

    def add_block(self, transactions):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), transactions,
                          previous_block.hash)
        self.chain.append(new_block)

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        if len(self.pending_transactions) > 0:
            self.add_block(self.pending_transactions)
            self.pending_transactions = []

    def get_block_by_index(self, index):
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True


class VotingSystem:
    def __init__(self):
        self.blockchain = Blockchain()
        self.votes = {}

    def add_vote(self, voter_id, candidate_id):
        if voter_id not in self.votes:
            transaction = {
                "voter_id": voter_id,
                "candidate_id": candidate_id
            }
            self.blockchain.add_transaction(transaction)
            self.votes[voter_id] = candidate_id
            return True
        return False

    def tally_votes(self):
        self.blockchain.mine_pending_transactions()
        tally = {}
        for block in self.blockchain.chain:
            for transaction in block.transactions:
                candidate_id = transaction["candidate_id"]
                if candidate_id in tally:
                    tally[candidate_id] += 1
                else:
                    tally[candidate_id] = 1
        return tally

    def get_vote(self, voter_id):
        return self.votes.get(voter_id)

    def verify_vote(self, voter_id, candidate_id):
        vote = self.get_vote(voter_id)
        if vote == candidate_id:
            return True
        return False
