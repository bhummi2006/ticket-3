
import streamlit as st
import hashlib
import json
import time

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_tickets = []
        self.new_block(proof=100, previous_hash="1")  # Genesis block

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

    def new_ticket(self, student_name, event_name):
        ticket_id = hashlib.sha256(f"{student_name}{event_name}{time.time()}".encode()).hexdigest()[:10]
        ticket = {
            "ticket_id": ticket_id,
            "student": student_name,
            "event": event_name,
            "timestamp": time.time(),
        }
        self.pending_tickets.append(ticket)
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
        for block in self.chain:
            for ticket in block["tickets"]:
                if ticket["ticket_id"] == ticket_id:
                    return True, ticket, block
        return False, None, None


# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Blockchain Event Ticketing", layout="wide")
st.title("🎟️ Blockchain-based Event Ticketing System")

# Initialize blockchain in session
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

blockchain = st.session_state.blockchain

# Event list
events = ["Dandiya Night", "Painting", "Movie", "Carnival", "DJ Night"]

# --- Ticket Purchase ---
st.header("🎫 Buy a Ticket")
col1, col2 = st.columns(2)
with col1:
    student_name = st.text_input("Enter your name")
with col2:
    event_choice = st.selectbox("Select Event", events)

if st.button("Buy Ticket"):
    if student_name and event_choice:
        ticket = blockchain.new_ticket(student_name, event_choice)
        blockchain.new_block(proof=12345)
        st.success(f"✅ Ticket Purchased! ID: {ticket['ticket_id']}")
    else:
        st.warning("Please enter your name and select an event.")

# --- Ticket Verification ---
st.header("🔍 Verify a Ticket")
ticket_id_input = st.text_input("Enter Ticket ID to verify")

if st.button("Verify Ticket"):
    valid, ticket, block = blockchain.verify_ticket(ticket_id_input)
    if valid:
        st.success("🎉 Ticket is VALID!")
        st.json(ticket)
        st.write("Found in Block:")
        st.json(block)
    else:
        st.error("❌ Ticket not found or invalid.")

# --- Blockchain Explorer ---
st.header("⛓️ Blockchain Explorer")
for block in blockchain.chain:
    with st.expander(f"Block {block['index']} | Hash: {blockchain.hash(block)[:15]}..."):
        st.json(block)

# --- Chain Validity ---
st.sidebar.header("Blockchain Status")
if blockchain.is_chain_valid():
    st.sidebar.success("✅ Blockchain is valid")
else:
    st.sidebar.error("⚠️ Blockchain integrity compromised!")
