import streamlit as st
import sqlite3
import pandas as pd
import os

conn = sqlite3.connect("hotel_database.db", check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        room_number INTEGER PRIMARY KEY,
        capacity INTEGER,
        is_reserved INTEGER
    )
''')
conn.commit()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number INTEGER,
        guest_name TEXT,
        contact_number TEXT,
        check_in_date DATE,
        check_out_date DATE,
        num_people INTEGER,
        room_image TEXT,
        room_type TEXT, -- New column for room type
        price REAL, -- New column for price
        FOREIGN KEY (room_number) REFERENCES rooms (room_number)
    )
''')
conn.commit()


class Room:
    def __init__(self, room_number, capacity, is_reserved=False):
        self.room_number = room_number
        self.capacity = capacity
        self.is_reserved = is_reserved


def add_room(room_number, capacity):
    cursor.execute("INSERT INTO rooms (room_number, capacity, is_reserved) VALUES (?, ?, 0)", (room_number, capacity))
    conn.commit()


def display_available_rooms():
    cursor.execute("SELECT * FROM rooms WHERE is_reserved = 0")
    return [Room(room_number, capacity, is_reserved) for room_number, capacity, is_reserved in cursor.fetchall()]


def make_reservation(room_number, guest_name, contact_number, check_in_date, check_out_date, num_people, room_tier):
    check_in_date_str = check_in_date.strftime("%Y-%m-%d")
    check_out_date_str = check_out_date.strftime("%Y-%m-%d")

    price = calculate_price(room_tier, check_in_date, check_out_date)

    image_directory = './room_images/'
    room_image = None

    if room_tier == "Single Room":
        room_image = 'single_room.png'
    elif room_tier == "Suite":
        room_image = 'suite.png'
    elif room_tier == "Deluxe Suite":
        room_image = 'deluxe_suite.png'

    if room_image is not None:
        cursor.execute("UPDATE rooms SET is_reserved = 1 WHERE room_number = ?", (room_number,))
        cursor.execute("INSERT INTO reservations (room_number, guest_name, contact_number, check_in_date, check_out_date, num_people, room_image, room_type, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (room_number, guest_name, contact_number, check_in_date_str, check_out_date_str, num_people, room_image, room_tier, price))
        conn.commit()

        return f"Reservation successful for Room {room_number}. Guest: {guest_name}, Contact Number: {contact_number}, Check-in Date: {check_in_date_str}, Check-out Date: {check_out_date_str}, Number of People: {num_people}, Room Type: {room_tier}, Price: {price}."
    else:
        return "Invalid room type selected. Reservation not made."



def calculate_price(room_tier, check_in_date, check_out_date):
    
    base_prices = {
        "Single Room": 5000,
        "Suite": 6000,
        "Deluxe Suite": 7000
    }

    num_days = max((check_out_date - check_in_date).days, 1) 

    if room_tier in base_prices:
        price_per_day = base_prices[room_tier]
        total_price = price_per_day * num_days
        return total_price
    else:
        return None 

    return f"Reservation successful for Room {room_number}. Guest: {guest_name}, Contact Number: {contact_number}, Check-in Date: {check_in_date_str}, Check-out Date: {check_out_date_str}, Number of People: {num_people}."

def display_home_page():
    st.subheader("Book a reservation:")
    available_rooms = display_available_rooms()
    for room in available_rooms:
        st.write(f"Room {room.room_number} - Capacity: {room.capacity}")


    room_tiers = ["Single Room", "Suite", "Deluxe Suite"]
    room_tier_make = st.selectbox("Select room tier:", room_tiers)
   
    room_number_make = st.number_input("Enter the room number to make a reservation:", min_value=1, step=1)
    guest_name = st.text_input("Enter your name:")
    contact_number = st.text_input("Enter your contact number:")
    check_in_date = st.date_input("Select check-in date:", format="YYYY-MM-DD")  
    check_out_date = st.date_input("Select check-out date:", format="YYYY-MM-DD")
    num_people = st.number_input("Enter the number of people:", min_value=1, step=1)


    if st.button("Make Reservation"):
        result_make = make_reservation(room_number_make, guest_name, contact_number, check_in_date, check_out_date, num_people, room_tier_make)
        st.success(result_make)


def cancel_reservation(reservation_id):
    cursor.execute("SELECT room_number FROM reservations WHERE reservation_id = ?", (reservation_id,))
    room_number = cursor.fetchone()[0]


    cursor.execute("UPDATE rooms SET is_reserved = 0 WHERE room_number = ?", (room_number,))


    cursor.execute("DELETE FROM reservations WHERE reservation_id = ?", (reservation_id,))


    conn.commit()
    return f"Reservation canceled for Room {room_number}."


def view_reservations():
    cursor.execute("SELECT reservation_id, room_number, guest_name, contact_number, check_in_date, check_out_date, num_people, room_type, price FROM reservations")
    reservations_data = cursor.fetchall()

    if not reservations_data:
        st.warning("No reservations found.")
    else:
        columns = ["Reservation ID", "Room Number", "Guest Name", "Contact Number", "Check-in Date", "Check-out Date", "Number of People", "Room Type", "Price"]
        df = pd.DataFrame(reservations_data, columns=columns)

        image_directory = './room_images/'

        col1, col2 = st.columns([1, 2])

        with col1:
            for index, row in df.iterrows():
                room_type = row['Room Type']
                image_path = None

                if room_type == "Single Room":
                    image_path = os.path.join(image_directory, 'single_room.png')
                elif room_type == "Suite":
                    image_path = os.path.join(image_directory, 'suite.png')
                elif room_type == "Deluxe Suite":
                    image_path = os.path.join(image_directory, 'deluxe_suite.png')

                if image_path and os.path.exists(image_path):
                    st.image(image_path, caption=f"Reservation ID: {row['Reservation ID']}", use_column_width=True)
                else:
                    st.write(f"No image available for Reservation ID: {row['Reservation ID']}")

        with col2:
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


    room_tiers = ["Single Room", "Suite", "Deluxe Suite"]
    room_tier_make = st.selectbox("Select room tier:", room_tiers)
   
    room_number_make = st.number_input("Enter the room number to make a reservation:", min_value=1, step=1)
    guest_name = st.text_input("Enter your name:")
    contact_number = st.text_input("Enter your contact number:")
    check_in_date = st.date_input("Select check-in date:", format="YYYY-MM-DD")  
    check_out_date = st.date_input("Select check-out date:", format="YYYY-MM-DD")
    num_people = st.number_input("Enter the number of people:", min_value=1, step=1)


    if st.button("Make Reservation"):
        result_make = make_reservation(room_number_make, guest_name, contact_number, check_in_date, check_out_date, num_people, room_tier_make)
        st.success(result_make)




    st.subheader("Cancel a Reservation:")
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

