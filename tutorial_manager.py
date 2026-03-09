import streamlit as st
import json
import os

# --- Tutorial Content Configuration ---
TUTORIAL_MODULES = [
    {"id": "Manage Departments", "name": "Departments", "icon": "🏢", "color": "#E8F4FD"},
    {"id": "Manage Shifts", "name": "Shifts", "icon": "🗓️", "color": "#FFF4E6"},
    {"id": "Manage Skills", "name": "Skills", "icon": "🔧", "color": "#F3F0FF"},
    {"id": "Grades Hierarchy", "name": "Grades", "icon": "🏆", "color": "#FFF9DB"},
    {"id": "Leave Types", "name": "Leave Types", "icon": "🏖️", "color": "#E6FFFA"},
    {"id": "Manage Staffs", "name": "Staff", "icon": "👥", "color": "#F8F9FA"},
    {"id": "Minimum Demand", "name": "Demand", "icon": "📊", "color": "#FFF5F5"},
    {"id": "Theme", "name": "Theme", "icon": "🎨", "color": "#F0F4F8"},
    {"id": "Hard Constraints", "name": "Hard Constraints", "icon": "🛡️", "color": "#E9ECEF"},
    {"id": "Soft Constraints", "name": "Soft Constraints", "icon": "⚖️", "color": "#FEFBF3"},
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
        .landing-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 70vh;
            text-align: center;
        }
        .landing-title {
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .landing-subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 40px;
            max-width: 600px;
        }
        .landing-buttons {
            display: flex;
            gap: 20px;
        }
        </style>
        <div class="landing-container">
            <div class="landing-title">Welcome to Nurse Roster AI</div>
            <div class="landing-subtitle">
                Supercharge your scheduling. Our AI helper ensures fair, compliant, 
                and efficient rosters in seconds. Ready to see how it works?
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    with col2:
        if st.button("✨ Start Tutorial", use_container_width=True, type="primary"):
            st.session_state.tutorial_active = True
            st.session_state.show_tutorial_landing = False
            st.rerun()
    with col3:
        if st.button("🚀 Explore on Your Own", use_container_width=True):
            st.session_state.show_tutorial_landing = False
            st.session_state.tutorial_active = False
            st.rerun()

def render_tutorial_menu():
    """Renders the grid of tutorial cards."""
    st.header("Pick a Module to Master")
    st.write("Each tutorial takes less than a minute. Complete them all to become a Pro!")

    # Custom CSS for playful cards
    st.markdown("""
        <style>
        .tutorial-card {
            padding: 20px;
            border-radius: 15px;
            border: 2px solid #F0F0F0;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            height: 180px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }
        .tutorial-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.05);
            border-color: #DDD;
        }
        .tutorial-icon {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .tutorial-name {
            font-weight: 700;
            font-size: 1.1rem;
        }
        .tutorial-status {
            font-size: 0.8rem;
            margin-top: 5px;
            color: #4CAF50;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, module in enumerate(TUTORIAL_MODULES):
        with cols[i % 3]:
            is_completed = module['id'] in st.session_state.completed_tutorials
            status_text = "✅ Completed" if is_completed else ""
            
            # Use a container and button combination for interaction
            # We use a button but style the container around it or use the button itself
            if st.button(f"{module['icon']}\n\n{module['name']}\n{status_text}", 
                         key=f"tutorial_card_{module['id']}", 
                         use_container_width=True,
                         help=f"Start {module['name']} Tutorial"):
                st.session_state.current_tutorial_module = module['id']
                st.session_state.current_tutorial_step = 0
                st.session_state.current_page = module['id'] # Switch app page to match
                st.rerun()

    st.markdown("---")
    if len(st.session_state.completed_tutorials) == len(TUTORIAL_MODULES):
        st.success("🏆 You've completed every tutorial module! Ready to build rosters?")
        if st.button("✨ Show Final Summary", use_container_width=True, type="primary"):
            st.session_state.tutorial_finished = True
            st.rerun()
    else:
        if st.button("Finish Tutorial & Start Using App", use_container_width=True, type="primary"):
            st.session_state.tutorial_active = False
            st.rerun()

def render_tutorial_step():
    """Renders the guidance overlay for a specific tutorial step."""
    module_id = st.session_state.current_tutorial_module
    step_idx = st.session_state.current_tutorial_step
    
    if module_id not in TUTORIAL_STEPS:
        st.session_state.current_tutorial_module = None
        st.rerun()
        
    steps = TUTORIAL_STEPS[module_id]
    if step_idx >= len(steps):
        # Module completed
        st.session_state.completed_tutorials.add(module_id)
        st.session_state.current_tutorial_module = None
        st.session_state.current_tutorial_step = 0
        st.success(f"🎉 Awesome! You've mastered {module_id}!")
        if st.button("Back to Tutorial Menu"):
            st.rerun()
        return

    step = steps[step_idx]
    
    # Render the guide card at the top
    with st.container(border=True):
        st.markdown(f"### {step['title']}")
        st.write(step['text'])
        
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            if st.button("⬅️ Back", disabled=(step_idx == 0), use_container_width=True):
                st.session_state.current_tutorial_step -= 1
                st.rerun()
        with c2:
            if st.button("Next ➡️", use_container_width=True, type="primary"):
                st.session_state.current_tutorial_step += 1
                if st.session_state.current_tutorial_step >= len(steps):
                    st.session_state.completed_tutorials.add(module_id)
                st.rerun()
        with c3:
            if st.button("⏭️ Skip Module", use_container_width=True):
                st.session_state.current_tutorial_module = None
                st.rerun()
        with c4:
            if st.button("🏁 Exit Tutorial", use_container_width=True):
                st.session_state.tutorial_active = False
                st.session_state.current_tutorial_module = None
                st.session_state.tutorial_finished = True
                st.rerun()

    # Progress bar
    progress = (step_idx + 1) / len(steps)
    st.progress(progress, text=f"Step {step_idx + 1} of {len(steps)}")
    
    # Visual highlight logic (CSS injection)
    st.markdown(f"""
        <style>
        /* Modern highlight effect */
        [data-testid*="{step['target']}"],
        div:has(> [data-testid*="{step['target']}"]),
        div:has(> label:contains("{step['target']}")) {{
            box-shadow: 0 0 0 2px #FFF, 0 0 0 6px #4ECDC4 !important;
            border-radius: 8px !important;
            z-index: 9999 !important;
            position: relative !important;
            animation: tutorialPulse 1.5s infinite !important;
        }}
        
        @keyframes tutorialPulse {{
            0% {{ box-shadow: 0 0 0 2px #FFF, 0 0 0 4px #4ECDC4; }}
            50% {{ box-shadow: 0 0 0 2px #FFF, 0 0 0 10px #FF6B6B; }}
            100% {{ box-shadow: 0 0 0 2px #FFF, 0 0 0 4px #4ECDC4; }}
        }}
        </style>
    """, unsafe_allow_html=True)

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
        st.rerun()
