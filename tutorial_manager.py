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

    # 2. Load from unified cookie
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
    
    import json
    cm.set(cookie="nurse_tutorial_state", val=json.dumps(state_obj), key="sync_state")
    
    # Also set a legacy compatible cookie for basic completed check if needed by other components
    if st.session_state.tutorial_finished:
        cm.set(cookie="tutorial_completed", val="true", key="sync_legacy")

def add_visited_module(module_id):
    """Adds a module to the visited list and syncs to cookies."""
    # Map the display name/id to the tutorial module ID if needed
    # (Checking if it's one of the 10 modules)
    module_ids = [m['id'] for m in TUTORIAL_MODULES]
    if module_id in module_ids and module_id not in st.session_state.completed_tutorials:
        st.session_state.completed_tutorials.add(module_id)
        st.session_state.tutorial_started = True
        
        # Sync immediately
        sync_state_to_cookies()
        if len(st.session_state.completed_tutorials) == len(TUTORIAL_MODULES):
            st.session_state.tutorial_finished = True
            
        sync_state_to_cookies()

def reset_tutorial():
    """Resets the tutorial progress and clears cookies."""
    st.session_state.tutorial_active = True
    st.session_state.show_tutorial_landing = False
    st.session_state.current_tutorial_module = None
    st.session_state.completed_tutorials = set()
    st.session_state.tutorial_finished = False
    st.session_state.tutorial_started = True # Force them to start again but from landing/menu
    
    # Clear cookies
    if 'cookie_manager' in st.session_state:
        cm = st.session_state.cookie_manager
        cm.delete(cookie="visited_modules")
        cm.delete(cookie="tutorial_started")
        cm.delete(cookie="tutorial_finished")
        cm.delete(cookie="tutorial_completed")
    
    st.rerun()

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
        
        .stApp {
            background: linear-gradient(135deg, #e0f7fa 0%, #e8eaf6 50%, #f3e5f5 100%) !important;
            height: 100vh;
            overflow: hidden;
        }
        
        .main-wrapper {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            width: 100%;
            text-align: center;
            padding: 20px;
            box-sizing: border-box;
        }
        
        .illustration-box {
            max-width: 400px;
            margin-bottom: 20px;
        }
        
        .illustration-box img {
            width: 100%;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            opacity: 0.9;
        }
        
        .landing-title {
            font-size: 3rem;
            font-weight: 800;
            margin: 10px 0;
            color: #1E1E1E;
            line-height: 1.2;
        }
        
        .landing-subtitle {
            font-size: 1.4rem;
            color: #555;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .landing-description {
            font-size: 1.1rem;
            color: #666;
            max-width: 600px;
            margin-bottom: 30px;
            line-height: 1.5;
        }
        
        .button-group {
            display: flex;
            flex-direction: column;
            gap: 12px;
            width: 300px;
            align-items: center;
        }
        
        /* Styled Start Tutorial Button */
        div.stButton > button:first-child[data-testid="baseButton-primary"] {
            background-color: #008080 !important;
            border-color: #008080 !important;
            color: white !important;
            font-weight: 700 !important;
            height: 50px !important;
            font-size: 1.1rem !important;
            width: 100% !important;
            box-shadow: 0 4px 15px rgba(0,128,128,0.2) !important;
        }
        
        /* Styled Explore Button (Secondary/Outline) */
        div.stButton > button.secondary-btn {
            background-color: transparent !important;
            border: 2px solid #008080 !important;
            color: #008080 !important;
            font-weight: 600 !important;
            height: 50px !important;
            font-size: 1.1rem !important;
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # We use a container to wrap everything for flexbox centering
    st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)
    
    # Illustration
    st.image("lobby_illustration.png", width=400)
    
    # Title & Subtitle
    st.markdown("""
        <div class="landing-title">Welcome to Nurse Rostering System</div>
        <div class="landing-subtitle">Jump in and explore!</div>
        <div class="landing-description">
            Learn how to configure staff, shifts, constraints, 
            and generate optimized nurse schedules.
        </div>
    """, unsafe_allow_html=True)
    
    # Buttons via Streamlit columns for centering the narrow button group
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Tutorial →", key="start_tutorial_btn", use_container_width=True, type="primary"):
            st.session_state.tutorial_active = True
            st.session_state.tutorial_started = True
            st.session_state.show_tutorial_landing = False
            sync_state_to_cookies()
            st.rerun()
            
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        
        if st.button("Explore on Your Own →", key="explore_btn", use_container_width=True):
            st.session_state.show_tutorial_landing = False
            st.session_state.tutorial_active = False
            st.session_state.tutorial_started = True
            sync_state_to_cookies()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

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
    """Renders the sidebar progress bar or certificate button."""
    total = len(TUTORIAL_MODULES)
    visited = len(st.session_state.completed_tutorials)
    
    if st.session_state.tutorial_finished:
        st.markdown("<div style='margin-bottom: 5px; font-weight: bold;'>🏅 Tutorial Certificate</div>", unsafe_allow_html=True)
        if st.sidebar.button("View Certificate", use_container_width=True):
            st.session_state.current_page = "Certificate"
            st.session_state.tutorial_active = False
            st.rerun()
    else:
        # Midway or skip users - show progress bar
        progress_val = int((visited / total) * 10)
        filled = "█" * progress_val
        empty = "░" * (10 - progress_val)
        
        st.markdown(f"""
            <div style='margin-bottom: 5px; font-size: 0.9rem;'>
                <div style='font-weight: bold; margin-bottom: 2px;'>Tutorial Progress</div>
                <div style='margin-bottom: 5px; color: #555;'>{visited} / {total} modules explored</div>
                <div style='font-family: monospace; font-size: 1.2rem; letter-spacing: 2px; color: #1E88E5;'>{filled}{empty}</div>
            </div>
        """, unsafe_allow_html=True)

def render_certificate():
    """Renders the high-quality styled certificate page with completion date and confetti."""
    # Celebration effect
    st.snow() # Streamlit built-in snowflake effect is nice, but balloons are better for a certificate
    st.balloons()
    
    completion_date = st.session_state.get('certificate_earned_date', "Today")
    
    st.markdown(f"""
        <style>
        .cert-container {{
            background-color: white;
            padding: 60px;
            border: 12px solid #D4AF37; /* Gold Border */
            border-style: double;
            text-align: center;
            max-width: 800px;
            margin: 40px auto;
            color: #333;
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
            position: relative;
            font-family: 'Inter', sans-serif;
        }}
        .cert-container::before {{
            content: "🏥";
            position: absolute;
            top: 20px;
            left: 20px;
            font-size: 2.5rem;
            opacity: 0.15;
        }}
        .cert-container::after {{
            content: "⚖️";
            position: absolute;
            bottom: 20px;
            right: 20px;
            font-size: 2.5rem;
            opacity: 0.15;
        }}
        .cert-header {{
            font-family: 'Playfair Display', serif;
            font-size: 3.5rem;
            color: #D4AF37;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 2px;
        }}
        .cert-sub {{
            font-size: 1.6rem;
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
            font-size: 1.3rem;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        .cert-date {{
            margin-top: 40px;
            font-size: 1.2rem;
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
        .stButton > button {{
            max-width: 300px;
            margin: 30px auto !important;
            display: block;
        }}
        </style>
        
        <div class="cert-container">
            <div class="cert-header">CERTIFICATE OF COMPLETION</div>
            <div class="cert-sub">This certificate is proudly presented to</div>
            <div class="cert-name">The User</div>
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
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🎉 Back to System", type="primary", use_container_width=True):
            st.session_state.current_page = "Theme" # Default starting page
            st.rerun()
