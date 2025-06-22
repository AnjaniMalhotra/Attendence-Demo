🧠 Smart Attendance System

A robust and modular Smart Attendance System built with Streamlit, Supabase, and GitHub Integration. The app features two separate panels for administrators and students, ensuring security, control, and real-time updates.

🔐 Admin Panel Features

Accessible only with secure login credentials:

🎓 Class Management
➕ Create New Class with default settings.
📋 Select Class from dropdown to view and manage.
⚙️ Update Attendance Code & Daily Limit per class.
📅 Attendance Controls
✅ Open/Close Attendance for a selected class.
🔁 Only one class can be open for attendance at a time.
📊 Attendance Matrix
Auto-generated pivot table displaying:
Roll Number, Name, and Date-wise Attendance.
Highlighted colors for Present (✅) and Absent (❌).
⬇️ Download CSV of attendance matrix.
🚀 Push matrix to GitHub repo with commit.
🗑️ Delete Class
Permanently deletes:
Classroom Settings
Attendance Records
Roll Number Mappings
Confirmation required (DELETE) for safety.
🎓 Student Panel Features

No login required – only open when a class is active:

📥 Submit Attendance
📌 Select open class
🔢 Enter Roll Number & Name
🔐 Enter attendance code
⛔ Prevents:
Duplicate entries for the day
Multiple students using same roll
Exceeding daily limit for class
📈 View Own Attendance
📋 Automatically displays only that student’s:
Attendance history (with dates)
Structured in tabular format
⚙️ Technologies Used

Streamlit for front-end interface
Supabase for real-time database and authentication
GitHub API for version-controlled data storage
Python and Pandas for data manipulation
Matplotlib for visual analytics (admin-side)

