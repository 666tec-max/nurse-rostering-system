import streamlit as st
import json
import os

# --- Tutorial Content Configuration ---
TUTORIAL_MODULES = [
    # Top Row: System Settings / Theme & Constraints
    {"id": "Theme", "name": "Theme", "icon": "🎨", "color": "#F0F4F8"},
    {"id": "Hard Constraints", "name": "Hard Constraints", "icon": "🛡️", "color": "#E9ECEF"},
    {"id": "Soft Constraints", "name": "Soft Constraints", "icon": "⚖️", "color": "#FEFBF3"},
    # Next Rows: Manage Modules
    {"id": "Manage Shifts", "name": "Manage Shifts", "icon": "🗓️", "color": "#FFF4E6"},
    {"id": "Manage Skills", "name": "Manage Skills", "icon": "🔧", "color": "#F3F0FF"},
    {"id": "Grades Hierarchy", "name": "Manage Grade", "icon": "🏆", "color": "#FFF9DB"},
    {"id": "Manage Departments", "name": "Manage Departments", "icon": "🏢", "color": "#E8F4FD"},
    {"id": "Minimum Demand", "name": "Manage Demand", "icon": "📊", "color": "#FFF5F5"},
    {"id": "Manage Staffs", "name": "Manage Staff", "icon": "👥", "color": "#F8F9FA"},
    {"id": "Leave Types", "name": "Manage Leave Types", "icon": "🏖️", "color": "#E6FFFA"},
]

TUTORIAL_STEPS = {
    "Manage Departments": [
        {"title": "Welcome to Departments", "text": "This is where you define the different areas of your hospital. Each nurse belongs to one primary department.", "target": "🏢 Manage Departments"},
        {"title": "Adding a Department", "text": "Click 'Add New Department' to create a new area. You'll need a unique ID and a friendly name.", "target": "Add New Department"},
        {"title": "Managing Lists", "text": "You can edit or delete departments here. Note: You can't delete a department if nurses are still assigned to it!", "target": "Available Departments"},
    ],
    "Manage Shifts": [
        {"title": "Defining Shifts", "text": "Shifts are the building blocks of your roster. Define when work starts and ends.", "target": "🗓️ Manage Shifts"},
        {"title": "Shift Colors", "text": "Use colors to make your roster visually easy to read. Night shifts are special and have strict recovery rules!", "target": "Add New Shift"},
    ],
    "Manage Skills": [
        {"title": "Specializations", "text": "Nurses have different skills (ICU, ER, ACLS). Some shifts might require specific skills to be present.", "target": "🔧 Manage Skills"},
    ],
    "Grades Hierarchy": [
        {"title": "The Pyramid", "text": "Grades define seniority. The system uses this to ensure shifts are covered by qualified staff.", "target": "🏆 Grades Hierarchy"},
    ],
    "Leave Types": [
        {"title": "Time Off", "text": "Define types of leave like Annual, Sick, or Unpaid. These are automatically respected during generation.", "target": "🏖️ Leave Types"},
    ],
    "Manage Staffs": [
        {"title": "Your Personnel", "text": "This is the heart of the system. Manage your nurses, their grades, skills, and department assignments.", "target": "👥 Personnel Management"},
        {"title": "Smart Filters", "text": "Use the search and filter bar to quickly find staff by name, grade, or department.", "target": "🔍 Search"},
    ],
    "Minimum Demand": [
        {"title": "Coverage Needs", "text": "How many nurses do you need for each shift? Define your standard requirements here.", "target": "📊 Minimum Demand"},
        {"title": "Overrides", "text": "Busy holiday coming up? Use 'Date-Specific Overrides' to adjust demand for specific days.", "target": "Date-Specific Overrides"},
    ],
    "Theme": [
        {"title": "Personalize", "text": "Choose a look that suits you. Try 'Eye Comfort' for late-night planning!", "target": "Theme Settings"},
    ],
    "Hard Constraints": [
        {"title": "Unbreakable Rules", "text": "These rules are strictly enforced by the AI. No nurse will ever work more than 7 days in a row!", "target": "🛡️ Hard Constraints"},
    ],
    "Soft Constraints": [
        {"title": "Balancing Act", "text": "Guidance for the AI. Adjust 'Fairness' to ensure everyone gets an equal share of weekends and nights.", "target": "⚖️ Soft Constraints"},
    ],
}

