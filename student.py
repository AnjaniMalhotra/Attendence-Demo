import streamlit as st
import pandas as pd
import os
import pickle

STATE_FILE = "streamlit_session.pkl"

def load_admin_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {
        "attendance_status": {},
        "attendance_codes": {},
        "attendance_limits": {},
        "submitted_rolls": {},
    }

# Load state from file
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

roll_number = st.text_input("Roll Number")
name = st.text_input("Name")
code_input = st.text_input("Enter Attendance Code")

if st.button("Submit Attendance"):
    if code_input != code_required:
        st.error("❌ Invalid Code.")
    elif roll_number in submitted_rolls:
        st.error("❌ Roll number already submitted.")
    else:
        file_path = f"{selected_class}.csv"
        df = pd.read_csv(file_path)
        if len(df) >= limit:
            st.warning("⚠️ Attendance limit reached.")
        else:
            df.loc[len(df)] = [roll_number, name]
            df.to_csv(file_path, index=False)
            submitted_rolls.add(roll_number)
            st.session_state.submitted_rolls[selected_class] = submitted_rolls

            # Save updated state
            with open(STATE_FILE, "wb") as f:
                pickle.dump(st.session_state, f)

            st.success("✅ Attendance submitted!")
