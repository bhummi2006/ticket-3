import streamlit as st
import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

# Dummy movie posters
MOVIES = {
    "Inception": "https://m.media-amazon.com/images/I/51zUbui+gbL._AC_.jpg",
    "Interstellar": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_SL1500_.jpg",
    "The Dark Knight": "https://m.media-amazon.com/images/I/51k0qa6qH-L._AC_.jpg",
    "Tenet": "https://m.media-amazon.com/images/I/71niXI3lxlL._AC_SL1024_.jpg"
}

# Seats
SEATS = [f"{row}{num}" for row in "ABCDEFGHIJ" for num in range(1, 11)]

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = "movies"
if "ticket_data" not in st.session_state:
    st.session_state.ticket_data = {}

# PDF generator (returns BytesIO PDF buffer)
def generate_pdf_receipt(ticket_data: dict) -> BytesIO:
    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=LETTER)
    width, height = LETTER

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, height - 72, "Ticket Verification Receipt")

    # Subheader / metadata
    c.setFont("Helvetica", 10)
    c.drawString(72, height - 96, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Ticket details
    y = height - 140
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Ticket Details:")
    y -= 18
    c.setFont("Helvetica", 11)
    for key, value in ticket_data.items():
        text = f"{key}: {value}"
        c.drawString(84, y, text)
        y -= 16
        if y < 140:
            c.showPage()
            y = height - 72

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(72, 48, "Thank you for booking. Please carry a printed or digital copy of this receipt.")
    c.save()

    pdf_buf.seek(0)
    return pdf_buf

# -----------------------
# Streamlit pages
# -----------------------

# Page 1: Movie Selection
if st.session_state.page == "movies":
    st.title("🎬 Select Your Movie")
    cols = st.columns(len(MOVIES))
    for i, (movie, poster) in enumerate(MOVIES.items()):
        with cols[i]:
            st.image(poster, caption=movie, use_column_width=True)
            if st.button(f"Book {movie}"):
                st.session_state.ticket_data = {}  # reset for new booking
                st.session_state.ticket_data["Movie"] = movie
                st.session_state.page = "datetime"
                st.experimental_rerun()

# Page 2: Date & Time
elif st.session_state.page == "datetime":
    st.title("📅 Select Date & Time")
    date = st.date_input("Choose Date", datetime.date.today())
    time = st.time_input("Choose Time")
    if st.button("Next"):
        st.session_state.ticket_data["Date"] = str(date)
        st.session_state.ticket_data["Time"] = str(time)
        st.session_state.page = "tickets"
        st.experimental_rerun()

# Page 3: Tickets & Seats
elif st.session_state.page == "tickets":
    st.title("🎟 Select Tickets & Seats")
    num_tickets = st.number_input("Number of Tickets", min_value=1, max_value=5, step=1)
    seats = st.multiselect("Choose Seats", SEATS, default=SEATS[:num_tickets])
    if st.button("Next"):
        if len(seats) != num_tickets:
            st.error("Please select the same number of seats as tickets.")
        else:
            st.session_state.ticket_data["Tickets"] = num_tickets
            st.session_state.ticket_data["Seats"] = ", ".join(seats)
            st.session_state.page = "payment"
            st.experimental_rerun()

# Page 4: Payment
elif st.session_state.page == "payment":
    st.title("💳 Payment Details")
    mode = st.selectbox("Payment Mode", ["Credit Card", "Debit Card", "UPI"])
    card_number = st.text_input("Card Number (numbers only)")
    exp_date = st.text_input("Expiry Date (MM/YY)")
    cvv = st.text_input("CVV", type="password")

    if st.button("Pay & Generate Ticket"):
        # Basic validations
        if mode in ("Credit Card", "Debit Card"):
            if not card_number or not card_number.isdigit() or len(card_number) < 12:
                st.error("Please enter a valid card number (digits only, min 12 digits).")
                st.stop()
            if not exp_date:
                st.error("Please enter expiry date.")
                st.stop()
            # mask card for storage/display
            masked = f"**** **** **** {card_number[-4:]}"
        else:
            masked = "UPI"

        st.session_state.ticket_data["Payment Mode"] = mode
        st.session_state.ticket_data["Card Number"] = masked
        st.session_state.page = "confirmation"
        st.experimental_rerun()

# Page 5: Confirmation & PDF Download
elif st.session_state.page == "confirmation":
    st.title("✅ Booking Confirmed")
    st.success("Your ticket has been booked successfully!")

    st.subheader("🎟 Ticket Details")
    for key, value in st.session_state.ticket_data.items():
        st.write(f"**{key}:** {value}")

    # Generate PDF receipt
    pdf_buf = generate_pdf_receipt(st.session_state.ticket_data)
    pdf_buf.seek(0)
    st.download_button(
        label="⬇️ Download Verification Receipt (PDF)",
        data=pdf_buf,
        file_name="ticket_receipt.pdf",
        mime="application/pdf"
    )

    # Option to book another ticket
    if st.button("Book Another Ticket"):
        st.session_state.page = "movies"
        st.session_state.ticket_data = {}
        st.experimental_rerun()
