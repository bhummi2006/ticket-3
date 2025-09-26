import streamlit as st
from fpdf import FPDF
import datetime

# Dummy movie posters (using URLs from the web)
MOVIES = {
    "Inception": "https://m.media-amazon.com/images/I/51zUbui+gbL._AC_.jpg",
    "Interstellar": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_SL1500_.jpg",
    "The Dark Knight": "https://m.media-amazon.com/images/I/51k0qa6qH-L._AC_.jpg",
    "Tenet": "https://m.media-amazon.com/images/I/71niXI3lxlL._AC_SL1024_.jpg"
}

# Seat options (simple dropdown for demo)
SEATS = [f"{row}{num}" for row in "ABCDEFGHIJ" for num in range(1, 11)]

# Session state
if "page" not in st.session_state:
    st.session_state.page = "movies"
if "ticket_data" not in st.session_state:
    st.session_state.ticket_data = {}

# PDF Generator
def generate_ticket_pdf(ticket_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="🎟 Movie Ticket", ln=True, align="C")

    pdf.set_font("Arial", size=12)
    for key, value in ticket_info.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True, align="L")

    filename = "movie_ticket.pdf"
    pdf.output(filename)
    return filename

# Page 1: Movie selection
if st.session_state.page == "movies":
    st.title("🎬 Select Your Movie")
    cols = st.columns(len(MOVIES))
    for i, (movie, poster) in enumerate(MOVIES.items()):
        with cols[i]:
            st.image(poster, caption=movie, use_column_width=True)
            if st.button(f"Book {movie}"):
                st.session_state.ticket_data["Movie"] = movie
                st.session_state.page = "datetime"
                st.rerun()

# Page 2: Date & Time
elif st.session_state.page == "datetime":
    st.title("📅 Select Date & Time")
    date = st.date_input("Choose Date", datetime.date.today())
    time = st.time_input("Choose Time")
    if st.button("Next"):
        st.session_state.ticket_data["Date"] = str(date)
        st.session_state.ticket_data["Time"] = str(time)
        st.session_state.page = "tickets"
        st.rerun()

# Page 3: Number of Tickets & Seats
elif st.session_state.page == "tickets":
    st.title("🎟 Select Tickets & Seats")
    num_tickets = st.number_input("Number of Tickets", min_value=1, max_value=5, step=1)
    seats = st.multiselect("Choose Seats", SEATS, default=SEATS[:num_tickets])

    if st.button("Next"):
        st.session_state.ticket_data["Tickets"] = num_tickets
        st.session_state.ticket_data["Seats"] = ", ".join(seats)
        st.session_state.page = "payment"
        st.rerun()

# Page 4: Payment
elif st.session_state.page == "payment":
    st.title("💳 Payment Details")
    mode = st.selectbox("Payment Mode", ["Credit Card", "Debit Card", "UPI"])
    card_number = st.text_input("Card Number")
    exp_date = st.text_input("Expiry Date (MM/YY)")
    cvv = st.text_input("CVV", type="password")

    if st.button("Pay & Generate Ticket"):
        st.session_state.ticket_data["Payment Mode"] = mode
        st.session_state.ticket_data["Card Number"] = f"**** **** **** {card_number[-4:]}" if card_number else "N/A"
        st.session_state.page = "confirmation"
        st.rerun()

# Page 5: Confirmation & PDF Download
elif st.session_state.page == "confirmation":
    st.title("✅ Booking Confirmed")
    st.success("Your ticket has been booked successfully!")

    st.subheader("🎟 Ticket Details")
    for key, value in st.session_state.ticket_data.items():
        st.write(f"**{key}:** {value}")

    # Generate PDF
    filename = generate_ticket_pdf(st.session_state.ticket_data)
    with open(filename, "rb") as f:
        st.download_button("⬇️ Download Ticket (PDF)", f, file_name=filename, mime="application/pdf")
