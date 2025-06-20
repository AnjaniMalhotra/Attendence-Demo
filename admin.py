import streamlit as st
import os
import pandas as pd
import requests
from datetime import datetime
import pickle

# ---- GitHub Configuration ----
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_USERNAME = st.secrets["GITHUB_USERNAME"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
BRANCH = "main"  # or use 'main' or the branch name

# ---- Admin Credentials ----
ADMIN_USERNAME = st.secrets["ADMIN_USERNAME"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

STATE_FILE = "streamlit_session.pkl"

# ---- GitHub Upload Function ----
def upload_to_github(file_path, repo_path):
    """Upload a local file to GitHub."""
    with open(file_path, "rb") as f:
        content = f.read()
    
    api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{repo_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if file exists
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        sha = response.json()['sha']
    else:
        sha = None

    commit_msg = f"Upload attendance for {file_path}"
    data = {
        "message": commit_msg,
        "content": content.encode("base64"),
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha

    # Send PUT request
    upload_response = requests.put(api_url, headers=headers, json=data)
    return upload_response.status_code == 201 or upload_response.status_code == 200

# ---- Admin Panel ----
def show_admin_panel():
    st.title("🧑‍🏫 Admin Panel")

    # Login
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Logged in as admin!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        return

    # Load attendance state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            admin_state = pickle.load(f)
    else:
        admin_state = {"attendance_status": {}, "attendance_codes": {}, "attendance_limits": {}}

    for key in ["attendance_status", "attendance_codes", "attendance_limits"]:
        if key not in st.session_state:
            st.session_state[key] = admin_state.get(key, {})

    # Add new class
    st.subheader("Manage Classrooms")
    new_class = st.text_input("Create New Class", key="new_class")
    if st.button("Create Classroom"):
        if new_class:
            filename = f"{new_class}.csv"
            if not os.path.exists(filename):
                df = pd.DataFrame(columns=["Roll Number", "Name"])
                df.to_csv(filename, index=False)
                st.success(f"Classroom '{new_class}' created.")
                st.rerun()
            else:
                st.warning("Class already exists!")

    # Select class
    classes = [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv")]
    if not classes:
        st.info("No classes yet.")
        return

    selected_class = st.selectbox("Select Class", classes)

    # View attendance
    df = pd.read_csv(f"{selected_class}.csv")
    st.dataframe(df)

    # Upload to GitHub
    if st.button("Upload Attendance to GitHub"):
        today = datetime.now().strftime("%Y-%m-%d")
        local_file = f"{selected_class}.csv"
        github_file_path = f"attendance/{selected_class}_{today}.csv"

        if upload_to_github(local_file, github_file_path):
            st.success(f"Uploaded to GitHub as {github_file_path}")
        else:
            st.error("Upload failed. Check token/repo permissions.")
