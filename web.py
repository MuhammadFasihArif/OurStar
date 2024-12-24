import streamlit as st
import sqlite3
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import random

# Database setup
conn = sqlite3.connect('team_app.db')
c = conn.cursor()

# Create tables if they do not exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    pdf BLOB,
    due_date DATE
)''')
c.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    task TEXT,
    done BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(project_id) REFERENCES projects(id)
)''')
conn.commit()

# RTC configuration for WebRTC
RTC_CONFIGURATION = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# Helper functions for authentication
def signup(username, password):
    try:
        role = "Admin" if username == "MFasihArif" else "Member"
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        st.success("User created successfully!")
    except sqlite3.IntegrityError:
        st.error("Username already exists!")

def home_page():
    st.title("Welcome :orange[Peanut Boy] HO HO HO!")
    st.subheader("Are you ready to get :red[spanked] by the amazing projects we are gonna do in near future?")
    st.subheader("If yes then go on now press :green[YES] button champ. If :red[No] then get the hell out of here you stinky pussy.")

    col1, col2 = st.columns(2)
    with col1:
        yes = st.button(":green[YES]")
    with col2:
        no = st.button(":red[NO]")

    if yes:
        st.session_state.response = (
            "Now my friend, you should press YES again and go to the <- :violet[sidebar] and click the :green[Projects page]. "
            "There you will find the :blue[most mind-blowing projects] for making you and me the masters of deep learning and AI."
        )
    elif no:
        st.session_state.response = (
            "You are a :red[stinky pussy] and you should get the hell out of here."
        )

    if "response" in st.session_state:
        st.subheader(st.session_state.response)

def login(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

def reset_password(username, new_password):
    c.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    st.success("Password updated successfully!")

# Video Processor class for screen sharing
class VideoProcessor(VideoProcessorBase):
    def recv(self, frame):
        return frame
    
def text_chat_page():
    st.title("Team Text Chat")
    st.write("Chat with your team members in real-time.")

    # Ensure the messages table exists
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()

    # Fetch all messages from the database
    def fetch_messages():
        c.execute("SELECT sender, content, timestamp FROM messages ORDER BY timestamp ASC")
        return c.fetchall()

    # Initialize session state for messages
    if 'messages' not in st.session_state:
        st.session_state.messages = fetch_messages()

    # Display chat messages
    st.markdown("### Chat History")
    chat_container = st.container()
    with chat_container:
        for sender, content, timestamp in st.session_state.messages:
            with st.chat_message("user" if sender == st.session_state.user[1] else "bot"):
                st.markdown(f"**{sender}:** {content}")

    # Chat input form
    st.markdown("---")
    with st.form(key="chat_form", clear_on_submit=True):
        chat_input = st.text_input("Type your message:", placeholder="Enter your message here...")
        send_button = st.form_submit_button(label="Send")

    # Handle message submission
    if send_button and chat_input.strip():
        # Add the new message to the database
        c.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (st.session_state.user[1], chat_input))
        conn.commit()

        # Update session state and refresh the chat
        st.session_state.messages = fetch_messages()
        #st.experimental_rerun()  # Refresh the page to display new messages
    elif send_button:
        st.warning("Message cannot be empty!")

def fetch_messages():
    c.execute("SELECT * FROM messages")
    messages = c.fetchall()
    formatted_messages = []
    for message in messages:
        formatted_messages.append({
            'role': 'user',  # Assuming all messages are from users
            'content': message[2]
        })
    return formatted_messages




