import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, time, date, timedelta
import calendar
from model import NurseRosteringModel

st.set_page_config(page_title="Nurse Rostering System", layout="wide")

# ---------------------------------------------------------------------
# Theme Support
# ---------------------------------------------------------------------
if 'theme' not in st.session_state:
    st.session_state.theme = 'Eye Comfort'

THEME_CSS = {
    'Light': '',
    'Dark': '''
    <style>
        .stApp, .main, [data-testid="stAppViewContainer"] {
            background-color: #1E1E2E !important;
            color: #CDD6F4 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #181825 !important;
            color: #CDD6F4 !important;
        }
        [data-testid="stSidebar"] * {
            color: #CDD6F4 !important;
        }
        .stApp header, [data-testid="stHeader"] {
            background-color: #1E1E2E !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stText {
            color: #CDD6F4 !important;
        }
        .stDataFrame, .stTable {
            background-color: #313244 !important;
        }
        [data-testid="stDataFrameResizable"] {
            background-color: #313244 !important;
        }
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stDateInput > div > div > input {
            background-color: #313244 !important;
            color: #CDD6F4 !important;
        }
        .stExpander {
            border-color: #45475A !important;
        }
        [data-testid="stExpander"] details {
            background-color: #181825 !important;
        }
        [data-testid="stExpander"] summary {
            background-color: #181825 !important;
            color: #CDD6F4 !important;
        }
        [data-testid="stExpander"] summary:hover {
            background-color: #313244 !important;
        }
        /* Sidebar secondary buttons */
        [data-testid="stSidebar"] button[kind="secondary"],
        [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
            background-color: #313244 !important;
            color: #CDD6F4 !important;
            border-color: #45475A !important;
        }
        [data-testid="stSidebar"] button[kind="secondary"]:hover,
        [data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
            background-color: #45475A !important;
            border-color: #585B70 !important;
        }
        /* Main area secondary buttons */
        .stApp button[kind="secondary"],
        .stApp .stButton > button:not([kind="primary"]) {
            background-color: #313244 !important;
            color: #CDD6F4 !important;
            border-color: #45475A !important;
        }
        .stApp button[kind="secondary"]:hover,
        .stApp .stButton > button:not([kind="primary"]):hover {
            background-color: #45475A !important;
            border-color: #585B70 !important;
        }
    </style>
    ''',
    'Eye Comfort': '''
    <style>
        .stApp, .main, [data-testid="stAppViewContainer"] {
            background-color: #FDF6E3 !important;
            color: #5C5040 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #F5EDDA !important;
            color: #5C5040 !important;
        }
        [data-testid="stSidebar"] * {
            color: #5C5040 !important;
        }
        .stApp header, [data-testid="stHeader"] {
            background-color: #FDF6E3 !important;
        }
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stText {
            color: #5C5040 !important;
        }
        .stDataFrame, .stTable {
            background-color: #F5EDDA !important;
        }
        [data-testid="stDataFrameResizable"] {
            background-color: #F5EDDA !important;
        }
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stDateInput > div > div > input {
            background-color: #FEFBF3 !important;
            color: #5C5040 !important;
        }
        .stExpander {
            border-color: #E0D6C3 !important;
        }
        [data-testid="stExpander"] details {
            background-color: #F5EDDA !important;
        }
        [data-testid="stExpander"] summary {
            background-color: #F5EDDA !important;
            color: #5C5040 !important;
        }
        [data-testid="stExpander"] summary:hover {
            background-color: #EDE5D2 !important;
        }
        /* Sidebar secondary buttons */
        [data-testid="stSidebar"] button[kind="secondary"],
        [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
            background-color: #FEFBF3 !important;
            color: #5C5040 !important;
            border-color: #E0D6C3 !important;
        }
        [data-testid="stSidebar"] button[kind="secondary"]:hover,
        [data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
            background-color: #EDE5D2 !important;
            border-color: #D4C9B4 !important;
        }
        /* Main area secondary buttons */
        .stApp button[kind="secondary"],
        .stApp .stButton > button:not([kind="primary"]) {
            background-color: #FEFBF3 !important;
            color: #5C5040 !important;
            border-color: #E0D6C3 !important;
        }
        .stApp button[kind="secondary"]:hover,
        .stApp .stButton > button:not([kind="primary"]):hover {
            background-color: #EDE5D2 !important;
            border-color: #D4C9B4 !important;
        }
    </style>
    '''
}

st.markdown(THEME_CSS.get(st.session_state.theme, ''), unsafe_allow_html=True)

NURSE_DATA_FILE = "nurses.json"
SHIFTS_DATA_FILE = "shifts.json"
SKILLS_DATA_FILE = "skills.json"
DEMAND_DATA_FILE = "demand.json"
GRADES_DATA_FILE = "grades.json"
LEAVES_DATA_FILE = "leaves.json"

def load_data(file_path, default_data):
    """Load data from JSON file or return default."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
    return default_data

def save_data(file_path, data):
    """Save data to JSON file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Error saving {file_path}: {e}")

# Default Shifts
DEFAULT_SHIFTS = [
    {"code": "M", "name": "Morning", "start": "07:00", "end": "14:00", "duration": 480, "type": "Day", "color": "#CCE5FF"},
    {"code": "E", "name": "Evening", "start": "14:00", "end": "22:00", "duration": 480, "type": "Day", "color": "#FFD699"},
    {"code": "N", "name": "Night", "start": "21:00", "end": "07:30", "duration": 600, "type": "Night", "color": "#E5CCFF"}
]

# Default Skills
DEFAULT_SKILLS = [
    {"code": "BLS", "name": "Basic Life Support", "description": "CPR, AED use, and basic emergency response."},
    {"code": "ACLS", "name": "Advanced Cardiac Life Support", "description": "Advanced treatment for cardiac emergencies."},
    {"code": "IVT", "name": "Intravenous Therapy", "description": "Inserting and managing IV lines."},
    {"code": "WDC", "name": "Wound Care", "description": "Cleaning, dressing, and monitoring wounds."},
    {"code": "MED", "name": "General Medicine", "description": "General medical ward care"},
    {"code": "SUR", "name": "Surgical", "description": "Surgical unit experience"},
    {"code": "CAR", "name": "Cardiology", "description": "Cardiology department"},
    {"code": "NEU", "name": "Neurology", "description": "Neurology department"}
]

st.title("Nurse Rostering System")

# Calculate planning horizon from user-selected date range
today = date.today()
_, num_days_in_month = calendar.monthrange(today.year, today.month)

if 'roster_start_date' not in st.session_state:
    st.session_state.roster_start_date = today
if 'roster_end_date' not in st.session_state:
    st.session_state.roster_end_date = date(today.year, today.month, num_days_in_month)

