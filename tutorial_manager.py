import streamlit as st
import json
import os

# --- Tutorial Content Configuration ---
TUTORIAL_MODULES = [
    # Top Row: System Settings / Theme & Constraints
    {"id": "Theme", "name": "Theme Settings", "icon": "🎨", "color": "#F0F4F8"},
    {"id": "Hard Constraints", "name": "Hard Constraints", "icon": "🛡️", "color": "#E9ECEF"},
    {"id": "Soft Constraints", "name": "Soft Constraints", "icon": "⚖️", "color": "#FEFBF3"},
    # Next Rows: Manage Modules
    {"id": "Manage Shifts", "name": "Shifts", "icon": "🗓️", "color": "#FFF4E6"},
    {"id": "Manage Skills", "name": "Skills", "icon": "🔧", "color": "#F3F0FF"},
    {"id": "Grades Hierarchy", "name": "Grades", "icon": "🏆", "color": "#FFF9DB"},
    {"id": "Manage Departments", "name": "Departments", "icon": "🏢", "color": "#E8F4FD"},
    {"id": "Minimum Demand", "name": "Minimum Demand", "icon": "📊", "color": "#FFF5F5"},
    {"id": "Manage Staff", "name": "Staff", "icon": "👥", "color": "#F8F9FA"},
    {"id": "Leave Type", "name": "Leave Types", "icon": "🏖️", "color": "#E6FFFA"},
]

