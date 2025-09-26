import streamlit as st
import datetime

# ------------------------
# Movie Data
# ------------------------
MOVIES = {
    "Inception": "https://m.media-amazon.com/images/I/51zUbui+gbL._AC_.jpg",
    "Interstellar": "https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_SL1500_.jpg",
    "The Dark Knight": "https://m.media-amazon.com/images/I/51k0qa6qH-L._AC_.jpg",
    "Tenet": "https://m.media-amazon.com/images/I/71niXI3lxlL._AC_SL1024_.jpg"
}

SEATS = [f"{row}{num}" for row in "ABCDEFGHIJ" for num in range(1, 11)]

# ------------------------
# Session State
# ------------------------
if "page" not in st.session_state:
    st.session_state.page = "movies"
if "ticket_data" not in st.session_state:
    st.session_state.ticket_data = {}

# ------------------------
# Page 1: Movie Selection
# ------------------------
if st.session_state.page == "movies":
    st.title("🎬 Select Your Movie")
    cols = st.columns(len(MOVIES))
    for i, (movie, poster) in enumerate(MOVIES.items()):
        with cols[i]:
            st.image(poster, caption=movie, use_column_width=True)
            if st.button(f"Book {movie}"):
                st.session_state.ticket_data["Movie"] = movie
                st.session_state.page = "datetime"
                st.experimental_rerun()

# ------------------------
# Page 2: Date & Time
# ------------------------
elif st.session_state.page == "datetime":
    st.title("📅 Select Date & Time")
    date = st.date_input("Choose Date", datetime.date.today())
    time = st.time_input("Choose Time")
    if st.button("Next"):
        st.session_state.ticket_data["Date"] = str(date)
        st.session_state.ticket_data["Time"] = str(time)
        st.session_state.page = "tickets"
        st.experimental_rerun()

# ------------------------
# Page 3: Tickets & Seats
# ------------------------
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

# ------------------------
# Page 4: Payment
# ------------------------
elif st.session_state.page == "payment":
    st.title("💳 Payment Details")
    mode = st.selectbox("Payment Mode", ["Credit Card", "Debit Card", "UPI"])
    card_number = st.text_input("Card Number")
    exp_date = st.text_input("Expiry Date (MM/YY)")
    cvv = st.text_input("CVV", type="password")
    if st.button("Pay & Confirm Ticket"):
        if not card_number or len(card_number) < 4:
            st.error("Please enter a valid card number.")
        else:
            st.session_state.ticket_data["Payment Mode"] = mode
            st.session_state.ticket_data["Card Number"] = f"**** **** **** {card_number[-4:]}"
            st.session_state.page = "confirmation"
            st.experimental_rerun()

# ------------------------
# Page 5: Confirmation
# ------------------------
elif st.session_state.page == "confirmation":
    st.title("✅ Booking Confirmed")
    st.success("Your ticket has been booked successfully!")

    st.subheader("🎟 Ticket Details")
    for key, value in st.session_state.ticket_data.items():
        st.write(f"**{key}:** {value}")

    # Option to book another ticket
    if st.button("Book Another Ticket"):
        st.session_state.ticket_data = {}
        st.session_state.page = "movies"
        st.experimental_rerun()