def check_url_trigger():
    """Detect if we are on the test site or have a query param to force the tutorial."""
    # Check query params FIRST as it's the most explicit override
    if st.query_params.get("tutorial") == "true":
        return True
        
    try:
        # Streamlit 1.34+ context headers
        # Note: This might not work on all Streamlit versions/environments
        from streamlit import context
        host = context.headers.get("Host", "")
        # The user specifically mentioned https://test-roster-system.streamlit.app/
        if "test-roster-system" in host or "streamlit.app" in host:
            return True
    except:
        pass
        
    return False

def initialize_tutorial_state():
    """Initializes session state for the tutorial system."""
    # Ensure all required keys exist
    if 'completed_tutorials' not in st.session_state:
        st.session_state.completed_tutorials = set()
    if 'tutorial_active' not in st.session_state:
        st.session_state.tutorial_active = False
    if 'tutorial_finished' not in st.session_state:
        st.session_state.tutorial_finished = False
    if 'current_tutorial_module' not in st.session_state:
        st.session_state.current_tutorial_module = None
    if 'current_tutorial_step' not in st.session_state:
        st.session_state.current_tutorial_step = 0

    # Logic to show the landing page
    if 'show_tutorial_landing' not in st.session_state:
        # Default to True for everyone in a new session
        st.session_state.show_tutorial_landing = True

    # Allow query param to FORCE it anytime (overrides everything)
    if st.query_params.get("tutorial") == "true":
        st.session_state.show_tutorial_landing = True
        st.session_state.tutorial_active = False
        st.session_state.current_tutorial_module = None
        st.session_state.tutorial_finished = False

def reset_tutorial():
    """Resets the tutorial progress."""
    st.session_state.tutorial_active = True
    st.session_state.show_tutorial_landing = False
    st.session_state.current_tutorial_module = None
    st.session_state.current_tutorial_step = 0
    st.session_state.completed_tutorials = set()
    st.session_state.tutorial_finished = False