roster_start = st.session_state.roster_start_date
roster_end = st.session_state.roster_end_date
planning_horizon = (roster_end - roster_start).days + 1

# Generate date labels for the columns (e.g., "Mon, Mar 01")
date_labels = [(roster_start + timedelta(days=d)).strftime("%a, %b %d") for d in range(planning_horizon)]

# ---------------------------------------------------------------------
# Data Initialization
# ---------------------------------------------------------------------
if 'shifts' not in st.session_state:
    st.session_state.shifts = load_data(SHIFTS_DATA_FILE, DEFAULT_SHIFTS)
    for s in st.session_state.shifts:
        if 'color' not in s:
            s['color'] = "#E0E0E0"
        if 'required_skills' not in s:
            s['required_skills'] = []

if 'skills' not in st.session_state:
    st.session_state.skills = load_data(SKILLS_DATA_FILE, DEFAULT_SKILLS)

if 'nurses' not in st.session_state:
    st.session_state.nurses = load_data(NURSE_DATA_FILE, [
        {'id': f'N{i+1:03}', 'name': f'Nurse {i+1}', 'grade': 'RN', 'leave_days': [], 'skills': []} for i in range(10)
    ])

if 'grades' not in st.session_state:
    # Hierarchy is a list of layers, from top (senior) to bottom (junior)
    # Each layer is a list of grade objects: {"code": "SN", "name": "Staff Nurse"}
    raw_grades = load_data(GRADES_DATA_FILE, [
        [{"code": "SN", "name": "Sister"}],
        [{"code": "RN", "name": "Registered Nurse"}],
        [{"code": "EN", "name": "Enrolled Nurse"}],
        [{"code": "NA", "name": "Nursing Assistant"}]
    ])
    
    # Robust check: if it's a flat list, convert each item to its own layer
    if raw_grades and isinstance(raw_grades, list) and len(raw_grades) > 0 and isinstance(raw_grades[0], dict):
        st.session_state.grades = [[g] for g in raw_grades]
    else:
        st.session_state.grades = raw_grades

if 'leaves' not in st.session_state:
    DEFAULT_LEAVES = [
        {"code": "AL", "name": "Annual Leave", "description": "Paid annual vacation", "color": "#E6FFFA", "is_paid": True},
        {"code": "SL", "name": "Sick Leave", "description": "Paid sick leave", "color": "#FFF5F5", "is_paid": True},
        {"code": "UL", "name": "Unpaid Leave", "description": "Unpaid leave of absence", "color": "#F7FAFC", "is_paid": False}
    ]
    st.session_state.leaves = load_data(LEAVES_DATA_FILE, DEFAULT_LEAVES)

if 'demand' not in st.session_state:
    # Default demand: { 'default': { 'shift_code': { 'skill_code': min_count, 'Total': min_count } }, 'overrides': { 'YYYY-MM-DD': { ... } } }
    st.session_state.demand = load_data(DEMAND_DATA_FILE, {
        "default": {},
        "overrides": {}
    })
    # Pre-populate default demand if empty
    if not st.session_state.demand["default"]:
        for s in st.session_state.shifts:
            if s['code'] == 'M': total = 2
            elif s['code'] == 'E': total = 2
            else: total = 1
            st.session_state.demand["default"][s['code']] = {"Total": total}

# ---------------------------------------------------------------------
# Dialog Modals
# ---------------------------------------------------------------------

