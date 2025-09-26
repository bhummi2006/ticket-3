import streamlit as st
import hashlib
import json
import time
from collections import defaultdict

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_tickets = []
        self.new_block(proof=100, previous_hash="1")  # Genesis block
        self.ticket_prices = {}  # store ticket cost per event

    def new_block(self, proof, previous_hash=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "tickets": self.pending_tickets,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_tickets = []
        self.chain.append(block)
        return block

    def new_ticket(self, student_name, event_name, cost):
        ticket_id = hashlib.sha256(f"{student_name}{event_name}{time.time()}".encode()).hexdigest()[:10]
        ticket = {
            "ticket_id": ticket_id,
            "student": student_name,
            "event": event_name,
            "cost": cost,
            "timestamp": time.time(),
        }
        self.pending_tickets.append(ticket)
        # store cost for reference
        self.ticket_prices[event_name] = cost
        return ticket

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def last_block(self):
        return self.chain[-1]

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            prev_block = self.chain[i - 1]
            block = self.chain[i]
            if block["previous_hash"] != self.hash(prev_block):
                return False
        return True

    def verify_ticket(self, ticket_id):
         """Return ticket details if valid, otherwise empty dict."""
    idx = self.tickets.get(ticket_id)
    if not idx:
        return {}
    block = self.chain[idx - 1]
    for tx in block['transactions']:
        if tx.get('ticket_id') == ticket_id:
            return {
                'valid': True,
                'block_index': block['index'],
                'block_hash': self.hash(block),
                'transaction': tx,
                'block_timestamp': block['timestamp']
            }
    return {}
    