def live_calls_page():
    st.title("Team Live Calls")
    st.write("Connect with your team via video, voice, or screen sharing.")
    
    # Create a table to manage room states
    c.execute('''CREATE TABLE IF NOT EXISTS live_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id TEXT UNIQUE,
        created_by TEXT
    )''')
    conn.commit()

    # Step 1: Check if a room already exists
    active_room = c.execute("SELECT * FROM live_calls").fetchone()
    
    # Initialize session state variables
    if 'room_id' not in st.session_state:
        st.session_state.room_id = None
    if 'in_call' not in st.session_state:
        st.session_state.in_call = False

    # Container for dynamic updates
    call_ui_container = st.container()

    # Handle active room logic
    if active_room:
        room_id = active_room[1]
        creator = active_room[2]
        st.success(f"Active Room ID: {room_id} (Created by: {creator})")
        
        # Join the existing room
        if not st.session_state.in_call:
            if st.button("Join Room"):
                st.session_state.room_id = room_id
                st.session_state.in_call = True

        # Display call options immediately if in call
        with call_ui_container:
            if st.session_state.in_call and st.session_state.room_id == room_id:
                st.info(f"Joined Room ID: {room_id}")
                call_type = st.radio("Select Call Type", ["Video Call", "Voice Call"], index=0)

                enable_screen_sharing = st.checkbox("Enable Screen Sharing", value=False)

                # Set up the call based on selection
                if enable_screen_sharing:
                    st.write("Screen sharing enabled.")
                    webrtc_streamer(
                        key=f"screen-{room_id}",
                        rtc_configuration=RTC_CONFIGURATION,
                        media_stream_constraints={
                            "video": {"mediaSource": "screen"},
                            "audio": True
                        },
                        video_processor_factory=VideoProcessor
                    )
                elif call_type == "Video Call":
                    st.write("Video call active.")
                    webrtc_streamer(
                        key=f"video-{room_id}",
                        rtc_configuration=RTC_CONFIGURATION,
                        video_processor_factory=VideoProcessor
                    )
                elif call_type == "Voice Call":
                    st.write("Voice call active.")
                    webrtc_streamer(
                        key=f"voice-{room_id}",
                        rtc_configuration=RTC_CONFIGURATION,
                        media_stream_constraints={
                            "video": False,
                            "audio": True
                        },
                        video_processor_factory=VideoProcessor
                    )

        # Option for the creator to cancel the room
        if st.session_state.user[1] == creator:  # Match username
            if st.button("Cancel Room"):
                c.execute("DELETE FROM live_calls WHERE room_id = ?", (room_id,))
                conn.commit()
                st.success("Room cancelled. Others can now generate a new Room ID.")
                st.session_state.room_id = None
                st.session_state.in_call = False
                #
    else:
        # Step 2: Allow generating a new room if no active room exists
        if st.button("Generate Room ID"):
            room_id = str(random.randint(1000, 9999))
            st.session_state.room_id = room_id  # Store the generated room ID in session state
            c.execute("INSERT INTO live_calls (room_id, created_by) VALUES (?, ?)", (room_id, st.session_state.user[1]))
            conn.commit()
            st.success(f"Generated Room ID: {room_id}. Share this ID with your team.")
            
            # Display the options immediately
            with call_ui_container:
                st.info(f"Created Room ID: {room_id}")
                call_type = st.radio("Select Call Type", ["Video Call", "Voice Call"], index=0)
                enable_screen_sharing = st.checkbox("Enable Screen Sharing", value=False)

                # Set up the call based on selection
                if enable_screen_sharing:
                    st.write("Screen sharing enabled.")
                    webrtc_streamer(
                        key=f"screen-{room_id}",
                        rtc_configuration=RTC_CONFIGURATION,
                        media_stream_constraints={
                            "video": {"mediaSource": "screen"},
                            "audio": True
                        },
                        video_processor_factory=VideoProcessor
                    )
                elif call_type == "Video Call":
                    st.write("Video call active.")
                    webrtc_streamer(
                        key=f"video-{room_id}",
                        rtc_configuration=RTC_CONFIGURATION,
                        video_processor_factory=VideoProcessor
                    )
                elif call_type == "Voice Call":
                    st.write("Voice call active.")
                    webrtc_streamer(
                        key=f"voice-{room_id}",
                        rtc_configuration=RTC_CONFIGURATION,
                        media_stream_constraints={
                            "video": False,
                            "audio": True
                        },
                        video_processor_factory=VideoProcessor
                    )

    # Optional: Display help or instructions for room generation and joining
    st.info("If a room exists, you can only join it. To create a new room, the existing room must be cancelled.")


    # Optional: Display help or instructions for room generation and joining
    st.info("If a room exists, you can only join it. To create a new room, the existing room must be cancelled.")

