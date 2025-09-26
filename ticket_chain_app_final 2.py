import streamlit as st
import datetime
import segno
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader

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

# QR generator (returns BytesIO PNG buffer)
def generate_qr_code(data: dict) -> BytesIO:
    ticket_text = "\n".join([f"{k}: {v}" for k, v in data.items()])
    qr = segno.make(ticket_text)
    buf = BytesIO()
    qr.save(buf, kind="png", scale=6)  # scale controls resolution
    buf.seek(0)
    return buf

# PDF generator (returns BytesIO PDF buffer), embeds the QR image
def generate_pdf_receipt(ticket_data: dict, qr_buf: BytesIO) -> BytesIO:
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
        # wrap long strings moderately
        text = f"{key}: {value}"
        c.drawString(84, y, text)
        y -= 16
        # move to next column if we run low on space (simple approach)
        if y < 140:
            c.showPage()
            y = height - 72

    # Add QR image on the right / bottom
    try:
        qr_buf.seek(0)
        img = ImageReader(qr_buf)
        # place QR at lower-right-ish corner
        qr_size = 150  # pixels (reportlab units)
        c.drawImage(img, width - qr_size - 72, 72, width=qr_size, height=qr_size)
        # Label near QR
        c.setFont("Helvetica", 9)
        c.drawString(width - qr_size - 72, 72 + qr_size + 6, "Scan this QR at entry")
    except Exception as e:
        # if embedding fails, write a note
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(72, 120, f"[QR embed failed: {e}]")

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
        # Optional: You can compute total or cost fields here if desired
        st.session_state.page = "confirmation"
        st.experimental_rerun()

# Page 5: Confirmation & Downloads
elif st.session_state.page == "confirmation":
    st.title("✅ Booking Confirmed")
    st.success("Your ticket has been booked successfully!")

    st.subheader("🎟 Ticket Details")
    for key, value in st.session_state.ticket_data.items():
        st.write(f"**{key}:** {value}")

    # Generate QR
    qr_buf = generate_qr_code(st.session_state.ticket_data)
    st.image(qr_buf, caption="🎫 Scan this QR at Entry", use_column_width=False)

    # Download QR PNG
    qr_buf.seek(0)
    st.download_button(
        label="⬇️ Download QR Code (PNG)",
        data=qr_buf,
        file_name="ticket_qr.png",
        mime="image/png"
    )

    # Generate PDF receipt
    pdf_buf = generate_pdf_receipt(st.session_state.ticket_data, qr_buf)
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
