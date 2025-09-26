import streamlit as st
import datetime
from io import BytesIO

# ✅ Try importing reportlab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Dummy movie posters (using URLs from the web)
MOVIES = {
    "Inception": "https://m.media-amazon.com/images/I/51zUbui+gbL._AC_.jpg",
    "Interstellar": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_SL1500_.jpg",
    "The Dark Knight": "https://m.media-amazon.com/images/I/51k0qa6qH-L._AC_.jpg",
    "Tenet": "https://m.media-amazon.com/images/I/71niXI3lxlL._AC_SL1024_.jpg"
}

# Seat options (A1–J10)
SEATS = [f"{row}{num}" for row in "ABCDEFGHIJ" for num in range(1, 11)]

# Session state
if "page" not in st.session_state:
    st.session_state.page = "movies"
if "ticket_data" not in st.session_state:
    st.session_state.ticket_data = {}

# Function to generate ticket PDF
def generate_ticket_pdf(ticket_info):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 50, "🎟 Movie Ticket 🎟")

    c.setFont("Helvetica", 12)
    y = height - 100
    for key, value in ticket_info.items():
        c.drawString(100, y, f"{key}: {value}")
        y -= 25

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

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

    if REPORTLAB_AVAILABLE:
        pdf_buffer = generate_ticket_pdf(st.session_state.ticket_data)
        st.download_button(
            label="⬇️ Download Ticket (PDF)",
            data=pdf_buffer,
            file_name="movie_ticket.pdf",
            mime="application/pdf"
        )
    else:
        st.error("⚠️ ReportLab is not installed. Please install it with `pip install reportlab` to enable PDF downloads.")
