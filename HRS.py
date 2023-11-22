import streamlit as st
import sqlite3
import pandas as pd

# Initialize SQLite database
conn = sqlite3.connect("hotel_database.db", check_same_thread=False)
cursor = conn.cursor()

# Create the rooms table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        room_number INTEGER PRIMARY KEY,
        capacity INTEGER,
        is_reserved INTEGER
    )
''')
conn.commit()

# Create the reservations table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number INTEGER,
        guest_name TEXT,
        contact_number TEXT,
        check_in_date DATE,
        check_out_date DATE,
        FOREIGN KEY (room_number) REFERENCES rooms (room_number)
    )
''')
conn.commit()

class Room:
    def __init__(self, room_number, capacity):
        self.room_number = room_number
        self.capacity = capacity
        self.is_reserved = False


def add_room(room_number, capacity):
    cursor.execute("INSERT INTO rooms (room_number, capacity, is_reserved) VALUES (?, ?, 0)", (room_number, capacity))
    conn.commit()


def display_available_rooms():
    cursor.execute("SELECT * FROM rooms WHERE is_reserved = 0")
    return [Room(room_number, capacity) for room_number, capacity, is_reserved in cursor.fetchall()]


def make_reservation(room_number, guest_name, contact_number, check_in_date, check_out_date):
    # Convert check_in_date and check_out_date to strings in ISO 8601 format
    check_in_date_str = check_in_date.strftime("%Y-%m-%d")
    check_out_date_str = check_out_date.strftime("%Y-%m-%d")

    cursor.execute("UPDATE rooms SET is_reserved = 1 WHERE room_number = ?", (room_number,))
    cursor.execute("INSERT INTO reservations (room_number, guest_name, contact_number, check_in_date, check_out_date) VALUES (?, ?, ?, ?, ?)",
                   (room_number, guest_name, contact_number, check_in_date_str, check_out_date_str))
    conn.commit()

    return f"Reservation successful for Room {room_number}. Guest: {guest_name}, Contact Number: {contact_number}, Check-in Date: {check_in_date_str}, Check-out Date: {check_out_date_str}."


def cancel_reservation(reservation_id):
    cursor.execute("SELECT room_number FROM reservations WHERE reservation_id = ?", (reservation_id,))
    room_number = cursor.fetchone()[0]

    cursor.execute("UPDATE rooms SET is_reserved = 0 WHERE room_number = ?", (room_number,))

    cursor.execute("DELETE FROM reservations WHERE reservation_id = ?", (reservation_id,))

    conn.commit()
    return f"Reservation canceled for Room {room_number}."


def view_reservations():
    cursor.execute("SELECT * FROM reservations")
    reservations_data = cursor.fetchall()
    if not reservations_data:
        st.warning("No reservations found.")
    else:
        columns = ["Reservation ID", "Room Number", "Guest Name", "Contact Number", "Check-in Date", "Check-out Date"]
        df = pd.DataFrame(reservations_data, columns=columns)
        st.dataframe(df)


def main():
    st.title("Hotel Reservation System")

    menu = ["Home", "Booked Reservations"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Home":
        display_home_page()
    elif choice == "Booked Reservations":
        view_reservations()


def display_home_page():
    st.subheader("Available Rooms:")
    available_rooms = display_available_rooms()
    for room in available_rooms:
        st.write(f"Room {room.room_number} - Capacity: {room.capacity}")

    st.subheader("Make a Reservation:")
    room_number_make = st.number_input("Enter the room number to make a reservation:", min_value=1, step=1)
    guest_name = st.text_input("Enter your name:")
    contact_number = st.text_input("Enter your contact number:")
    check_in_date = st.date_input("Select check-in date:", format="YYYY-MM-DD")  # Explicitly set the format
    check_out_date = st.date_input("Select check-out date:", format="YYYY-MM-DD")  # Explicitly set the format

    if st.button("Make Reservation"):
        result_make = make_reservation(room_number_make, guest_name, contact_number, check_in_date, check_out_date)
        st.success(result_make)

    st.subheader("Cancel a Reservation:")
    # Display reservations for cancellation
    cursor.execute("SELECT * FROM reservations")
    reservations_data = cursor.fetchall()
    if reservations_data:
        reservations = {f"{reservation[0]} - Room {reservation[1]} - {reservation[2]}": reservation[0] for reservation in reservations_data}
        selected_reservation = st.selectbox("Select reservation to cancel:", list(reservations.keys()), index=0)
        reservation_id_to_cancel = reservations[selected_reservation]

        if st.button("Cancel Reservation"):
            result_cancel = cancel_reservation(reservation_id_to_cancel)
            st.success(result_cancel)
    else:
        st.warning("No reservations available for cancellation.")


if __name__ == '__main__':
    main()

