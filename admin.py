import streamlit as st
import os
import pandas as pd
from datetime import datetime
import pickle
from github import Github

# ---- Credentials from Streamlit secrets ----
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
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
        try:
            with open(STATE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Error loading state: {e}")
    return {
        "attendance_status": {},
        "attendance_codes": {},
        "attendance_limits": {}
    }

def get_class_list():
    return [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv")]

def create_classroom(class_name):
    file_path = f"{class_name}.csv"
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Roll Number", "Name"])
        df.to_csv(file_path, index=False)

def delete_classroom(class_name):
    file_path = f"{class_name}.csv"
    if os.path.exists(file_path):
        os.remove(file_path)
        for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
            st.session_state.get(key, {}).pop(class_name, None)
        save_admin_state()

def trigger_student_refresh():
    with open("refresh_trigger.txt", "w") as f:
        f.write(datetime.now().isoformat())

def push_to_github(filename):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_user(GITHUB_USERNAME).get_repo(GITHUB_REPO)
        with open(filename, "rb") as f:
            content = f.read()
        path = f"attendance/{filename}"
        try:
            contents = repo.get_contents(path)
            repo.update_file(contents.path, f"Update {filename}", content, contents.sha)
        except:
            repo.create_file(path, f"Create {filename}", content)
        st.success("✅ Pushed to GitHub successfully!")
    except Exception as e:
        st.error(f"GitHub push failed: {e}")

def show_admin_panel():
    st.title("🧑‍🏫 Admin Panel")

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                state = load_admin_state()
                for k, v in state.items():
                    st.session_state[k] = v
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    if st.sidebar.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.subheader("Manage Classrooms")
    new_class = st.text_input("Add New Classroom")
    if st.button("Add Classroom"):
        if new_class:
            create_classroom(new_class)
            st.success(f"{new_class} created.")
            st.rerun()

    class_list = get_class_list()
    if not class_list:
        st.warning("No classrooms found.")
        return

    selected_class = st.selectbox("Select Classroom", class_list)

    if st.button("Delete Selected Classroom"):
        delete_classroom(selected_class)
        st.success(f"{selected_class} deleted.")
        st.rerun()

    st.markdown("---")
    st.subheader(f"Attendance Controls for '{selected_class}'")

    status = st.session_state.attendance_status.get(selected_class, False)
    st.info(f"Attendance is currently {'🟢 OPEN' if status else '🔴 CLOSED'}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Open Attendance"):
            st.session_state.attendance_status[selected_class] = True
            save_admin_state()
            trigger_student_refresh()
            st.success("Attendance opened.")
            st.rerun()

    with col2:
        if st.button("Close Attendance"):
            st.session_state.attendance_status[selected_class] = False
            save_admin_state()
            trigger_student_refresh()
            st.info("Attendance closed.")
            st.rerun()

    code = st.text_input("Set Attendance Code", st.session_state.attendance_codes.get(selected_class, ""))
    limit = st.number_input("Set Attendance Limit", 1, 1000, st.session_state.attendance_limits.get(selected_class, 1))
    if st.button("Update Code & Limit"):
        st.session_state.attendance_codes[selected_class] = code
        st.session_state.attendance_limits[selected_class] = limit
        save_admin_state()
        st.success("Updated code and limit.")
        st.rerun()

    st.markdown("---")
    st.subheader("📄 View & Push Attendance")

    file_path = f"{selected_class}.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        st.dataframe(df)

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                "⬇️ Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name=file_path,
                mime="text/csv"
            )
        with btn_col2:
            if st.button("📤 Push to GitHub"):
                push_to_github(file_path)
    else:
        st.warning("Attendance file not found.")
