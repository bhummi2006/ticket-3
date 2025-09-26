import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.tickets: Dict[str, int] = {}  # ticket_id -> block index
        # Genesis block
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        for tx in self.pending_transactions:
            self.tickets[tx['ticket_id']] = block['index']
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, buyer: str, movie: str, date: str, time_slot: str,
                        seat_no: str, num_seats: int, payment_mode: str,
                        card_number: str, exp_date: str, cvv: str) -> str:
        ticket_id = hashlib.sha256(
            f"{buyer}{movie}{date}{time_slot}{seat_no}{num_seats}{payment_mode}{time.time()}".encode()
        ).hexdigest()

        self.pending_transactions.append({
            'buyer': buyer,
            'movie': movie,
            'date': date,
            'time_slot': time_slot,
            'seat_no': seat_no,
            'num_seats': num_seats,
            'payment_mode': payment_mode,
            'card_number': card_number[-4:],  # store only last 4 digits
            'exp_date': exp_date,
            'cvv': "***",  # never store real cvv
            'ticket_id': ticket_id,
            'timestamp': time.time()
        })
        return ticket_id

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

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

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="Blockchain Movie Ticketing", layout="centered")
st.title("🎬 Blockchain-based Movie Ticketing System")

if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()

if 'step' not in st.session_state:
    st.session_state.step = 1

# Step 1: Select Movie
if st.session_state.step == 1:
    st.subheader("Step 1: Select a Movie")
    movies = ["Inception", "Interstellar", "Avengers: Endgame", "The Dark Knight", "Titanic"]
    movie_choice = st.selectbox("Choose a movie:", movies)
    buyer_name = st.text_input("Enter your name:")
    if st.button("Next") and buyer_name and movie_choice:
        st.session_state.movie = movie_choice
        st.session_state.buyer = buyer_name
        st.session_state.step = 2
        st.rerun()

# Step 2: Date and Time
elif st.session_state.step == 2:
    st.subheader("Step 2: Select Date and Time")
    date = st.date_input("Select date:")
    time_slot = st.selectbox("Select showtime:", ["12:00 PM", "3:00 PM", "6:00 PM", "9:00 PM"])
    num_seats = st.number_input("Number of Seats:", min_value=1, max_value=10, step=1)
    if st.button("Next"):
        st.session_state.date = str(date)
        st.session_state.time_slot = time_slot
        st.session_state.num_seats = num_seats
        st.session_state.step = 3
        st.rerun()

# Step 3: Seat Selection
elif st.session_state.step == 3:
    st.subheader("Step 3: Choose Seats")
    seat_no = st.text_input("Enter seat numbers (e.g., A1,A2):")
    if st.button("Next") and seat_no:
        st.session_state.seat_no = seat_no
        st.session_state.step = 4
        st.rerun()

# Step 4: Payment
elif st.session_state.step == 4:
    st.subheader("Step 4: Payment")
    payment_mode = st.selectbox("Select Payment Mode:", ["Credit Card", "Debit Card"])
    card_number = st.text_input("Card Number:")
    exp_date = st.text_input("Expiry Date (MM/YY):")
    cvv = st.text_input("CVV:", type="password")

    if st.button("Pay & Confirm") and card_number and exp_date and cvv:
        blockchain: Blockchain = st.session_state.blockchain
        ticket_id = blockchain.new_transaction(
            buyer=st.session_state.buyer,
            movie=st.session_state.movie,
            date=st.session_state.date,
            time_slot=st.session_state.time_slot,
            seat_no=st.session_state.seat_no,
            num_seats=st.session_state.num_seats,
            payment_mode=payment_mode,
            card_number=card_number,
            exp_date=exp_date,
            cvv=cvv
        )
        blockchain.new_block(proof=123, previous_hash=blockchain.hash(blockchain.last_block()))
        st.session_state.ticket_id = ticket_id
        st.session_state.step = 5
        st.rerun()

# Step 5: Ticket Verification Slip
elif st.session_state.step == 5:
    st.success("✅ Payment Successful! Here is your ticket slip:")
    ticket_data = st.session_state.blockchain.verify_ticket(st.session_state.ticket_id)
    if ticket_data:
        tx = ticket_data['transaction']
        st.write(f"🎟 **Ticket ID:** {tx['ticket_id']}")
        st.write(f"👤 **Buyer:** {tx['buyer']}")
        st.write(f"🎬 **Movie:** {tx['movie']}")
        st.write(f"📅 **Date:** {tx['date']}")
        st.write(f"🕒 **Time:** {tx['time_slot']}")
        st.write(f"💺 **Seats:** {tx['seat_no']} (x{tx['num_seats']})")
        st.write(f"💳 **Payment Mode:** {tx['payment_mode']} (Card ****{tx['card_number']})")
    if st.button("Book Another Ticket"):
        st.session_state.step = 1
        st.rerun()