def render_landing_page():
    """Renders the first-time visit landing page."""
    st.markdown("""
        <style>
        [data-testid="collapsedControl"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        .stApp {
            background: linear-gradient(135deg, #e0f7fa 0%, #e8eaf6 50%, #f3e5f5 100%) !important;
        }
        .landing-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            text-align: center;
            position: relative;
            z-index: 10;
        }
        .landing-title {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 20px;
            color: #1E1E1E;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.05);
        }
        .landing-subtitle {
            font-size: 1.5rem;
            color: #555;
            margin-bottom: 50px;
        }
        /* Floating Background Icons */
        .icon-bg {
            position: absolute;
            font-size: 10rem;
            opacity: 0.05;
            z-index: 1;
        }
        .icon-1 { top: 10%; left: 10%; transform: rotate(-15deg); }
        .icon-2 { top: 60%; right: 10%; transform: rotate(15deg); }
        .icon-3 { bottom: 10%; left: 30%; transform: rotate(5deg); }
        </style>
        <div class="icon-bg icon-1">🗓️</div>
        <div class="icon-bg icon-2">⏱️</div>
        <div class="icon-bg icon-3">🩺</div>
        <div class="landing-container">
            <div class="landing-title">Welcome to Nurse Rostering System</div>
            <div class="landing-subtitle">Jump in and explore!</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='display: flex; justify-content: center; gap: 20px; margin-top: 20px;'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 1])
    with col2:
        if st.button("Start Tutorial →", use_container_width=True, type="primary"):
            st.session_state.tutorial_active = True
            st.session_state.show_tutorial_landing = False
            st.rerun()
    with col3:
        if st.button("Explore on Your Own →", use_container_width=True):
            st.session_state.show_tutorial_landing = False
            st.session_state.tutorial_active = False
            # We explicitly do NOT set tutorial_finished to True here,
            # so the persistent "Start Tutorial" button can appear.
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def render_tutorial_menu():
    """Renders the grid of tutorial cards."""
    # Center-aligned title
    st.markdown("<h1 style='text-align: center;'>Guided Tutorial Workflow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1rem; color: #666;'>Visit all modules to unlock the full app experience. Progress through each area to master the system.</p>", unsafe_allow_html=True)

    # Progress Calculation
    total_modules = len(TUTORIAL_MODULES)
    completed_count = len(st.session_state.completed_tutorials)
    progress_percentage = int((completed_count / total_modules) * 100)

    # Progress Indicator
    st.markdown(f"""
        <div style="max-width: 600px; margin: 20px auto;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-weight: 600;">Overall Progress</span>
                <span style="font-weight: 600;">{progress_percentage}%</span>
            </div>
            <div style="background-color: #EEE; border-radius: 10px; height: 12px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #4ECDC4, #FF6B6B); width: {progress_percentage}%; height: 100%; transition: width 0.5s ease;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Custom CSS for playful cards
    st.markdown("""
        <style>
        .stButton > button {
            height: 120px !important;
            border-radius: 15px !important;
            border: 2px solid #F0F0F0 !important;
            transition: all 0.3s ease !important;
            background: #FFF !important;
            color: #333 !important;
            padding: 10px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .stButton > button:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 10px 20px rgba(0,0,0,0.05) !important;
            border-color: #4ECDC4 !important;
        }
        .stButton > button p {
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            margin: 0 !important;
            white-space: pre-wrap !important;
        }
        .completed-btn {
            border-color: #4CAF50 !important;
            background: #F1FBF2 !important;
        }
        .active-btn {
            border-color: #4ECDC4 !important;
            border-width: 3px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Define Rows based on requirements
    rows = [
        TUTORIAL_MODULES[0:3],   # Theme, Hard, Soft (Row 1)
        TUTORIAL_MODULES[3:6],   # Shifts, Skills, Grade (Row 2)
        [TUTORIAL_MODULES[6], TUTORIAL_MODULES[7]], # Dept, Demand (Row 3)
        [TUTORIAL_MODULES[8], TUTORIAL_MODULES[9]], # Staff, Leave (Row 4)
    ]

    for row_modules in rows:
        margin_col_left, *cols, margin_col_right = st.columns([1] + [2] * len(row_modules) + [1])
        for i, module in enumerate(row_modules):
            with cols[i]:
                is_completed = module['id'] in st.session_state.completed_tutorials
                
                status_emoji = "✅ " if is_completed else ""
                btn_label = f"{module['icon']}\n{status_emoji}{module['name']}"
                
                if st.button(btn_label, key=f"btn_{module['id']}", use_container_width=True):
                    st.session_state.completed_tutorials.add(module['id'])
                    st.session_state.current_tutorial_module = module['id']
                    st.session_state.current_page = module['id']
                    st.rerun()

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
    
    # Final Action Button
    all_done = completed_count == total_modules
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        if st.button("Finish Tutorial & Start Using App", 
                     use_container_width=True, 
                     type="primary", 
                     disabled=not all_done,
                     help="Visit all modules to unlock the app"):
            st.session_state.tutorial_active = False
            st.session_state.tutorial_finished = True
            st.session_state.show_tutorial_summary = True
            st.rerun()

# render_tutorial_step removed as it is no longer needed in the new checklist flow

def render_summary_page():
    """Renders the final tutorial summary."""
    st.balloons()
    st.markdown("""
        <div style="text-align: center; padding: 40px;">
            <h1 style="font-size: 3rem;">🎓 Roster Master!</h1>
            <p style="font-size: 1.2rem; margin-bottom: 30px;">
                You've completed the orientation. You're now ready to build 
                the most efficient rosters your hospital has ever seen.
            </p>
            <h3>Quick Tips:</h3>
            <ul style="text-align: left; display: inline-block; margin-bottom: 30px;">
                <li>Start by setting up your <b>Departments</b> and <b>Staff</b>.</li>
                <li>Check <b>Hard Constraints</b> if you're not sure why someone wasn't assigned.</li>
                <li>Use the <b>Shift Painter</b> to manually tweak generated rosters.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Enter the System", use_container_width=True, type="primary"):
        st.session_state.tutorial_active = False
        st.session_state.show_tutorial_summary = False
        st.rerun()
