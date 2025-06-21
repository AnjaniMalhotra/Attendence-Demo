# ---------- ✅ student.py (Updated to handle timezone, name-locking, persistent state) ----------

import streamlit as st
import pandas as pd
import os
import pickle
from datetime import datetime
import pytz

STATE_FILE = "streamlit_session.pkl"
IST = pytz.timezone('Asia/Kolkata')

def current_ist_date():
    return datetime.now(IST).strftime("%Y-%m-%d")

def load_admin_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {
        "attendance_status": {},
        "attendance_codes": {},
        "attendance_limits": {},
        "submitted_rolls": {},
        "roll_name_map": {},
    }

# Load persistent state
admin_state = load_admin_state()
for key in admin_state:
    st.session_state[key] = admin_state[key]

st.title("🎓 Student Attendance")

class_list = [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv") and f != STATE_FILE.replace(".pkl", ".csv")]
if not class_list:
    st.warning("No classrooms available.")
    st.stop()

selected_class = st.selectbox("Select Your Class", class_list)
attendance_open = st.session_state.attendance_status.get(selected_class, False)

if not attendance_open:
    st.error(f"Attendance for '{selected_class}' is currently CLOSED.")
    st.stop()

code_required = st.session_state.attendance_codes.get(selected_class, "")
limit = st.session_state.attendance_limits.get(selected_class, 1)
submitted_rolls = st.session_state.submitted_rolls.get(selected_class, set())
roll_name_map = st.session_state.roll_name_map.get(selected_class, {})

roll_number = st.text_input("Roll Number")
name = ""
if roll_number in roll_name_map:
    name = roll_name_map[roll_number]
    st.info(f"📝 Name auto-filled for roll {roll_number}: {name}")
else:
    name = st.text_input("Name")

code_input = st.text_input("Enter Attendance Code")

if st.button("Submit Attendance"):
    if code_input != code_required:
        st.error("❌ Invalid Code.")
    elif roll_number in submitted_rolls:
        st.error("❌ Roll number already submitted.")
    elif roll_number in roll_name_map and roll_name_map[roll_number] != name:
        st.error("❌ This roll number is already assigned to a different name.")
    elif not name:
        st.error("❌ Name is required.")
    else:
        file_path = f"{selected_class}.csv"
        df = pd.read_csv(file_path)
        if len(df[df['Date'] == current_ist_date()]) >= limit:
            st.warning("⚠️ Attendance limit reached for today.")
        else:
            new_entry = pd.DataFrame([[current_ist_date(), roll_number, name]], columns=["Date", "Roll Number", "Name"])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(file_path, index=False)

            # Update state
            submitted_rolls.add(roll_number)
            st.session_state.submitted_rolls[selected_class] = submitted_rolls
            roll_name_map[roll_number] = name
            st.session_state.roll_name_map[selected_class] = roll_name_map

            with open(STATE_FILE, "wb") as f:
                pickle.dump(st.session_state, f)

            st.success("✅ Attendance submitted successfully!")
