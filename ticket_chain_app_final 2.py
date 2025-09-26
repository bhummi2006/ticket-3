import streamlit as st
import datetime
from io import BytesIO

# Dummy movie posters (URLs)
MOVIES = {
    "Inception": "https://m.media-amazon.com/images/I/51zUbui+gbL._AC_.jpg",
    "Interstellar": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_SL1500_.jpg",
    "The Dark Knight": "https://m.media-amazon.com/images/I/51k0qa6qH-L._AC_.jpg",
    "Tenet": "https://m.media-amazon.com/images/I/71niXI3lxlL._AC_SL1024_.jpg"
}

# Seats
SEATS = [f"{row}{num}" for row in "ABCDEFGHIJ" for num in range(1, 11)]

# Session state
if "page" not in st.session_state:
    st.session_state.page = "movies"
if "ticket_data" not in st.session_state:
    st.session_state.ticket_data = {}

# ✅ Styled PDF generator
def generate_ticket_pdf(ticket_info):
    lines = [
        "Movie Ticket",
        "------------------------",
    ]
    for key, value in ticket_info.items():
        lines.append(f"{key}: {value}")
    lines.append("------------------------")
    lines.append("Enjoy Your Show! 🍿")

    # PDF content stream
    content = "BT /F1 16 Tf 200 750 Td (🎟 YOUR MOVIE TICKET 🎟) Tj ET\n"
    y = 700
    for line in lines:
        content += f"BT /F1 12 Tf 100 {y} Td ({line}) Tj ET\n"
        y -= 25

    # Draw a rectangle box
    box = "100 690 400 200 re S\n"

    pdf_bytes = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] 
   /Contents 4 0 R 
   /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(content) + len(box)} >>
stream
{content}
{box}
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000120 00000 n 
0000000301 00000 n 
0000000400 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
480
%%EOF
"""
    return BytesIO(pdf_bytes.encode("latin-1"))

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

# Page 3: Tickets & Seats
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
        st.session_state.ticket_data["Card Number"] = (
            f"**** **** **** {card_number[-4:]}" if card_number else "N/A"
        )
        st.session_state.page = "confirmation"
        st.rerun()

# Page 5: Confirmation & Download
elif st.session_state.page == "confirmation":
    st.title("✅ Booking Confirmed")
    st.success("Your ticket has been booked successfully!")

    st.subheader("🎟 Ticket Details")
    for key, value in st.session_state.ticket_data.items():
        st.write(f"**{key}:** {value}")

    pdf_file = generate_ticket_pdf(st.session_state.ticket_data)
    st.download_button(
        label="⬇️ Download Ticket (PDF)",
        data=pdf_file,
        file_name="movie_ticket.pdf",
        mime="application/pdf"
    )