# Main app functionality
def main():
    if "user" not in st.session_state:
        st.session_state.user = None

    def login_page():
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.success("Logged in successfully!")
                
            else:
                st.error("Invalid credentials!")

        if st.button("Forgot Password?"):
            reset_username = st.text_input("Enter your username", key="reset_username")
            new_password = st.text_input("Enter new password", type="password", key="reset_password")
            if st.button("Reset Password", key="reset_password_btn"):
                reset_password(reset_username, new_password)

    def signup_page():
        st.title("Signup")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Signup"):
            signup(username, password)

    if st.session_state.user is None:
        auth_page = st.sidebar.selectbox("Auth", ["Login", "Signup"])
        if auth_page == "Login":
            login_page()
        else:
            signup_page()
        return

    st.sidebar.success(f"Logged in as {st.session_state.user[1]} ({st.session_state.user[3]})")
    page = st.sidebar.radio("Navigate", ["Home", "Projects", "Live Calls","Discussions", "Logout"])

    
    def projects_page():
        st.title("Projects Section")
        st.subheader("Manage your projects and track progress here.")

        # Admin-only: Add and delete projects
        if st.session_state.user[3] == "Admin":
            with st.expander("Add New Project"):
                new_title = st.text_input("Project Title", key="new_title")
                new_description = st.text_area("Project Description", key="new_description")
                uploaded_file = st.file_uploader("Upload Project PDF", type="pdf", key="new_pdf")
                new_due_date = st.date_input("Set a Due Date", key="new_due_date")

                # Add tasks for the new project
                st.markdown("**Tasks:**")
                if "new_tasks" not in st.session_state:
                    st.session_state.new_tasks = []
                task_text = st.text_input("Add a task", key="new_task")
                if st.button("Add Task", key="add_task"):
                    if task_text:
                        st.session_state.new_tasks.append({"task": task_text, "done": False})
                        st.success(f"Task '{task_text}' added!")
                for t in st.session_state.new_tasks:
                    st.write(f"- {t['task']}")

                if st.button("Add Project"):
                    pdf_data = uploaded_file.read() if uploaded_file else None
                    c.execute("INSERT INTO projects (title, description, pdf, due_date) VALUES (?, ?, ?, ?)",
                            (new_title, new_description, pdf_data, new_due_date))
                    project_id = c.lastrowid
                    for task in st.session_state.new_tasks:
                        c.execute("INSERT INTO tasks (project_id, task) VALUES (?, ?)", (project_id, task["task"]))
                    conn.commit()
                    st.session_state.new_tasks = []
                    st.success("Project added successfully!")
                    

        # Fetch and display all projects
        projects = c.execute("SELECT * FROM projects").fetchall()
        if not projects:
            st.info("No projects available.")
            return

        for project in projects:
            # Fetch all tasks for this project
            tasks = c.execute("SELECT * FROM tasks WHERE project_id = ?", (project[0],)).fetchall()

            # Check if all tasks are already completed
            if all(task[3] for task in tasks):  # task[3] is the 'done' status
                continue  # Skip this project since all tasks are done

            with st.container():
                st.markdown(f"### {project[1]}")
                st.markdown(f"**Description:** {project[2]}")
                if project[3]:
                    st.download_button("Download Project PDF", data=project[3], file_name="project.pdf", mime="application/pdf")
                st.markdown(f"**Due Date:** {project[4]}")

                # Display tasks with checkboxes for each project
                st.markdown("**Tasks:**")
                task_updates = []  # Track tasks to be updated
                for task in tasks:
                    task_done = st.checkbox(task[2], value=task[3], key=f"task_{task[0]}")
                    task_updates.append((task[0], task_done))

                # Submission button for tasks
                if st.button(f"Submit Completed Tasks for '{project[1]}'", key=f"submit_tasks_{project[0]}"):
                    any_task_updated = False
                    for task_id, task_done in task_updates:
                        c.execute("SELECT done FROM tasks WHERE id = ?", (task_id,))
                        current_done_status = c.fetchone()[0]
                        if task_done and not current_done_status:  # Update only if status has changed
                            c.execute("UPDATE tasks SET done = TRUE WHERE id = ?", (task_id,))
                            any_task_updated = True
                    if any_task_updated:
                        conn.commit()
                        st.success("Tasks updated successfully!")
                        st.balloons()  # Happy animation

                    # Check if all tasks are done after submission
                    updated_tasks = c.execute("SELECT * FROM tasks WHERE project_id = ?", (project[0],)).fetchall()
                    if all(task[3] for task in updated_tasks):  # If all tasks are done
                        st.success(f"All tasks for '{project[1]}' are completed! Project is now hidden.")
                    
                    

                # Admin-only: Delete project
                if st.session_state.user[3] == "Admin":
                    if st.button(f"Delete Project '{project[1]}'", key=f"delete_project_{project[0]}"):
                        c.execute("DELETE FROM tasks WHERE project_id = ?", (project[0],))
                        c.execute("DELETE FROM projects WHERE id = ?", (project[0],))
                        conn.commit()
                        st.warning(f"Project '{project[1]}' deleted.")
                        


    if page == "Home":
        home_page()
    elif page == "Projects":
        projects_page()
    elif page == "Live Calls":
        live_calls_page()
    elif page == "Discussions":
        text_chat_page()
    elif page == "Logout":
        st.session_state.user = None
        

if __name__ == "__main__":
    main()
