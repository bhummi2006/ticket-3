import streamlit as st
import hashlib
import json
import time
import uuid
from typing import List, Dict, Any

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_txs: List[Dict[str, Any]] = []
        self.tickets: Dict[str, int] = {}
        self.event_seat_index: Dict[str, str] = {}
        self.new_block(proof=100, previous_hash='1')

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.pending_txs.copy(),
            'proof': proof,
            'previous_hash': previous_hash or (self.hash(self.chain[-1]) if self.chain else '1')
        }

        for tx in block['transactions']:
            tid = tx.get('ticket_id')
            if tid:
                self.tickets[tid] = block['index']
                key = self._event_seat_key(tx['event_name'], tx.get('seat'))
                if key:
                    self.event_seat_index[key] = tid

        self.pending_txs = []
        self.chain.append(block)
        return block

    def new_transaction(self, buyer_name: str, buyer_email: str, event_name: str, seat: str = None, price: float = 0.0) -> Dict[str, Any]:
        if seat:
            key = self._event_seat_key(event_name, seat)
            if key in self.event_seat_index:
                raise ValueError(f"Seat {seat} for event '{event_name}' is already sold")

        raw = f"{buyer_name}|{buyer_email}|{event_name}|{seat}|{price}|{time.time()}|{uuid.uuid4()}"
        ticket_id = hashlib.sha256(raw.encode()).hexdigest()

        tx = {
            'buyer_name': buyer_name,
            'buyer_email': buyer_email,
            'event_name': event_name,
            'seat': seat,
            'price': price,
            'timestamp': time.time(),
            'ticket_id': ticket_id
        }

        self.pending_txs.append(tx)
        return tx

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while not self._valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def _valid_proof(last_proof: int, proof: int) -> bool:
        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def verify_ticket(self, ticket_id: str) -> Dict[str, Any]:
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

    def _event_seat_key(self, event_name: str, seat: str) -> str:
        if not seat:
            return ''
        return f"{event_name.lower()}::seat::{seat.lower()}"

    def get_chain(self) -> Dict[str, Any]:
        return {'length': len(self.chain), 'chain': self.chain}

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title='Blockchain Ticketing Demo', layout='wide')
st.title('🎟️ Blockchain-based Event Ticketing System (Demo)')

if 'blockchain' not in st.session_state:
    st.session_state['blockchain'] = Blockchain()

blockchain: Blockchain = st.session_state['blockchain']

col1, col2 = st.columns([2, 1])

with col1:
    st.header('Buy Ticket (Simulate Purchase)')
    with st.form('buy_ticket_form'):
        buyer_name = st.text_input('Buyer Name')
        buyer_email = st.text_input('Buyer Email')
        event_name = st.text_input('Event Name', value='Coldplay Live')
        event_date = st.date_input('Event Date')
        seat = st.text_input('Seat (optional)')
        price = st.number_input('Price (INR)', min_value=0.0, value=999.0)
        submitted = st.form_submit_button('Purchase Ticket')

        if submitted:
            try:
                tx = blockchain.new_transaction(
                    buyer_name=buyer_name or 'Anonymous',
                    buyer_email=buyer_email or 'anonymous@example.com',
                    event_name=f"{event_name} - {event_date.isoformat()}",
                    seat=seat or None,
                    price=float(price)
                )

                last_proof = blockchain.last_block['proof']
                with st.spinner('Mining block...'):
                    new_proof = blockchain.proof_of_work(last_proof)
                    blockchain.new_block(proof=new_proof)

                st.success('✅ Ticket purchased!')
                st.code(tx['ticket_id'])
                st.json(tx)

            except ValueError as e:
                st.error(str(e))

    st.markdown('---')
    st.header('Verify Ticket')
    ticket_input = st.text_input('Enter Ticket ID to verify')
    if st.button('Verify'):
        if not ticket_input.strip():
            st.warning('Please enter a Ticket ID.')
        else:
            result = blockchain.verify_ticket(ticket_input.strip())
            if result:
                st.success('✅ Valid ticket')
                st.json(result['transaction'])
                st.write(f"Block index: {result['block_index']}")
                st.write(f"Block hash: {result['block_hash']}")
                st.write(f"Recorded: {time.ctime(result['block_timestamp'])}")
            else:
                st.error('❌ Ticket not found or invalid')

with col2:
    st.header('Blockchain Ledger')
    info = blockchain.get_chain()
    st.metric('Blocks in chain', info['length'])

    rows = []
    for b in info['chain']:
        rows.append({
            'index': b['index'],
            'timestamp': time.ctime(b['timestamp']),
            'transactions': len(b['transactions']),
            'proof': b['proof'],
            'previous_hash': b['previous_hash'][:12] + '...' if b['previous_hash'] else ''
        })
    st.table(rows)

    st.markdown('Expand chain:')
    for b in info['chain']:
        with st.expander(f"Block {b['index']} - {time.ctime(b['timestamp'])}"):
            st.code(f"Block hash: {blockchain.hash(b)}")
            st.code(f"Previous hash: {b['previous_hash']}")
            st.write('Proof:', b['proof'])
            st.json(b['transactions'])

st.caption('Demo only. In real use, connect to distributed ledger and secure wallets.')

