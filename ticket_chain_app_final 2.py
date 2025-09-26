import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any
import requests
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import base64

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_transactions: List[Dict[str, Any]] = []
        self.tickets: Dict[str, int] = {}
        self.booked_seats: set = set()
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
            for s in tx['seat_no']:
                self.booked_seats.add(s)
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, buyer: str, movie: str, date: str, time_slot: str,
                        seat_no: List[str], num_seats: int, payment_mode: str,
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
            'card_number': card_number[-4:],
            'exp_date': exp_date,
            'cvv': "***",
            'ticket_id': ticket_id,
            'timestamp': time.time()
        })
        return ticket_id

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

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
# Helper: load image from URL
# -----------------------
def load_image_from_url(url: str):
    try:
        resp = requests.get(url)
        img = Image.open(BytesIO(resp.content))
        return img
    except Exception:
        return None

# -----------------------
# Generate PDF Ticket
# -----------------------
def generate_ticket_pdf(ticket_data: Dict[str, Any]) -> bytes:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 50, "🎟 Blockchain Movie Ticket")

    c.setFont("Helvetica", 14)
    tx = ticket_data['transaction']
    details = [
        f"Ticket ID: {tx['ticket_id']}",
        f"Buyer: {tx['buyer']}",
        f"Movie: {tx['movie']}",
        f"Date: {tx['date']}",
        f"Time: {tx['time_slot']}",
        f"Seats: {', '.join(tx['seat_no'])} (x{tx['num_seats']})",
        f"Payment Mode: {tx['payment_mode']} (****{tx['card_number']})",
    ]

    y = height - 120
    for line in details:
        c.drawString(100, y, line)
        y -= 30

    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(width / 2, 100, "Thank you for booking with Blockchain Ticketing System")

    c.save()
    pdf_data = open(temp_file.name, "rb").read()
    return pdf_data

# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="Blockchain Movie Ticketing", layout="wide")
st.title("🎬 Blockchain-based Movie Ticketing System")

if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()
if 'step' not in st.session_state:
    st.session_state.step = 1

# Dummy posters
MOVIE_POSTERS = {
    "Inception": "https://via.placeholder.com/600x400.png?text=Inception",
    "Interstellar": "https://via.placeholder.com/600x400.png?text=Interstellar",
    "Avengers: Endgame": "https://via.placeholder.com/600x400.png?text=Avengers+Endgame",
    "The Dark Knight": "https://via.placeholder.com/600x400.png?text=The+Dark+Knight"
}

# Step 1: Movie Selection
if st.session_state.step == 1:
    st.subheader("Step 1: Select a Movie")
    movie_choice = st.selectbox("Choose a movie:", list(MOVIE_POSTERS.keys()))
    buyer_name = st.text_input("Enter your name:")

    img = load_image_from_url(MOVIE_POSTERS[movie_choice])
    if img:
        st.image(img, use_column_width=True)

    if st.button("Next") and buyer_name:
        st.session_state.movie = movie_choice
        st.session_state.buyer = buyer_name
        st.session_state.step = 2
        st.rerun()

# Step 2: Date & Time
elif st.session_state.step == 2:
    st.subheader("Step 2: Select Date & Time")
    date = st.date_input("Select date:")
    time_slot = st.selectbox("Select showtime:", ["12:00 PM", "3:00 PM", "6:00 PM", "9:00 PM"])
    if st.button("Next"):
        st.session_state.date = str(date)
        st.session_state.time_slot = time_slot
        st.session_state.step = 3
        st.rerun()

# Step 3: Seat Selection
elif st.session_state.step == 3:
    st.subheader("Step 3: Select Seats")
    rows = ["A","B","C","D","E","F","G","H"]
    cols = list(range(1, 11))
    all_seats = [f"{r}{c}" for r in rows for c in cols]
    available = [s for s in all_seats if s not in st.session_state.blockchain.booked_seats]

    if not available:
        st.error("No seats available")
    else:
        num_seats = st.selectbox("How many seats?", list(range(1, min(6, len(available)) + 1)))
        selected_seats = []
        for i in range(num_seats):
            sel = st.selectbox(f"Seat #{i+1}", ["--Select--"] + available, key=f"seat_sel_{i}")
            selected_seats.append(sel)

        if st.button("Next") and all([s != "--Select--" for s in selected_seats]):
            st.session_state.seat_no = selected_seats
            st.session_state.num_seats = num_seats
            st.session_state.step = 4
            st.rerun()

# Step 4: Payment
elif st.session_state.step == 4:
    st.subheader("Step 4: Payment")
    payment_mode = st.selectbox("Select Payment Mode:", ["Credit Card", "Debit Card", "UPI"])
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

# Step 5: Ticket Slip + PDF Download
elif st.session_state.step == 5:
    st.success("✅ Payment Successful! Here’s your ticket slip:")
    ticket_data = st.session_state.blockchain.verify_ticket(st.session_state.ticket_id)
    if ticket_data:
        tx = ticket_data['transaction']
        st.write(f"🎟 **Ticket ID:** {tx['ticket_id']}")
        st.write(f"👤 **Buyer:** {tx['buyer']}")
        st.write(f"🎬 **Movie:** {tx['movie']}")
        st.write(f"📅 **Date:** {tx['date']}")
        st.write(f"🕒 **Time:** {tx['time_slot']}")
        st.write(f"💺 **Seats:** {', '.join(tx['seat_no'])} (x{tx['num_seats']})")
        st.write(f"💳 **Payment Mode:** {tx['payment_mode']} (Card ****{tx['card_number']})")

        # Generate PDF
        pdf_data = generate_ticket_pdf(ticket_data)
        b64_pdf = base64.b64encode(pdf_data).decode("utf-8")
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="ticket.pdf">📥 Download Ticket (PDF)</a>'
        st.markdown(href, unsafe_allow_html=True)

    if st.button("Book Another"):
        st.session_state.step = 1
        st.rerun()