TUTORIAL_STEPS = {
    "Manage Departments": [
        {"title": "Welcome to Departments", "text": "This is where you define the different areas of your hospital. Each nurse belongs to one primary department.", "target": "🏢 Departments"},
        {"title": "Adding a Department", "text": "Click 'Add New Department' to create a new area. You'll need a unique ID and a friendly name.", "target": "Add New Department"},
        {"title": "Managing Lists", "text": "You can edit or delete departments here. Note: You can't delete a department if nurses are still assigned to it!", "target": "Available Departments"},
    ],
    "Manage Shifts": [
        {"title": "Defining Shifts", "text": "Shifts are the building blocks of your roster. Define when work starts and ends.", "target": "🗓️ Shifts"},
        {"title": "Shift Colors", "text": "Use colors to make your roster visually easy to read. Night shifts are special and have strict recovery rules!", "target": "Add New Shift"},
    ],
    "Manage Skills": [
        {"title": "Specializations", "text": "Nurses have different skills (ICU, ER, ACLS). Some shifts might require specific skills to be present.", "target": "🔧 Skills"},
    ],
    "Grades Hierarchy": [
        {"title": "The Pyramid", "text": "Grades define seniority. The system uses this to ensure shifts are covered by qualified staff.", "target": "🏆 Grades"},
    ],
    "Leave Type": [
        {"title": "Time Off", "text": "Define types of leave like Annual, Sick, or Unpaid. These are automatically respected during generation.", "target": "🏖️ Leave Types"},
    ],
    "Manage Staff": [
        {"title": "Your Personnel", "text": "This is the heart of the system. Manage your nurses, their grades, skills, and department assignments.", "target": "👥 Staff"},
        {"title": "Smart Filters", "text": "Use the search and filter bar to quickly find staff by name, grade, or department.", "target": "🔍 Search"},
    ],
    "Minimum Demand": [
        {"title": "Coverage Needs", "text": "How many nurses do you need for each shift? Define your standard requirements here.", "target": "📊 Minimum Demand"},
        {"title": "Overrides", "text": "Busy holiday coming up? Use 'Date-Specific Overrides' to adjust demand for specific days.", "target": "Date-Specific Overrides"},
    ],
    "Theme": [
        {"title": "Personalize", "text": "Choose a look that suits you. Try 'Eye Comfort' for late-night planning!", "target": "🎨 Theme Settings"},
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
    """Initializes session state for the tutorial system, loading from a unified cookie if available."""
    # 1. Base initialization
    if 'completed_tutorials' not in st.session_state:
        st.session_state.completed_tutorials = set()
    if 'tutorial_active' not in st.session_state:
        st.session_state.tutorial_active = False
    if 'tutorial_finished' not in st.session_state:
        st.session_state.tutorial_finished = False
    if 'current_tutorial_module' not in st.session_state:
        st.session_state.current_tutorial_module = None
    if 'tutorial_started' not in st.session_state:
        st.session_state.tutorial_started = False
    if 'show_tutorial_landing' not in st.session_state:
        st.session_state.show_tutorial_landing = True
    if 'certificate_earned_date' not in st.session_state:
        st.session_state.certificate_earned_date = None

    # 2. Skip cookie loading if we just performed a reset in this session
    if st.session_state.get('just_reset'):
        st.session_state.just_reset = False
        return

    # 3. Load from unified cookie
    if 'cookie_manager' in st.session_state:
        cm = st.session_state.cookie_manager
        raw_state = cm.get(cookie="nurse_tutorial_state")
        
        if raw_state:
            try:
                # Handle potential JSON parsing errors
                if isinstance(raw_state, str):
                    import json
                    state = json.loads(raw_state)
                else:
                    state = raw_state
                
                # Validation: Ensure only valid module IDs are kept
                valid_ids = {m['id'] for m in TUTORIAL_MODULES}
                visited = [m for m in state.get("visited_modules", []) if m in valid_ids]
                
                st.session_state.completed_tutorials = set(visited)
                st.session_state.tutorial_started = state.get("tutorial_started", False)
                st.session_state.tutorial_finished = state.get("tutorial_finished", False)
                st.session_state.certificate_earned_date = state.get("certificate_earned_date")
                
                # If they have progress or finished, skip landing
                if st.session_state.tutorial_started or st.session_state.tutorial_finished or len(st.session_state.completed_tutorials) > 0:
                    st.session_state.show_tutorial_landing = False
            except Exception:
                # If corruption occurs, we ignore the cookie but keep base state
                pass

    # 3. Handle query param override
    if st.query_params.get("tutorial") == "true":
        st.session_state.show_tutorial_landing = True
        st.session_state.tutorial_active = False
        st.session_state.current_tutorial_module = None
        st.session_state.tutorial_finished = False
        st.session_state.tutorial_started = False
        st.session_state.completed_tutorials = set()

def sync_state_to_cookies():
    """Persists all tutorial variables together in a single JSON cookie."""
    if 'cookie_manager' not in st.session_state:
        return
        
    cm = st.session_state.cookie_manager
    
    state_obj = {
        "visited_modules": list(st.session_state.completed_tutorials),
        "tutorial_started": st.session_state.tutorial_started,
        "tutorial_finished": st.session_state.tutorial_finished,
        "certificate_earned_date": st.session_state.certificate_earned_date
    }
    
    # Use a unique key to prevent StreamlitDuplicateElementKey errors if called multiple times in one run
    sync_key = f"sync_state_{st.session_state.get('sync_count', 0)}"
    st.session_state.sync_count = st.session_state.get('sync_count', 0) + 1
    
    import json
    cm.set(cookie="nurse_tutorial_state", val=json.dumps(state_obj), key=sync_key)
    
    # Also set a legacy compatible cookie for basic completed check if needed by other components
    if st.session_state.tutorial_finished:
        legacy_key = f"sync_legacy_{st.session_state.get('sync_count_legacy', 0)}"
        st.session_state.sync_count_legacy = st.session_state.get('sync_count_legacy', 0) + 1
        cm.set(cookie="tutorial_completed", val="true", key=legacy_key)

def add_visited_module(module_id):
    """Adds a module to the visited list and syncs to cookies."""
    # Map the display name/id to the tutorial module ID if needed
    # (Checking if it's one of the 10 modules)
    module_ids = [m['id'] for m in TUTORIAL_MODULES]
    
    # Safety check for session state initialization
    if 'completed_tutorials' not in st.session_state:
        st.session_state.completed_tutorials = set()
    if 'tutorial_started' not in st.session_state:
        st.session_state.tutorial_started = False
        
    if module_id in module_ids and module_id not in st.session_state.completed_tutorials:
        st.session_state.completed_tutorials.add(module_id)
        st.session_state.tutorial_started = True
        
        if len(st.session_state.completed_tutorials) == len(TUTORIAL_MODULES):
            st.session_state.tutorial_finished = True
        sync_state_to_cookies()

def reset_tutorial():
    """Resets the tutorial progress and clears cookies."""
    # Set a flag to bypass cookie loading on the next run
    st.session_state.just_reset = True
    
    st.session_state.completed_tutorials = set()
    st.session_state.tutorial_started = False
    st.session_state.tutorial_finished = False
    st.session_state.tutorial_active = True
    st.session_state.show_tutorial_landing = False
    st.session_state.current_page = 'Tutorial Menu'
    st.session_state.current_tutorial_module = None
    st.session_state.certificate_earned_date = None
    
    # Clear cookies (both unified and legacy)
    if 'cookie_manager' in st.session_state:
        cm = st.session_state.cookie_manager
        
        # Use sync count logic for unique keys if needed or just delete
        st.session_state.sync_count = st.session_state.get('sync_count', 0) + 1
        sync_key = f"reset_state_{st.session_state.sync_count}"
        
        # Clear main state objects
        cm.set(cookie="nurse_tutorial_state", val="{}", key=sync_key)
        cm.set(cookie="tutorial_completed", val="false", key=sync_key + "_leg")
        
    # No st.rerun() here - let the script continue so the cookie set can render.
    # The st.button that calls this will naturally cause a rerun anyway.

def render_landing_page():
    """Renders the first-time visit landing page with 100vh flex centering."""
    
    # Base64 encode the illustration for inline display if possible, or just use absolute path
    # Since we are in Streamlit, using an absolute path or served path is tricky.
    # We'll use the image from the local path.
    
    st.markdown("""
        <style>
        /* Hide sidebar and header completely */
        [data-testid="collapsedControl"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        header { visibility: hidden; }
        
        /* Make the app container fill the screen and center content */
        .stApp {
            background: linear-gradient(135deg, #e0f7fa 0%, #e8eaf6 50%, #f3e5f5 100%) !important;
            height: 100vh;
        }
        
        /* Target the main scrollable area */
        .main [data-testid="stVerticalBlock"] > div:first-child {
            padding-top: 0 !important;
        }

        .landing-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 40px 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .illustration-img {
            max-width: 400px;
            width: 100%;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .landing-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 10px;
            color: #1E1E1E;
            line-height: 1.2;
        }
        
        .landing-subtitle {
            font-size: 1.5rem;
            color: #008080;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .landing-description {
            font-size: 1.2rem;
            color: #555;
            max-width: 600px;
            margin-bottom: 40px;
            line-height: 1.6;
        }
        
        /* Premium Buttons Styling */
        div.stButton > button {
            height: 55px !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            margin-bottom: 15px !important;
        }
        
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #008080 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0,128,128,0.3) !important;
        }
        
        div.stButton > button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0,128,128,0.4) !important;
        }
        
        div.stButton > button:not([data-testid="baseButton-primary"]) {
            background-color: transparent !important;
            border: 2px solid #008080 !important;
            color: #008080 !important;
        }
        
        div.stButton > button:not([data-testid="baseButton-primary"]):hover {
            background-color: rgba(0,128,128,0.05) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Centers the entire block in the column
    st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) # Top spacer
    
    # We'll use a single markdown for the non-interactive parts to ensure they are grouped
    st.markdown(f"""
        <div class="landing-container">
            <div class="landing-title">Nurse Rostering System</div>
            <div class="landing-subtitle">Jump in and explore!</div>
            <div class="landing-description">
                Master the art of scheduling. Learn how to configure staff, shifts, and constraints to generate optimized rosters in seconds.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Buttons centered via columns
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if st.button("Start Tutorial →", key="start_tutorial_btn", use_container_width=True, type="primary"):
            st.session_state.tutorial_active = True
            st.session_state.tutorial_started = True
            st.session_state.show_tutorial_landing = False
            sync_state_to_cookies()
            st.rerun()
            
        if st.button("Explore on Your Own →", key="explore_btn", use_container_width=True):
            st.session_state.show_tutorial_landing = False
            st.session_state.tutorial_active = False
            st.session_state.tutorial_started = True
            sync_state_to_cookies()
            st.rerun()

def render_tutorial_menu():
    """Renders the grid of tutorial cards with completion indicators."""
    # Center-aligned header
    st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>Guided Tutorial Workflow</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1rem; color: #666; margin-bottom: 30px;'>Explore each module to master the Nurse Rostering System.</p>", unsafe_allow_html=True)

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

    # Custom CSS for premium tutorial cards
    st.markdown("""
        <style>
        .stButton > button {
            height: 100px !important;
            border-radius: 12px !important;
            border: 2px solid #F0F0F0 !important;
            transition: all 0.3s ease !important;
            background: #FFF !important;
            color: #333 !important;
            white-space: pre-wrap !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            padding: 10px !important;
        }
        .stButton > button:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 10px 20px rgba(0,0,0,0.05) !important;
            border-color: #008080 !important;
        }
        /* Completed Module Style */
        .completed-btn > div > button {
            background-color: #f0fff4 !important;
            border-color: #9ae6b4 !important;
            color: #2f855a !important;
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
        # Center the rows by adding margin columns
        cols = st.columns([1] + [2] * len(row_modules) + [1])
        for i, module in enumerate(row_modules):
            with cols[i+1]:
                is_completed = module['id'] in st.session_state.completed_tutorials
                status_emoji = "✅ " if is_completed else ""
                btn_label = f"{module['icon']}\n{status_emoji}{module['name']}"
                
                # Wrap in a container to target via CSS
                if is_completed:
                    st.markdown('<div class="completed-btn">', unsafe_allow_html=True)
                
                if st.button(btn_label, key=f"btn_menu_{module['id']}", use_container_width=True):
                    add_visited_module(module['id'])
                    st.session_state.current_tutorial_module = module['id']
                    st.session_state.current_page = module['id']
                    st.rerun()
                
                if is_completed:
                    st.markdown('</div>', unsafe_allow_html=True)

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
            import datetime
            st.session_state.certificate_earned_date = datetime.datetime.now().strftime("%B %d, %Y")
            st.session_state.tutorial_active = False
            st.session_state.tutorial_finished = True
            st.session_state.show_tutorial_summary = True
            sync_state_to_cookies()
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

def render_sidebar_progress():
    """Renders the dynamic tutorial navigation button based on progress."""
    total = len(TUTORIAL_MODULES)
    completed = list(st.session_state.get('completed_tutorials', []))
    visited = len(completed)
    
    # 🏅 Tutorial & Certificate (Dropdown Style)
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<span style='font-size: 0.75rem; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>🏅 Tutorial & Certificate</span>", unsafe_allow_html=True)
    
    with st.expander("🏅 Tutorial & Certificate", expanded=False):
        if visited == 0:
            if st.button("🎓 Start Tutorial", use_container_width=True, type="primary"):
                st.session_state.tutorial_active = True
                st.session_state.show_tutorial_landing = False
                st.session_state.current_tutorial_module = None
                st.session_state.current_page = 'Tutorial Menu'
                st.rerun()
        elif visited < total:
            if st.button("🎓 Continue Tutorial", use_container_width=True, type="primary"):
                st.session_state.tutorial_active = True
                st.session_state.show_tutorial_landing = False
                st.session_state.current_tutorial_module = None
                st.session_state.current_page = 'Tutorial Menu'
                st.rerun()
        else:
            # Progress = 100%
            if st.button("🏅 Your Certificate", use_container_width=True, type="primary"):
                st.session_state.current_page = "Certificate"
                st.session_state.tutorial_active = False
                st.rerun()
            
            if st.button("🔄 Reset Progress", use_container_width=True, help="Clear all tutorial data and restart from scratch"):
                reset_tutorial()

        # Progress Bar (optional but nice for context)
        if 0 < visited < total:
            progress_percentage = int((visited / total) * 100)
            st.markdown(f"""
                <div style='margin-top: 10px; margin-bottom: 5px;'>
                    <div style='background-color: #EEE; border-radius: 4px; height: 6px; overflow: hidden;'>
                        <div style='background: #4ECDC4; width: {progress_percentage}%; height: 100%;'></div>
                    </div>
                    <div style='display: flex; justify-content: space-between; font-size: 0.7rem; color: #64748b; margin-top: 4px;'>
                        <span>Progress</span>
                        <span>{progress_percentage}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

def render_certificate():
    """Renders the high-quality styled certificate page with completion date and confetti."""
    # Celebration effect
    st.snow()
    st.balloons()
    
    import datetime
    # Get current date if not already stored
    if not st.session_state.get('certificate_earned_date'):
        st.session_state.certificate_earned_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    # User customization
    col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
    with col_c2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        user_name = st.text_input("Enter your name for the certificate:", value=st.session_state.get('cert_user_name', 'The User'))
        st.session_state.cert_user_name = user_name
        
        # New: Editable Completion Date
        completion_date = st.text_input("Date of Completion:", value=st.session_state.certificate_earned_date)
        st.session_state.certificate_earned_date = completion_date
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"""
        <style>
        .cert-container {{
            background-color: white;
            padding: 60px;
            border: 12px solid #D4AF37; /* Gold Border */
            border-style: double;
            text-align: center;
            max-width: 800px;
            margin: 20px auto;
            color: #333;
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
            position: relative;
            font-family: 'Inter', sans-serif;
            transition: all 0.5s ease;
        }}
        .cert-header {{
            font-family: 'Playfair Display', serif;
            font-size: 3rem;
            color: #D4AF37;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 2px;
        }}
        .cert-sub {{
            font-size: 1.4rem;
            font-style: italic;
            margin-bottom: 15px;
            color: #555;
        }}
        .cert-name {{
            font-size: 2.8rem;
            font-weight: bold;
            text-decoration: underline;
            margin: 25px 0;
            color: #1E1E1E;
        }}
        .cert-desc {{
            font-size: 1.2rem;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        .cert-date {{
            margin-top: 40px;
            font-size: 1.1rem;
            font-weight: bold;
            color: #555;
        }}
        .cert-footer {{
            margin-top: 20px;
            font-size: 1.4rem;
            font-weight: 800;
            color: #D4AF37;
            text-transform: uppercase;
            letter-spacing: 4px;
        }}
        </style>
        
        <div class="cert-container">
            <div class="cert-header">CERTIFICATE OF COMPLETION</div>
            <div class="cert-sub">This certificate is proudly presented to</div>
            <div class="cert-name">{user_name}</div>
            <div class="cert-desc">
                for successfully exploring and completing<br>
                all modules in the<br>
                <b>Nurse Rostering System Tutorial</b>
            </div>
            <div class="cert-date">
                Date of Completion: {completion_date}
            </div>
            <div class="cert-footer">
                CONGRATULATIONS!
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        if st.button("🎉 Back to System", type="primary", use_container_width=True):
            st.session_state.current_page = "Generate Schedule"
            st.rerun()
