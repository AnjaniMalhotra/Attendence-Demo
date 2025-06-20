import streamlit as st
import os
import pandas as pd
from datetime import datetime
import pickle
from github import Github

# --- Admin Credentials from secrets ---
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# --- GitHub Details from secrets ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_USERNAME = st.secrets["GITHUB_USERNAME"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

STATE_FILE = "streamlit_session.pkl"

def save_admin_state():
    admin_state = {
        "attendance_status": st.session_state.attendance_status,
        "attendance_codes": st.session_state.attendance_codes,
        "attendance_limits": st.session_state.attendance_limits
    }
    with open(STATE_FILE, "wb") as f:
        pickle.dump(admin_state, f)

def load_admin_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {"attendance_status": {}, "attendance_codes": {}, "attendance_limits": {}}

def get_class_list():
    return [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv") and f != STATE_FILE.replace(".pkl", ".csv")]

def create_classroom(class_name):
    file_path = f"{class_name}.csv"
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Roll Number", "Name"])
        df.to_csv(file_path, index=False)

def delete_classroom(class_name):
    file_path = f"{class_name}.csv"
    if os.path.exists(file_path):
        os.remove(file_path)
    for state in ["attendance_status", "attendance_codes", "attendance_limits"]:
        if class_name in st.session_state[state]:
            del st.session_state[state][class_name]
    save_admin_state()

def trigger_student_refresh():
    with open("refresh_trigger.txt", "w") as f:
        f.write(datetime.now().isoformat())

def push_to_github(classroom, df):
    file_path = f"{classroom}.csv"
    file_name = f"attendance_{classroom}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    repo_path = f"records/{file_name}"
    content = df.to_csv(index=False)

    g = Github(GITHUB_TOKEN)
    repo = g.get_user(GITHUB_USERNAME).get_repo(GITHUB_REPO)
    try:
        repo.create_file(repo_path, f"Add attendance for {classroom}", content, branch="main")
        st.success(f"✅ File pushed to GitHub: `{repo_path}`")
    except Exception as e:
        st.warning(f"⚠️ Could not push to GitHub: {e}")

def show_admin_panel():
    st.title("🧑‍🏫 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                admin_state = load_admin_state()
                for key in admin_state:
                    st.session_state[key] = admin_state[key]
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    if st.sidebar.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.subheader("📂 Manage Classrooms")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_class = st.text_input("New Classroom Name")
    with col2:
        if st.button("Add Classroom"):
            if new_class.strip():
                create_classroom(new_class.strip())
                st.success(f"Created class: {new_class}")
                st.rerun()

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms found.")
        return

    selected_class = st.selectbox("Select Classroom", class_list)

    if st.button("🗑️ Delete Selected Class"):
        delete_classroom(selected_class)
        st.rerun()

    st.subheader(f"🕹️ Control Attendance for '{selected_class}'")
    current_status = st.session_state.attendance_status.get(selected_class, False)
    st.info(f"Portal is currently: **{'OPEN' if current_status else 'CLOSED'}**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            st.session_state.attendance_status[selected_class] = True
            save_admin_state()
            trigger_student_refresh()
            st.rerun()
    with col2:
        if st.button("Close Attendance"):
            st.session_state.attendance_status[selected_class] = False
            save_admin_state()
            trigger_student_refresh()
            st.rerun()

    st.markdown("#### Token Code & Limit")
    current_code = st.session_state.attendance_codes.get(selected_class, "")
    current_limit = st.session_state.attendance_limits.get(selected_class, 1)

    code = st.text_input("Code", value=current_code)
    limit = st.number_input("Limit", min_value=1, value=current_limit, step=1)

    if st.button("Update Code & Limit"):
        st.session_state.attendance_codes[selected_class] = code
        st.session_state.attendance_limits[selected_class] = int(limit)
        save_admin_state()
        st.success("Code and limit updated")
        st.rerun()

    st.subheader("📊 Attendance Records")
    file_path = f"{selected_class}.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if not df.empty:
            st.dataframe(df)

            if st.button("📤 Push to GitHub"):
                push_to_github(selected_class, df)

            st.download_button(
                "⬇️ Download CSV",
                df.to_csv(index=False).encode('utf-8'),
                file_name=f"{selected_class}_attendance.csv",
                mime="text/csv"
            )
        else:
            st.info("No records found yet.")
    else:
        st.error("Attendance file not found.")