def render_manage_shifts():
    # --- Success Message Handling ---
    if 'shift_success_msg' in st.session_state and st.session_state.shift_success_msg:
        st.success(st.session_state.shift_success_msg)
        st.session_state.shift_success_msg = None # Clear after showing

    # --- Custom Styling for Shift Cards ---
    st.markdown("""
    <style>
    .shift-card {
        padding: 15px;
        margin-bottom: 12px;
        border-radius: 12px;
        border: 2px solid #EEE;
        background: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .shift-card:hover {
        border-color: #DDE;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }
    .shift-info {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .shift-code {
        font-family: monospace;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 6px;
        color: white;
        min-width: 60px;
        text-align: center;
    }
    .shift-details {
        display: flex;
        flex-direction: column;
    }
    .shift-name {
        font-weight: 600;
        color: #333;
    }
    .shift-time {
        font-size: 0.85rem;
        color: #666;
    }
    .shift-actions {
        display: flex;
        gap: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    hours = [f"{i:02d}" for i in range(24)]
    minutes = ["00", "15", "30", "45"]

    st.write("Add new shift types according to the hospital's operating requirements.")
    with st.expander("Add New Shift", expanded=False):
        with st.form("add_shift_form", clear_on_submit=True):
            new_shift_code = st.text_input("Code (e.g., D1)", max_chars=5)
            new_shift_name = st.text_input("Name")
            new_shift_type = st.selectbox("Type", ["Day", "Night"])
            
            st.write("**Shift Time**")
            col_s_h, col_s_m, col_arrow, col_e_h, col_e_m = st.columns([2, 2, 1, 2, 2])
            
            with col_s_h:
                new_s_h = st.selectbox("Start Hour", hours, index=7)
            with col_s_m:
                new_s_m = st.selectbox("Start Min", minutes, index=0)
            with col_arrow:
                st.markdown("<div style='text-align: center; padding-top: 30px;'>➡️</div>", unsafe_allow_html=True)
            with col_e_h:
                new_e_h = st.selectbox("End Hour", hours, index=15)
            with col_e_m:
                new_e_m = st.selectbox("End Min", minutes, index=0)
                
            new_shift_color = st.color_picker("Color", "#E0E0E0")
            
            if st.form_submit_button("Add Shift", use_container_width=True):
                if new_shift_code and new_shift_name:
                    if any(s['code'] == new_shift_code for s in st.session_state.shifts):
                        st.error("Shift code already exists!")
                    else:
                        s_time = f"{new_s_h}:{new_s_m}"
                        e_time = f"{new_e_h}:{new_e_m}"
                        
                        start_dt = datetime.strptime(s_time, "%H:%M")
                        end_dt = datetime.strptime(e_time, "%H:%M")
                        if end_dt <= start_dt:
                            end_dt = end_dt + timedelta(days=1)
                        duration_mins = int((end_dt - start_dt).total_seconds() / 60)
                        
                        new_shift = {
                            "code": new_shift_code,
                            "name": new_shift_name,
                            "type": new_shift_type,
                            "start": s_time,
                            "end": e_time,
                            "duration": duration_mins,
                            "color": new_shift_color,
                            "id": f"{new_shift_code}_{datetime.now().timestamp()}" # Stable unique ID
                        }
                        st.session_state.shifts.append(new_shift)
                        # Automatic Sort by Start Time
                        st.session_state.shifts.sort(key=lambda x: x.get('start', '00:00'))
                        save_data(SHIFTS_DATA_FILE, st.session_state.shifts)
                        
                        # Set success message for next run
                        st.session_state.shift_success_msg = f"Successfully added shift: {new_shift_code}"
                        st.rerun()
                else:
                    st.warning("Code and Name required.")

    st.markdown("---")
    st.subheader("Available Shifts")

    # Track which shift is being edited
    if 'editing_shift_id' not in st.session_state:
        st.session_state.editing_shift_id = None
    
    for i, s in enumerate(st.session_state.shifts):
        if 'id' not in s:
            s['id'] = f"{s['code']}_{i}"
        
        stable_key = s['id']
        
        # --- Render Shift Card with Side-by-Side Buttons ---
        with st.container():
            # Use columns to ensure buttons are strictly alongside the info
            card_cols = st.columns([8, 0.8, 0.8])
            
            with card_cols[0]:
                st.markdown(f"""
                <div class="shift-card" style="margin-bottom: 0; border: none; box-shadow: none; padding: 0;">
                    <div class="shift-info">
                        <div class="shift-code" style="background-color: {s.get('color', '#E0E0E0')}66; border: 2px solid {s.get('color', '#E0E0E0')}; color: #333">
                            {s['code']}
                        </div>
                        <div class="shift-details">
                            <span class="shift-name">{s['name']}</span>
                            <span class="shift-time">🕒 {s.get('start', '??')} - {s.get('end', '??')} ({s.get('duration', '0')} mins)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with card_cols[1]:
                # Vertical centering hack for Streamlit buttons
                st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                if st.button("✏️", key=f"edit_btn_{stable_key}", help="Edit Shift", use_container_width=True):
                    st.session_state.editing_shift_id = s['id']
            with card_cols[2]:
                st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_btn_{stable_key}", help="Delete Shift", use_container_width=True):
                    st.session_state.shifts.pop(i)
                    save_data(SHIFTS_DATA_FILE, st.session_state.shifts)
                    st.rerun()
            
            # Sub-card styling for the whole container
            st.markdown("<hr style='margin: 8px 0; border: 0; border-top: 1px solid #EEE;'>", unsafe_allow_html=True)

        # --- Render Edit Form if active ---
        if st.session_state.editing_shift_id == s['id']:
            with st.form(key=f"edit_form_{stable_key}"):
                st.write(f"### Edit Shift: {s['code']}")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    edit_code = st.text_input("Code", value=s['code'], max_chars=5)
                with col2:
                    edit_name = st.text_input("Name", value=s['name'])
                with col3:
                    type_options = ["Day", "Night"]
                    edit_type = st.selectbox("Type", type_options, index=type_options.index(s['type']) if s['type'] in type_options else 0)
                
                st.write("**Time & Color**")
                col_s_h, col_s_m, col_arrow, col_e_h, col_e_m = st.columns([2, 2, 1, 2, 2])
                s_parts = s.get('start', '07:00').split(':')
                e_parts = s.get('end', '15:00').split(':')
                
                with col_s_h:
                    e_s_h = st.selectbox("Start Hour", hours, index=int(s_parts[0]))
                with col_s_m:
                    curr_min = s_parts[1] if s_parts[1] in minutes else "00"
                    e_s_m = st.selectbox("Start Min", minutes, index=minutes.index(curr_min))
                with col_arrow:
                    st.markdown("<div style='text-align: center; padding-top: 30px;'>➡️</div>", unsafe_allow_html=True)
                with col_e_h:
                    e_e_h = st.selectbox("End Hour", hours, index=int(e_parts[0]))
                with col_e_m:
                    curr_min_e = e_parts[1] if e_parts[1] in minutes else "00"
                    e_e_m = st.selectbox("End Min", minutes, index=minutes.index(curr_min_e))
                
                edit_color = st.color_picker("Color", s.get('color', '#E0E0E0'))
                
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    if st.form_submit_button("✅ Save Changes", use_container_width=True):
                        s_time = f"{e_s_h}:{e_s_m}"
                        e_time = f"{e_e_h}:{e_e_m}"
                        start_dt = datetime.strptime(s_time, "%H:%M")
                        end_dt = datetime.strptime(e_time, "%H:%M")
                        if end_dt <= start_dt:
                            end_dt = end_dt + timedelta(days=1)
                        
                        s['code'] = edit_code
                        s['name'] = edit_name
                        s['type'] = edit_type
                        s['start'] = s_time
                        s['end'] = e_time
                        s['duration'] = int((end_dt - start_dt).total_seconds() / 60)
                        s['color'] = edit_color
                        
                        # Automatic Sort by Start Time
                        st.session_state.shifts.sort(key=lambda x: x.get('start', '00:00'))
                        save_data(SHIFTS_DATA_FILE, st.session_state.shifts)
                        st.session_state.editing_shift_id = None
                        st.session_state.shift_success_msg = f"Successfully updated shift: {s['code']}"
                        st.rerun()
                with f_col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.editing_shift_id = None
                        st.rerun()
            st.markdown("---")

def render_manage_grades():
    st.subheader("Grades Hierarchy")
    st.write("Higher layers represent more senior grades. Seniors can cover junior shifts.")

    # --- Visual Pyramid Representation ---
    st.markdown("""
    <style>
    .pyramid-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        margin: 20px 0;
    }
    .pyramid-layer {
        padding: 15px;
        text-align: center;
        border-radius: 8px;
        background: #FEFBF3;
        border: 2px solid #E0D6C3;
        color: #5C5040;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .pyramid-layer:hover {
        transform: scale(1.02);
        border-color: #D4C9B4;
    }
    .grade-badge {
        display: inline-block;
        background: #FDF6E3;
        border: 1px solid #D4C9B4;
        padding: 2px 8px;
        border-radius: 4px;
        margin: 2px;
        font-weight: bold;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="pyramid-container">', unsafe_allow_html=True)
        for i, layer in enumerate(st.session_state.grades):
            # Calculate width based on layer index (top is narrowest)
            width = 40 + (i * 15)
            grades_html = " ".join([f'<span class="grade-badge">{g["code"]}</span>' for g in layer])
            st.markdown(f'<div class="pyramid-layer" style="width: {width}%; font-size: {1.2 + (i*0.1)}rem;">'
                        f'<strong>Level {i+1}</strong><br>{grades_html}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- Management UI ---
    col_add, col_rem = st.columns(2)
    with col_add:
        if st.button("➕ Add Layer to Bottom", use_container_width=True):
            st.session_state.grades.append([])
            save_data(GRADES_DATA_FILE, st.session_state.grades)
            st.rerun()
    with col_rem:
        if len(st.session_state.grades) > 1:
            if st.button("➖ Remove Bottom Layer", use_container_width=True):
                # Move grades from bottom layer to the one above before deleting if needed? 
                # For now just delete if empty or warning.
                if not st.session_state.grades[-1] or st.button("Confirm Delete Non-Empty Layer"):
                    st.session_state.grades.pop()
                    save_data(GRADES_DATA_FILE, st.session_state.grades)
                    st.rerun()

    st.subheader("Edit Layers")
    for i, layer in enumerate(st.session_state.grades):
        with st.expander(f"Level {i+1} Management", expanded=(i==0)):
            # Add Grade to this layer
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                new_g_code = st.text_input("Code", key=f"new_g_code_{i}", max_chars=5)
            with col2:
                new_g_name = st.text_input("Full Name", key=f"new_g_name_{i}")
            with col3:
                st.write("") # Spacer
                st.write("") # Spacer
                if st.button("Add Grade", key=f"add_g_btn_{i}", use_container_width=True):
                    if new_g_code and new_g_name:
                        st.session_state.grades[i].append({"code": new_g_code, "name": new_g_name})
                        save_data(GRADES_DATA_FILE, st.session_state.grades)
                        st.rerun()
            
            # Current Grades in this layer
            if layer:
                st.write("Current Grades:")
                for j, grade in enumerate(layer):
                    c1, c2, c3 = st.columns([1, 3, 1])
                    c1.code(grade['code'])
                    c2.write(grade['name'])
                    if c3.button("🗑️", key=f"del_g_{i}_{j}"):
                        st.session_state.grades[i].pop(j)
                        save_data(GRADES_DATA_FILE, st.session_state.grades)
                        st.rerun()

            # Move layer up/down
            m1, m2 = st.columns(2)
            if i > 0:
                if m1.button(f"⬆️ Move Level {i+1} Up", key=f"up_layer_{i}"):
                    st.session_state.grades[i-1], st.session_state.grades[i] = st.session_state.grades[i], st.session_state.grades[i-1]
                    save_data(GRADES_DATA_FILE, st.session_state.grades)
                    st.rerun()
            if i < len(st.session_state.grades) - 1:
                if m2.button(f"⬇️ Move Level {i+1} Down", key=f"down_layer_{i}"):
                    st.session_state.grades[i], st.session_state.grades[i+1] = st.session_state.grades[i+1], st.session_state.grades[i]
                    save_data(GRADES_DATA_FILE, st.session_state.grades)
                    st.rerun()

def render_manage_leave_types():
    # --- Success Message Handling ---
    if 'leave_success_msg' in st.session_state and st.session_state.leave_success_msg:
        st.success(st.session_state.leave_success_msg)
        st.session_state.leave_success_msg = None

    with st.expander("Add New Leave Type", expanded=False):
        with st.form("add_leave_form", clear_on_submit=True):
            col_code, col_name, col_paid = st.columns([1, 2, 1])
            with col_code:
                new_code = st.text_input("Code (e.g., ML)", max_chars=5)
            with col_name:
                new_name = st.text_input("Leave Name")
            with col_paid:
                st.write("") # Spacer
                st.write("") # Spacer
                new_is_paid = st.checkbox("Paid Leave", value=True)
                
            new_desc = st.text_input("Description")
            new_color = st.color_picker("Color", "#E0E0E0")
            
            if st.form_submit_button("Add Leave Type", use_container_width=True):
                if new_code and new_name:
                    if any(l['code'] == new_code for l in st.session_state.leaves):
                        st.error("Leave code already exists!")
                    else:
                        st.session_state.leaves.append({
                            "code": new_code,
                            "name": new_name,
                            "description": new_desc,
                            "color": new_color,
                            "is_paid": new_is_paid
                        })
                        save_data(LEAVES_DATA_FILE, st.session_state.leaves)
                        st.success(f"Added leave type: {new_code}")
                        st.rerun()
                else:
                    st.warning("Code and Name are required.")

    st.markdown("---")
    st.subheader("Current Leave Types")
    
    for i, leave in enumerate(st.session_state.leaves):
        with st.expander(f"[{leave['code']}] {leave['name']}", expanded=False):
            col_code, col_name, col_paid = st.columns([1, 2, 1])
            updated = False
            
            with col_code:
                edit_code = st.text_input("Code", value=leave.get('code', ''), max_chars=5, key=f"leave_code_{i}")
                if edit_code != leave.get('code'):
                    leave['code'] = edit_code
                    updated = True
                    
            with col_name:
                edit_name = st.text_input("Name", value=leave.get('name', ''), key=f"leave_name_{i}")
                if edit_name != leave.get('name'):
                    leave['name'] = edit_name
                    updated = True
                    
            with col_paid:
                st.write("") # Spacer
                st.write("") # Spacer
                edit_paid = st.checkbox("Paid Leave", value=leave.get('is_paid', True), key=f"leave_paid_{i}")
                if edit_paid != leave.get('is_paid'):
                    leave['is_paid'] = edit_paid
                    updated = True
                    
            edit_desc = st.text_input("Description", value=leave.get('description', ''), key=f"leave_desc_{i}")
            if edit_desc != leave.get('description'):
                leave['description'] = edit_desc
                updated = True
                
            edit_color = st.color_picker("Color", value=leave.get('color', '#E0E0E0'), key=f"leave_color_{i}")
            if edit_color != leave.get('color'):
                leave['color'] = edit_color
                updated = True
                
            col_save, col_del = st.columns(2)
            with col_save:
                if updated:
                    if st.button("Save Changes", key=f"save_leave_{i}", use_container_width=True):
                        save_data(LEAVES_DATA_FILE, st.session_state.leaves)
                        st.session_state.leave_success_msg = f"Changes for '{leave['name']}' saved successfully."
                        st.rerun()
            with col_del:
                if st.button("Delete Type", key=f"del_leave_{i}", type="primary", use_container_width=True):
                    st.session_state.leaves.pop(i)
                    save_data(LEAVES_DATA_FILE, st.session_state.leaves)
                    st.rerun()

def render_manage_staffs():
    # --- Success Message Handling ---
    if 'staff_success_msg' in st.session_state and st.session_state.staff_success_msg:
        st.success(st.session_state.staff_success_msg)
        st.session_state.staff_success_msg = None

    with st.expander("Add New Nurse", expanded=False):
        col_id, col_name, col_grade, col_btn = st.columns([1, 2, 2, 1])
        with col_id:
            new_nurse_id = st.text_input("Nurse ID", key="new_nurse_id", placeholder="e.g. N001")
        with col_name:
            new_nurse_name = st.text_input("Nurse Name", key="new_nurse_name")
        with col_grade:
            all_grades = [g['code'] for layer in st.session_state.grades for g in layer]
            new_nurse_grade = st.selectbox("Grade", all_grades if all_grades else ["RN"], key="new_nurse_grade")
        with col_btn:
            st.write("") # Spacer
            st.write("") # Spacer
            if st.button("Add", use_container_width=True):
                if new_nurse_name and new_nurse_id:
                    new_nurse = {
                        'id': new_nurse_id,
                        'name': new_nurse_name, 
                        'grade': new_nurse_grade, 
                        'leave_days': [],
                        'skills': []
                    }
                    st.session_state.nurses.append(new_nurse)
                    save_data(NURSE_DATA_FILE, st.session_state.nurses)
                    st.success(f"Added {new_nurse_name}")
                    st.rerun()
                else:
                    st.warning("Please enter ID and name.")

    st.markdown("---")
    st.subheader("Current Nurses")

    for i, nurse in enumerate(st.session_state.nurses):
        if 'grade' not in nurse:
            nurse['grade'] = nurse.get('role', 'RN')
        if 'id' not in nurse:
            nurse['id'] = f"N{i+1:03}"
            
        with st.expander(f"[{nurse['id']}] {nurse['name']} ({nurse['grade']}) - Leaves: {nurse['leave_days']}"):
            col_id, col_name, col_grade, col_action = st.columns([1, 2, 1, 1])
            updated = False
            
            with col_id:
                new_id = st.text_input(f"ID", value=nurse['id'], key=f"id_{i}")
                if new_id != nurse['id']:
                    nurse['id'] = new_id
                    updated = True

            with col_name:
                new_name = st.text_input(f"Name", value=nurse['name'], key=f"name_{i}")
                if new_name != nurse['name']:
                    nurse['name'] = new_name
                    updated = True
                
            with col_grade:
                all_grades = [g['code'] for layer in st.session_state.grades for g in layer]
                if not all_grades: all_grades = ["RN"]
                current_index = all_grades.index(nurse['grade']) if nurse['grade'] in all_grades else 0
                new_grade = st.selectbox("Grade", all_grades, index=current_index, key=f"grade_{i}")
                if new_grade != nurse['grade']:
                    nurse['grade'] = new_grade
                    updated = True

            col_leaves, col_reqs, col_skills = st.columns([2, 2, 2])
            with col_leaves:
                leaves_str = ",".join(map(str, nurse['leave_days']))
                new_leaves_str = st.text_input(
                    f"Leave Days", 
                    value=leaves_str, 
                    key=f"leaves_{i}",
                    help="Comma-separated day numbers"
                )
                try:
                    if new_leaves_str.strip():
                        leaves_list = [int(x.strip()) for x in new_leaves_str.split(',') if x.strip().isdigit()]
                        valid_leaves = [d for d in leaves_list if 0 <= d < planning_horizon]
                        if valid_leaves != nurse['leave_days']:
                            nurse['leave_days'] = valid_leaves
                            updated = True
                    elif nurse['leave_days']:
                        nurse['leave_days'] = []
                        updated = True
                except ValueError:
                    st.error("Invalid leave format.")

            with col_reqs:
                current_requests = nurse.get('must_have_shifts', [])
                req_str = ", ".join([f"{r['day']}:{r['shift']}" for r in current_requests])
                new_req_str = st.text_input("Requests (Day:Shift)", value=req_str, key=f"reqs_{i}")
                # ... same parsing logic as before ...
                try:
                    parsed_reqs = []
                    if new_req_str.strip():
                        parts = new_req_str.split(',')
                        for p in parts:
                            if ':' in p:
                                d_str, s_str = p.split(':')
                                d = int(d_str.strip())
                                s = s_str.strip()
                                valid_shifts = [sh['code'] for sh in st.session_state.shifts]
                                if 0 <= d < planning_horizon and s in valid_shifts:
                                    parsed_reqs.append({'day': d, 'shift': s})
                    parsed_reqs.sort(key=lambda x: x['day'])
                    current_sorted = sorted(current_requests, key=lambda x: x['day']) if current_requests else []
                    if parsed_reqs != current_sorted:
                        nurse['must_have_shifts'] = parsed_reqs
                        updated = True
                except ValueError: pass

            with col_skills:
                skill_options = [f"{skill['code']} - {skill['name']}" for skill in st.session_state.skills]
                current_nurse_skills = nurse.get('skills', [])
                current_skill_options = [f"{skill['code']} - {skill['name']}" for skill in st.session_state.skills if skill['code'] in current_nurse_skills]
                edit_nurse_skills = st.multiselect("Skills", options=skill_options, default=current_skill_options, key=f"nurse_skills_{i}")
                edit_nurse_skills_codes = [skill.split(' - ')[0] for skill in edit_nurse_skills]
                if edit_nurse_skills_codes != current_nurse_skills:
                    nurse['skills'] = edit_nurse_skills_codes
                    updated = True

            if st.button("Delete Nurse", key=f"delete_{i}", type="primary", use_container_width=True):
                st.session_state.nurses.pop(i)
                save_data(NURSE_DATA_FILE, st.session_state.nurses)
                st.rerun()
            
            if updated:
                if st.button("Save Changes", key=f"save_nurse_{i}", use_container_width=True):
                    save_data(NURSE_DATA_FILE, st.session_state.nurses)
                    st.session_state.staff_success_msg = f"Changes saved for {nurse['name']}."
                    st.rerun()

def render_manage_skills():
    # --- Success Message Handling ---
    if 'skill_success_msg' in st.session_state and st.session_state.skill_success_msg:
        st.success(st.session_state.skill_success_msg)
        st.session_state.skill_success_msg = None 

    # --- Custom Styling for Skill Cards ---
    st.markdown("""
    <style>
    .skill-card {
        padding: 15px;
        margin-bottom: 12px;
        border-radius: 12px;
        border: 2px solid #EEE;
        background: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .skill-card:hover {
        border-color: #DDE;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }
    .skill-info {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .skill-code {
        font-family: monospace;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 6px;
        background-color: #F0F4F8;
        border: 2px solid #D1D9E0;
        color: #333;
        min-width: 60px;
        text-align: center;
    }
    .skill-details {
        display: flex;
        flex-direction: column;
    }
    .skill-name {
        font-weight: 600;
        color: #333;
    }
    .skill-desc {
        font-size: 0.85rem;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

    st.write("Add new nursing skills and specializations to the system.")
    with st.expander("Add New Skill", expanded=False):
        with st.form("add_skill_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 3])
            with col1:
                new_skill_code = st.text_input("Code", max_chars=5, help="e.g., ICU, ER")
            with col2:
                new_skill_name = st.text_input("Name", help="e.g., ICU Care")
            
            new_skill_desc = st.text_area("Description", help="Brief description")

            if st.form_submit_button("Add Skill", use_container_width=True):
                if new_skill_code and new_skill_name:
                    if any(s['code'] == new_skill_code for s in st.session_state.skills):
                        st.error("Skill code already exists!")
                    else:
                        new_skill = {
                            "code": new_skill_code,
                            "name": new_skill_name,
                            "description": new_skill_desc if new_skill_desc else "",
                            "id": f"skill_{new_skill_code}_{datetime.now().timestamp()}"
                        }
                        st.session_state.skills.append(new_skill)
                        save_data(SKILLS_DATA_FILE, st.session_state.skills)
                        st.session_state.skill_success_msg = f"Successfully added skill: {new_skill_code}"
                        st.rerun()
                else:
                    st.warning("Code and Name are required.")

    st.markdown("---")
    st.subheader("Available Skills")

    if 'editing_skill_id' not in st.session_state:
        st.session_state.editing_skill_id = None

    if not st.session_state.skills:
        st.info("No skills defined yet. Add your first skill above.")
    else:
        for i, skill in enumerate(st.session_state.skills):
            if 'id' not in skill:
                skill['id'] = f"skill_{skill['code']}_{i}"
            
            stable_key = skill['id']

            # --- Render Skill Card ---
            with st.container():
                card_cols = st.columns([8, 0.8, 0.8])
                
                with card_cols[0]:
                    st.markdown(f"""
                    <div class="skill-card" style="margin-bottom: 0; border: none; box-shadow: none; padding: 0;">
                        <div class="skill-info">
                            <div class="skill-code">
                                {skill['code']}
                            </div>
                            <div class="skill-details">
                                <span class="skill-name">{skill['name']}</span>
                                <span class="skill-desc">{skill.get('description', '')}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with card_cols[1]:
                    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("✏️", key=f"edit_skill_{stable_key}", help="Edit Skill"):
                        st.session_state.editing_skill_id = skill['id']
                
                with card_cols[2]:
                    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_skill_{stable_key}", help="Delete Skill"):
                        st.session_state.skills.pop(i)
                        save_data(SKILLS_DATA_FILE, st.session_state.skills)
                        st.rerun()

            # --- Inline Edit Form ---
            if st.session_state.editing_skill_id == skill['id']:
                with st.form(f"edit_skill_form_{stable_key}"):
                    st.write(f"**Edit Skill: {skill['code']}**")
                    e_col1, e_col2 = st.columns([1, 2])
                    edit_code = e_col1.text_input("Code", value=skill['code'], max_chars=5)
                    edit_name = e_col2.text_input("Name", value=skill['name'])
                    edit_desc = st.text_area("Description", value=skill.get('description', ''))
                    
                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        if st.form_submit_button("✅ Save Changes", use_container_width=True):
                            if edit_code != skill['code'] and any(s['code'] == edit_code for s in st.session_state.skills):
                                st.error("Skill code already exists!")
                            else:
                                skill['code'] = edit_code
                                skill['name'] = edit_name
                                skill['description'] = edit_desc
                                save_data(SKILLS_DATA_FILE, st.session_state.skills)
                                st.session_state.editing_skill_id = None
                                st.session_state.skill_success_msg = f"Successfully updated skill: {edit_code}"
                                st.rerun()
                    with f_col2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state.editing_skill_id = None
                            st.rerun()
                st.markdown("---")

def render_manage_demand():
    st.subheader("Daily Minimum Coverage")
    st.write("Specify the requirements for each shift and skill.")

    tab1, tab2 = st.tabs(["Default Demand", "Date-Specific Overrides"])

    with tab1:
        st.info("Set the **standard** requirements for each shift.")
        
        for s in st.session_state.shifts:
            with st.expander(f"Shift: {s['code']} - {s['name']}", expanded=True):
                shift_code = s['code']
                if shift_code not in st.session_state.demand["default"]:
                    st.session_state.demand["default"][shift_code] = {"Total": 1}
                
                # Total requirement
                col_t1, col_t2 = st.columns([2, 1])
                with col_t1:
                    current_total = st.session_state.demand["default"][shift_code].get("Total", 1)
                    new_total = st.number_input(f"Minimum Total Nurses", min_value=1, value=current_total, key=f"def_total_{shift_code}")
                    st.session_state.demand["default"][shift_code]["Total"] = new_total
                with col_t2:
                    all_grades = [g['code'] for layer in st.session_state.grades for g in layer]
                    current_grade = st.session_state.demand["default"][shift_code].get("Grade", all_grades[-1] if all_grades else "RN")
                    grade_idx = all_grades.index(current_grade) if current_grade in all_grades else (len(all_grades)-1 if all_grades else 0)
                    new_grade = st.selectbox("Min Grade", all_grades, index=grade_idx, key=f"def_grade_{shift_code}", help="Nurses must be this grade or higher")
                    st.session_state.demand["default"][shift_code]["Grade"] = new_grade

                # Skills section
                st.write("**Specific Skill Requirements**")
                
                # Filter out 'Total' to get only skills
                current_skills_req = {k: v for k, v in st.session_state.demand["default"][shift_code].items() if k != "Total"}
                
                if current_skills_req:
                    # Create a list for editing
                    skill_list = []
                    for k, v in current_skills_req.items():
                        skill_list.append({"Skill": k, "Min Count": v})
                    
                    df_skills = pd.DataFrame(skill_list)
                    edited_skills = st.data_editor(
                        df_skills,
                        num_rows="dynamic",
                        key=f"def_skills_editor_{shift_code}",
                        column_config={
                            "Skill": st.column_config.SelectboxColumn(
                                "Skill",
                                options=[sk['code'] for sk in st.session_state.skills],
                                required=True
                            ),
                            "Min Count": st.column_config.NumberColumn(
                                "Min Count",
                                min_value=1,
                                max_value=new_total,
                                default=1,
                                required=True
                            )
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Update state based on edited DF
                    new_skill_dict = {"Total": new_total}
                    for _, row in edited_skills.iterrows():
                        if pd.notna(row['Skill']):
                            # Clamp min count to total
                            count = min(int(row['Min Count']), new_total)
                            new_skill_dict[row['Skill']] = count
                    st.session_state.demand["default"][shift_code] = new_skill_dict
                else:
                    if st.button(f"Add Skill Requirement...", key=f"add_skill_btn_{shift_code}"):
                        st.session_state.demand["default"][shift_code][st.session_state.skills[0]['code']] = 1
                        st.rerun()

        if st.button("Save Default Demand", type="primary"):
            save_data(DEMAND_DATA_FILE, st.session_state.demand)
            st.success("Default demand saved!")

    with tab2:
        st.write("Modify requirements for **specific dates**.")
        target_date = st.date_input("Select Date", value=st.session_state.roster_start_date, min_value=st.session_state.roster_start_date, max_value=st.session_state.roster_end_date)
        date_str = target_date.strftime("%Y-%m-%d")

        # Load current override or copy from default if new
        if st.button("Create/Edit Override for this Date", key="btn_create_ov"):
            if date_str not in st.session_state.demand["overrides"]:
                st.session_state.demand["overrides"][date_str] = json.loads(json.dumps(st.session_state.demand["default"]))
            st.info(f"Override enabled for {date_str}")

        if date_str in st.session_state.demand["overrides"]:
            st.warning(f"Editing overrides for {date_str}")
            override_data = st.session_state.demand["overrides"][date_str]
            
            for s in st.session_state.shifts:
                with st.expander(f"Shift: {s['code']} - {s['name']} (OVERRIDE)", expanded=False):
                    shift_code = s['code']
                    if shift_code not in override_data:
                        override_data[shift_code] = {"Total": 1, "Grade": all_grades[-1] if all_grades else "RN"}
                    
                    ov_col1, ov_col2 = st.columns([2, 1])
                    with ov_col1:
                        ov_total = st.number_input(f"Minimum Total Nurses", min_value=1, value=override_data[shift_code].get("Total", 1), key=f"ov_total_{date_str}_{shift_code}")
                        override_data[shift_code]["Total"] = ov_total
                    with ov_col2:
                        all_grades = [g['code'] for layer in st.session_state.grades for g in layer]
                        ov_current_grade = override_data[shift_code].get("Grade", all_grades[-1] if all_grades else "RN")
                        ov_grade_idx = all_grades.index(ov_current_grade) if ov_current_grade in all_grades else (len(all_grades)-1 if all_grades else 0)
                        ov_new_grade = st.selectbox("Min Grade", all_grades, index=ov_grade_idx, key=f"ov_grade_{date_str}_{shift_code}")
                        override_data[shift_code]["Grade"] = ov_new_grade

                    st.write("**Specific Skill Requirements**")
                    ov_skills_req = {k: v for k, v in override_data[shift_code].items() if k != "Total"}
                    
                    # Similar data editor approach for overrides
                    ov_skill_list = [{"Skill": k, "Min Count": v} for k, v in ov_skills_req.items()]
                    df_ov_skills = pd.DataFrame(ov_skill_list)
                    
                    edited_ov_skills = st.data_editor(
                        df_ov_skills,
                        num_rows="dynamic",
                        key=f"ov_skills_editor_{date_str}_{shift_code}",
                        column_config={
                            "Skill": st.column_config.SelectboxColumn("Skill", options=[sk['code'] for sk in st.session_state.skills], required=True),
                            "Min Count": st.column_config.NumberColumn("Min Count", min_value=1, max_value=ov_total, default=1, required=True)
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # Update override state
                    new_ov_dict = {"Total": ov_total}
                    for _, row in edited_ov_skills.iterrows():
                        if pd.notna(row['Skill']):
                            count = min(int(row['Min Count']), ov_total)
                            new_ov_dict[row['Skill']] = count
                    st.session_state.demand["overrides"][date_str][shift_code] = new_ov_dict

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Override", type="primary"):
                    save_data(DEMAND_DATA_FILE, st.session_state.demand)
                    st.success(f"Override saved for {date_str}")
            with col2:
                if st.button("Delete Override", type="secondary"):
                    del st.session_state.demand["overrides"][date_str]
                    save_data(DEMAND_DATA_FILE, st.session_state.demand)
                    st.success(f"Override deleted for {date_str}")
                    st.rerun()
        else:
            st.info("No override set for this date. Default demand will be used.")


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Generate Schedule'

st.sidebar.markdown('### Overview')
st.sidebar.button("🚀 Generate Schedule", on_click=lambda: st.session_state.update(current_page='Generate Schedule'), use_container_width=True, type="primary")

st.sidebar.markdown('### Settings')

with st.sidebar.expander("⚙️ General Settings", expanded=True):
    st.button("🎨 Theme", on_click=lambda: st.session_state.update(current_page='Theme'), use_container_width=True)
    st.button("📅 Date Range", on_click=lambda: st.session_state.update(current_page='Date Range'), use_container_width=True)
    st.button("ℹ️ Constraints & Rules", on_click=lambda: st.session_state.update(current_page='Constraints & Rules'), use_container_width=True)

with st.sidebar.expander("🔐 Admin Database", expanded=False):
    st.button("🗓️ Manage Shifts", on_click=lambda: st.session_state.update(current_page='Manage Shifts'), use_container_width=True)
    st.button("🔧 Manage Skills", on_click=lambda: st.session_state.update(current_page='Manage Skills'), use_container_width=True)
    st.button("🏆 Grades Hierarchy", on_click=lambda: st.session_state.update(current_page='Grades Hierarchy'), use_container_width=True)
    st.button("🏖️ Leave Types", on_click=lambda: st.session_state.update(current_page='Leave Types'), use_container_width=True)
    st.button("👥 Manage Staffs", on_click=lambda: st.session_state.update(current_page='Manage Staffs'), use_container_width=True)
    st.button("📊 Minimum Demand", on_click=lambda: st.session_state.update(current_page='Minimum Demand'), use_container_width=True)

# ---------------------------------------------------------------------
# Main Layout: Content
# ---------------------------------------------------------------------

if st.session_state.current_page == 'Theme':
    st.header("Theme Settings")
    st.write("Choose a visual theme for the application.")

    theme_options = ['Light', 'Dark', 'Eye Comfort']
    theme_descriptions = {
        'Light': '☀️ Default bright theme — clean and clear.',
        'Dark': '🌙 Dark background — easy on the eyes in low light.',
        'Eye Comfort': '🍂 Warm sepia tones — reduces blue light for extended use.'
    }

    for theme_name in theme_options:
        is_active = st.session_state.theme == theme_name
        btn_type = 'primary' if is_active else 'secondary'
        label = f"{'✅ ' if is_active else ''}{theme_name}"
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(label, key=f"theme_{theme_name}", type=btn_type, use_container_width=True):
                st.session_state.theme = theme_name
                st.rerun()
        with col2:
            st.write(theme_descriptions[theme_name])

    st.caption(f"Current theme: **{st.session_state.theme}**")

elif st.session_state.current_page == 'Date Range':
    st.header("Select Roster Date Range")
    st.write("Pick **two dates** on the calendar below. The earlier date becomes the **start** and the later date becomes the **end** of your roster.")

    selected_range = st.date_input(
        "Roster period",
        value=(st.session_state.roster_start_date, st.session_state.roster_end_date),
        min_value=today,
        max_value=date(today.year + 10, today.month, today.day),
        format="YYYY-MM-DD",
        key="date_range_picker"
    )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        num_days = (end_date - start_date).days + 1
        st.success(f"**Selected range:** {start_date.strftime('%a, %b %d, %Y')} → {end_date.strftime('%a, %b %d, %Y')}  ({num_days} days)")

        if st.button("✅ Apply Date Range", type="primary"):
            st.session_state.roster_start_date = start_date
            st.session_state.roster_end_date = end_date
            # Reset demand table so it rebuilds for the new date range
            if 'shift_reqs_df' in st.session_state:
                del st.session_state['shift_reqs_df']
            st.success("Date range updated!")
            st.rerun()
    else:
        st.info("Please select both a **start** and **end** date.")

elif st.session_state.current_page == 'Manage Shifts':
    render_manage_shifts()

elif st.session_state.current_page == 'Manage Skills':
    render_manage_skills()

elif st.session_state.current_page == 'Grades Hierarchy':
    st.header("Grades Hierarchy")
    render_manage_grades()

elif st.session_state.current_page == 'Leave Types':
    st.header("Leave Types")
    render_manage_leave_types()

elif st.session_state.current_page == 'Manage Staffs':
    st.header("Manage Staffs")
    render_manage_staffs()

elif st.session_state.current_page == 'Minimum Demand':
    st.header("Minimum Demand")
    render_manage_demand()

elif st.session_state.current_page == 'Constraints & Rules':
    st.header("Constraints & Rules")
    st.write("Overview of the scheduling constraints and optimization objectives used by the solver.")

    st.subheader("Hard Constraints (Enforced)")
    
    # Checkbox to toggle multiple shifts
    if 'allow_multiple_shifts' not in st.session_state:
        st.session_state.allow_multiple_shifts = False

    mult_shifts_col1, mult_shifts_col2 = st.columns([1, 11])
    with mult_shifts_col1:
        new_val = st.checkbox("", value=st.session_state.allow_multiple_shifts, key="mult_shifts_toggle")
        if new_val != st.session_state.allow_multiple_shifts:
            st.session_state.allow_multiple_shifts = new_val
            st.rerun()
    with mult_shifts_col2:
        st.markdown("**Allow Multiple Shifts Per Day** (Must not overlap in time)")

    st.markdown('''
    These rules are **always** enforced — the solver will never violate them.
    ''')
    
    if st.session_state.allow_multiple_shifts:
        st.markdown('''
        - **Max Shifts/Day:** Nurses can work multiple shifts per day, as long as their times do not overlap.
        - **Max 6 Shifts/Week:** No nurse works more than 6 days in a 7-day week.
        - **Max 6 Consecutive Days:** No nurse works more than 6 days in a row.
        - **Night Shift Recovery:**
            - Max 4 consecutive night shifts.
            - 1 Night → 1 Day Off
            - 2-3 Nights → 2 Days Off
            - 4 Nights → 3 Days Off
        - **Leave Compliance:** Nurses on leave are not assigned.
        ''')
    else:
        st.markdown('''
        - **Max 1 Shift/Day:** No nurse works more than 1 shift per day.
        - **Max 6 Shifts/Week:** No nurse works more than 6 days in a 7-day week.
        - **Max 6 Consecutive Days:** No nurse works more than 6 days in a row.
        - **Night Shift Recovery:**
            - Max 4 consecutive night shifts.
            - 1 Night → 1 Day Off
            - 2-3 Nights → 2 Days Off
            - 4 Nights → 3 Days Off
        - **Leave Compliance:** Nurses on leave are not assigned.
        ''')

    st.subheader("Soft Objectives (Optimized)")
    st.markdown('''
    These goals are **optimized** — the solver tries its best to achieve them.

    - **Maximize Utilization:** Assign extra nurses to shifts beyond minimums if capacity allows.
    - **Fairness:** Balance total shifts among all nurses.
    ''')

elif st.session_state.current_page == 'Generate Schedule':
    st.header("Schedule Generation")
    st.info("The solver will prioritize filling extra shifts (utilization) while keeping the workload balanced (fairness).")

    if st.button("Generate Optimized Schedule", type="primary"):
        with st.spinner("Optimizing for utilization and fairness..."):
            
            shift_requirements = {}

            # Build structured shift requirements
            for d_idx in range(planning_horizon):
                target_date = roster_start + timedelta(days=d_idx)
                date_str = target_date.strftime("%Y-%m-%d")
                
                # Check for override, otherwise use default
                day_demand = st.session_state.demand["overrides"].get(date_str, st.session_state.demand["default"])
                
                for s in st.session_state.shifts:
                    req_dict = day_demand.get(s['code'], {"Total": 1})
                    shift_requirements[(d_idx, s['code'])] = req_dict

            model = NurseRosteringModel(
                num_nurses=len(st.session_state.nurses),
                num_days=planning_horizon,
                nurses_list=st.session_state.nurses,
                shift_requirements=shift_requirements,
                shifts_config=st.session_state.shifts,
                grade_hierarchy=st.session_state.grades,
                allow_multiple_shifts=st.session_state.get('allow_multiple_shifts', False)
            )
            
            try:
                model.build_model()
                model.add_constraints()
                status = model.solve_model()
                
                from ortools.sat.python import cp_model
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    st.success("Optimized schedule found!")
                    
                    schedule = model.extract_solution(status)
                    
                    df_schedule = pd.DataFrame.from_dict(schedule, orient='index')
                    df_schedule.columns = date_labels
                    
                    def color_schedule(val):
                        current_colors = {s['code']: s.get('color', '#FFFFFF') for s in st.session_state.shifts}
                        color = current_colors.get(val, 'white')
                        if val == '-':
                            return 'background-color: white; color: black'
                        
                        return f'background-color: {color}; color: black; font-weight: bold'

                    st.dataframe(df_schedule.style.map(color_schedule), use_container_width=True)
                    
                    stats = []
                    total_assigned_all = 0
                    min_shifts = float('inf')
                    max_shifts = float('-inf')

                    for nurse_name, shifts in schedule.items():
                        total_shifts = sum(1 for s in shifts if s != '-')
                        stats.append({'Nurse': nurse_name, 'Total Shifts': total_shifts})
                        total_assigned_all += total_shifts
                        min_shifts = min(min_shifts, total_shifts)
                        max_shifts = max_shifts if max_shifts > total_shifts else total_shifts

                    df_stats = pd.DataFrame(stats)
                    st.dataframe(df_stats, use_container_width=True)

                    st.metric("Total Shifts Assigned", total_assigned_all)
                    st.metric("Shift Fairness", f"{min_shifts}-{max_shifts} shifts per nurse")
                    st.info(f"Lexicographic Optimization Applied: Max utilization first, then fairness.")
                    
                else:
                    st.error("No feasible solution found. Try adding more nurses or reducing minimum coverage requirements.")
                    
            except Exception as e:
                import traceback
                st.error(f"An error occurred: {e}\n{traceback.format_exc()}")
