import streamlit as st 

import pandas as pd
import json
import os
import io
from datetime import datetime, time, date, timedelta
import calendar
from model import NurseRosteringModel
from supabase import create_client, Client
import staff_db
from professional_roster_component import professional_roster
import tutorial_manager

st.set_page_config(page_title="Nurse Rostering System", layout="wide")

# --- Initialize Tutorial ---
tutorial_manager.initialize_tutorial_state()

# --- Tutorial Page Checks (Force show before anything else) ---
if st.session_state.show_tutorial_landing:
    tutorial_manager.render_landing_page()
    st.stop()

if st.session_state.tutorial_finished:
    tutorial_manager.render_summary_page()
    st.stop()

if st.session_state.tutorial_active and st.session_state.current_tutorial_module is None:
    tutorial_manager.render_tutorial_menu()
    st.stop()

# Temporary Debug Info - remove after fixing
with st.sidebar.expander("🛠️ Tutorial Debug", expanded=True):
    st.write(f"show_tutorial_landing: {st.session_state.get('show_tutorial_landing')}")
    st.write(f"tutorial_active: {st.session_state.get('tutorial_active')}")
    st.write(f"tutorial_finished: {st.session_state.get('tutorial_finished')}")
    if st.button("Force Show Landing API"):
         st.session_state.show_tutorial_landing = True
         st.rerun()

# --- Supabase Initialization ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase configuration error: {e}")
    st.stop()

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
DEPARTMENTS_DATA_FILE = "departments.json"
if 'pending_notification' not in st.session_state:
    st.session_state.pending_notification = None
if 'last_action_message' not in st.session_state:
    st.session_state.last_action_message = "System Ready"

def reset_form_keys(keys):
    """Utility to clear specific keys from session state to reset forms."""
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]

def notify(message, detail=None, type="success"):
    """Queues a notification and updates the last action sidebar indicator."""
    # Use double newline for reliable markdown line breaks
    full_msg = f"**{message}**\n\n{detail}" if detail else message
    st.session_state.pending_notification = (message, detail, type)
    st.session_state.last_action_message = full_msg

def show_notifications():
    """Displays queued notifications as toasts."""
    if st.session_state.pending_notification:
        message, detail, type = st.session_state.pending_notification
        icon = "✅" if type == "success" else "⚠️" if type == "warning" else "❌" if type == "error" else "ℹ️"
        
        # Use two spaces followed by a newline for the toast
        # This is a standard markdown trick for line breaks within a block
        toast_msg = f"**{message}**  \n{detail}" if detail else message
        st.toast(toast_msg, icon=icon)
        st.session_state.pending_notification = None

def load_data(table_name, file_path, default_data):
    """Load data from Supabase, falling back to JSON or default."""
    try:
        # 1. Try Supabase
        response = supabase.table(table_name).select("*").execute()
        if response.data:
            # Table-specific post-processing
            if table_name == "grades":
                # Reconstruct hierarchy: list of lists
                layers = {}
                for g in response.data:
                    idx = g['layer_index']
                    if idx not in layers: layers[idx] = []
                    layers[idx].append({"code": g['code'], "name": g['name']})
                return [layers[i] for i in sorted(layers.keys())]
            
            if table_name == "demand":
                # Reconstruct demand dict
                demand = {"default": {}, "overrides": {}}
                for d in response.data:
                    type_str = d['type']
                    date_key = d['date_key']
                    shift = d['shift_code']
                    skill = d['skill_code'] or "Total"
                    count = d['count']
                    
                    if date_key not in demand[type_str]: demand[type_str][date_key] = {}
                    if shift not in demand[type_str][date_key]: demand[type_str][date_key][shift] = {}
                    demand[type_str][date_key][shift][skill] = count
                return demand
                
            return response.data
    except Exception as e:
        st.warning(f"Could not load {table_name} from Supabase: {e}")

    # 2. Fallback to JSON
    json_data = default_data
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                loaded = json.load(f)
                if loaded:
                    json_data = loaded
                    # AUTO-MIGRATION: If Supabase was empty but JSON has data, push it up!
                    # This happens "invisibly" the first time a user with local data connects to cloud.
                    try:
                        save_data(table_name, file_path, json_data)
                    except:
                        pass # Failure here is fine, it will stay in local fallback
        except Exception as e:
            st.error(f"Error loading {file_path}: {e}")
    
    return json_data

def save_data(table_name, file_path, data):
    """Save data to Supabase and fallback to JSON."""
    try:
        # Success flag for UI feedback
        cloud_success = False
        
        # Table-specific pre-processing and UPSERT
        if table_name == "grades":
            # Flatten hierarchy for storage
            flattened = []
            for idx, layer in enumerate(data):
                for g in layer:
                    flattened.append({"layer_index": idx, "code": g['code'], "name": g['name']})
            # Clear and repopulate (simple for small config tables)
            supabase.table(table_name).delete().neq("id", -1).execute() # Clear all
            if flattened:
                supabase.table(table_name).insert(flattened).execute()
            cloud_success = True
            
        elif table_name == "demand":
            # Flatten demand dict
            rows = []
            for typ in ["default", "overrides"]:
                for d_key, shifts in data.get(typ, {}).items():
                    for s_code, skills in shifts.items():
                        for skill, count in skills.items():
                            rows.append({
                                "type": typ,
                                "date_key": d_key,
                                "shift_code": s_code,
                                "skill_code": None if skill == "Total" else skill,
                                "count": count
                            })
            supabase.table(table_name).delete().neq("id", -1).execute()
            if rows:
                supabase.table(table_name).insert(rows).execute()
            cloud_success = True
            
        elif table_name in ["nurses", "shifts", "skills", "leaves", "departments"]:
            # Standard UPSERT
            # Map logical table name "nurses" to physical table "staff"
            actual_table = "staff" if table_name == "nurses" else table_name
            
            # Filter columns to only those present in the database to prevent PostgREST key mismatch crashes
            table_columns = {
                "staff": ["employee_id", "name", "grade", "leave_days", "skills", "department_id", "allow_night_shift", "max_consecutive_work_days"],
                "shifts": ["id", "code", "name", "start", "end", "duration", "type", "color", "required_skills"],
                "skills": ["id", "code", "name", "description", "color"],
                "leaves": ["code", "name", "description", "color", "is_paid"],
                "departments": ["id", "name", "description"]
            }
            allowed_keys = table_columns.get(actual_table, [])
            
            clean_data = []
            for item in data:
                clean_item = {}
                for k in allowed_keys:
                    if k == "employee_id":
                        clean_item[k] = item.get("employee_id", item.get("id"))
                    elif k == "required_skills":
                        clean_item[k] = item.get(k, [])
                    elif k == "leave_days":
                        clean_item[k] = item.get(k, [])
                    elif k == "skills":
                        clean_item[k] = item.get(k, [])
                    elif k == "description":
                        clean_item[k] = item.get(k, "")
                    else:
                        clean_item[k] = item.get(k)
                clean_data.append(clean_item)
                
            supabase.table(actual_table).upsert(clean_data).execute()
            cloud_success = True
            
    except Exception as e:
        st.error(f"Supabase Save Error ({table_name}): {e}")

    # Also save to local JSON as backup
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Local Save Error ({file_path}): {e}")

# Default Shifts
DEFAULT_SHIFTS = [
    {"code": "M", "name": "Morning", "start": "07:00", "end": "14:00", "duration": 480, "type": "Day", "color": "#CCE5FF"},
    {"code": "E", "name": "Evening", "start": "14:00", "end": "22:00", "duration": 480, "type": "Day", "color": "#FFD699"},
    {"code": "N", "name": "Night", "start": "21:00", "end": "07:30", "duration": 600, "type": "Night", "color": "#E5CCFF"}
]

# Default Skills
DEFAULT_SKILLS = [
    {"code": "ACLS", "name": "Advanced Cardiac Life Support", "description": "Advanced treatment for cardiac emergencies.", "color": "#FFCCCB"},
    {"code": "BLS", "name": "Basic Life Support", "description": "CPR, AED use, and basic emergency response.", "color": "#B2F2BB"},
    {"code": "CAR", "name": "Cardiology", "description": "Cardiology department", "color": "#A5D8FF"},
    {"code": "IVT", "name": "Intravenous Therapy", "description": "Inserting and managing IV lines.", "color": "#FFD8A8"},
    {"code": "MED", "name": "General Medicine", "description": "General medical ward care", "color": "#D0EBFF"},
    {"code": "NEU", "name": "Neurology", "description": "Neurology department", "color": "#D3f9d8"},
    {"code": "SUR", "name": "Surgical", "description": "Surgical unit experience", "color": "#FFF9DB"},
    {"code": "WDC", "name": "Wound Care", "description": "Cleaning, dressing, and monitoring wounds.", "color": "#F3D9FA"}
]

st.title("Nurse Rostering System")
show_notifications()

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
if 'departments' not in st.session_state:
    st.session_state.departments = load_data("departments", DEPARTMENTS_DATA_FILE, [{"id": "default-dept", "name": "General Department", "description": "Default department"}])

if 'shifts' not in st.session_state:
    st.session_state.shifts = load_data("shifts", SHIFTS_DATA_FILE, DEFAULT_SHIFTS)
    for s in st.session_state.shifts:
        if 'color' not in s:
            s['color'] = "#E0E0E0"
        if 'required_skills' not in s:
            s['required_skills'] = []

if 'skills' not in st.session_state:
    st.session_state.skills = load_data("skills", SKILLS_DATA_FILE, DEFAULT_SKILLS)
    for sk in st.session_state.skills:
        if 'color' not in sk:
            sk['color'] = "#F0F4F8"
    st.session_state.skills.sort(key=lambda x: x['code'].upper())

if 'nurses' not in st.session_state:
    raw_staff = staff_db.fetch_all_staff(supabase)
    if not raw_staff:
        # Fallback to JSON or defaults if Supabase is empty
        raw_staff = load_data("nurses", NURSE_DATA_FILE, [
            {'employee_id': f'N{i+1:03}', 'name': f'Nurse {i+1}', 'grade': 'RN', 'leave_days': [], 'skills': [], 'department_id': 'default-dept', 'allow_night_shift': True, 'max_consecutive_work_days': 6} for i in range(10)
        ])
    
    # Map employee_id to id for backward compatibility
    for s in raw_staff:
        if 'employee_id' in s:
            s['id'] = s['employee_id']
        elif 'id' in s:
            s['employee_id'] = s['id']
            s['id'] = s['employee_id']
            
    st.session_state.nurses = raw_staff

if 'grades' not in st.session_state:
    # Hierarchy is a list of layers, from top (senior) to bottom (junior)
    # Each layer is a list of grade objects: {"code": "SN", "name": "Staff Nurse"}
    raw_grades = load_data("grades", GRADES_DATA_FILE, [
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

if 'grades_pool' not in st.session_state:
    st.session_state.grades_pool = []

if 'leaves' not in st.session_state:
    DEFAULT_LEAVES = [
        {"code": "AL", "name": "Annual Leave", "description": "Paid annual vacation", "color": "#E6FFFA", "is_paid": True},
        {"code": "SL", "name": "Sick Leave", "description": "Paid sick leave", "color": "#FFF5F5", "is_paid": True},
        {"code": "UL", "name": "Unpaid Leave", "description": "Unpaid leave of absence", "color": "#F7FAFC", "is_paid": False}
    ]
    st.session_state.leaves = load_data("leaves", LEAVES_DATA_FILE, DEFAULT_LEAVES)

if 'demand' not in st.session_state:
    # Default demand: { 'default': { 'shift_code': { 'skill_code': min_count, 'Total': min_count } }, 'overrides': { 'YYYY-MM-DD': { ... } } }
    st.session_state.demand = load_data("demand", DEMAND_DATA_FILE, {
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

if 'schedule_weights' not in st.session_state:
    st.session_state.schedule_weights = {
        'utilization': 10,
        'overall_fairness': 5,
        'night_fairness': 5,
        'weekend_fairness': 5
    }

if 'zoom_level' not in st.session_state:
    st.session_state.zoom_level = 100

if 'painter_shift' not in st.session_state:
    st.session_state.painter_shift = None

# ---------------------------------------------------------------------
# Dialog Modals
# ---------------------------------------------------------------------

def render_manage_shifts():
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
            new_shift_code = st.text_input("Code (e.g., D1)", max_chars=5, key="new_shift_code")
            new_shift_name = st.text_input("Name", key="new_shift_name")
            new_shift_type = st.selectbox("Type", ["Day", "Night"], key="new_shift_type")
            
            st.write("**Shift Time**")
            col_s_h, col_s_m, col_arrow, col_e_h, col_e_m = st.columns([2, 2, 1, 2, 2])
            
            with col_s_h:
                new_s_h = st.selectbox("Start Hour", hours, index=7, key="new_shift_s_h")
            with col_s_m:
                new_s_m = st.selectbox("Start Min", minutes, index=0, key="new_shift_s_m")
            with col_arrow:
                st.markdown("<div style='text-align: center; padding-top: 30px;'>➡️</div>", unsafe_allow_html=True)
            with col_e_h:
                new_e_h = st.selectbox("End Hour", hours, index=15, key="new_shift_e_h")
            with col_e_m:
                new_e_m = st.selectbox("End Min", minutes, index=0, key="new_shift_e_m")
                
            new_shift_color = st.color_picker("Color", "#E0E0E0", key="new_shift_color")
            
            if st.form_submit_button("Add Shift", use_container_width=True):
                if new_shift_code and new_shift_name:
                    if any(s['code'] == new_shift_code for s in st.session_state.shifts):
                        notify("Add Shift Failed", detail="Shift code already exists!", type="error")
                        st.rerun()
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
                        save_data("shifts", SHIFTS_DATA_FILE, st.session_state.shifts)
                        notify("Shift added successfully:", detail=f"{new_shift_code} - {new_shift_name} ({new_shift_type})")
                        
                        # Clear form state
                        reset_form_keys(["new_shift_code", "new_shift_name", "new_shift_type", 
                                       "new_shift_s_h", "new_shift_s_m", "new_shift_e_h", 
                                       "new_shift_e_m", "new_shift_color"])
                else:
                    notify("Add Shift Failed", detail="Code and Name are required.", type="warning")


    st.markdown("---")
    st.subheader("Available Shifts")

    # Track which shift is being edited
    if 'editing_shift_id' not in st.session_state:
        st.session_state.editing_shift_id = None
        
    # --- Bulk Actions ---
    selected_for_deletion = [s['id'] for s in st.session_state.shifts if st.session_state.get(f"bulk_del_shift_{s['id']}", False)]
    if selected_for_deletion:
        if st.button(f"🗑️ Delete {len(selected_for_deletion)} Selected Shifts", type="primary"):
            shift_codes_to_del = [s['code'] for s in st.session_state.shifts if s['id'] in selected_for_deletion]
            for code in shift_codes_to_del:
                try: supabase.table("shifts").delete().eq("code", code).execute()
                except: pass
            st.session_state.shifts = [s for s in st.session_state.shifts if s['id'] not in selected_for_deletion]
            save_data("shifts", SHIFTS_DATA_FILE, st.session_state.shifts)
            for sid in selected_for_deletion:
                if f"bulk_del_shift_{sid}" in st.session_state: del st.session_state[f"bulk_del_shift_{sid}"]
            notify("Bulk Delete Successful", detail=f"Removed {len(selected_for_deletion)} shifts.")
            st.rerun()
    
    for i, s in enumerate(st.session_state.shifts):
        if 'id' not in s:
            s['id'] = f"{s['code']}_{i}"
        
        stable_key = s['id']
        
        # --- Render Shift Card with Side-by-Side Buttons ---
        with st.container():
            # Use columns to ensure buttons are strictly alongside the info
            card_cols = st.columns([0.5, 7.5, 0.8, 0.8])
            
            with card_cols[0]:
                st.markdown("<div style='padding-top: 25px;'></div>", unsafe_allow_html=True)
                st.checkbox("", key=f"bulk_del_shift_{stable_key}", label_visibility="collapsed")
                
            with card_cols[1]:
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
            
            with card_cols[2]:
                # Vertical centering hack for Streamlit buttons
                st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                if st.button("✏️", key=f"edit_btn_{stable_key}", help="Edit Shift", use_container_width=True):
                    st.session_state.editing_shift_id = s['id']
            with card_cols[3]:
                st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_btn_{stable_key}", help="Delete Shift", use_container_width=True):
                    deleted_name = st.session_state.shifts[i]['name']
                    st.session_state.shifts.pop(i)
                    save_data("shifts", SHIFTS_DATA_FILE, st.session_state.shifts)
                    notify("Shift deleted successfully:", detail=f"'{deleted_name}' removed")
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
                        
                        old_code = s['code']
                        if edit_code != old_code and any(shift['code'] == edit_code for shift in st.session_state.shifts):
                            notify("Update Failed", detail="Shift code already exists!", type="error")
                            st.rerun()
                        else:
                            if edit_code != old_code:
                                try: supabase.table("shifts").update({"code": edit_code}).eq("code", old_code).execute()
                                except: pass
                                
                                # Cascade local demand references
                                for t in ["default", "overrides"]:
                                    for d_key, shifts_dict in st.session_state.demand.get(t, {}).items():
                                        if old_code in shifts_dict:
                                            shifts_dict[edit_code] = shifts_dict.pop(old_code)
                                import threading
                                threading.Thread(target=save_data, args=("demand", DEMAND_DATA_FILE, st.session_state.demand)).start()

                            s['code'] = edit_code
                            s['name'] = edit_name
                            s['type'] = edit_type
                            s['start'] = s_time
                            s['end'] = e_time
                            s['duration'] = int((end_dt - start_dt).total_seconds() / 60)
                            s['color'] = edit_color
                            
                            # Automatic Sort by Start Time
                            st.session_state.shifts.sort(key=lambda x: x.get('start', '00:00'))
                            save_data("shifts", SHIFTS_DATA_FILE, st.session_state.shifts)
                            st.session_state.editing_shift_id = None
                            notify("Shift updated successfully:", detail=f"{s['code']} - {s['name']}")
                            st.rerun()
                with f_col2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.editing_shift_id = None
                        st.rerun()
            st.markdown("---")

def render_manage_grades():
    import streamlit.components.v1 as components
    import json as _json

    st.subheader("Grades Hierarchy")
    st.caption("Higher layers = more senior. Seniors can cover junior shifts. Use the controls below to manage the pyramid.")

    grades = st.session_state.grades  # list of lists

    # ── Rich Pyramid Visualization ──
    layer_colors = [
        "#3b3486", "#5a52b0", "#7b74d4", "#9d98e0",
        "#bfbdec", "#d6d4f2", "#e8e7f8", "#f0effe"
    ]
    total = len(grades)

    pyramid_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', system-ui, sans-serif; background: transparent; }
    .pyramid-container {
        display: flex; flex-direction: column; align-items: center;
        gap: 8px; padding: 20px 10px;
    }
    .pyramid-title {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1.5px; color: #7c83a8; margin-bottom: 8px;
    }
    .pyramid-layer {
        display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;
        padding: 12px 18px; border-radius: 12px; min-height: 44px;
        transition: all 0.3s ease; position: relative; align-items: center;
    }
    .pyramid-layer:hover { transform: scale(1.02); filter: brightness(1.05); }
    .layer-label {
        position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
        font-size: 0.6rem; font-weight: 700; letter-spacing: 0.5px;
        text-transform: uppercase; opacity: 0.6; color: rgba(255,255,255,0.8);
        pointer-events: none;
    }
    .grade-badge {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 6px 14px; border-radius: 8px; font-weight: 600;
        font-size: 0.82rem; background: rgba(255,255,255,0.92);
        border: 1.5px solid rgba(0,0,0,0.06); white-space: nowrap;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }
    .grade-badge:hover { transform: translateY(-1px); box-shadow: 0 3px 8px rgba(0,0,0,0.12); }
    .grade-code {
        font-family: 'SF Mono', 'Menlo', monospace; font-weight: 700;
    }
    .grade-name { font-weight: 500; opacity: 0.85; }
    .empty-layer {
        font-size: 0.75rem; color: rgba(255,255,255,0.6); font-style: italic;
    }
    .seniority-arrow {
        font-size: 0.65rem; color: #9ba3c7; text-align: center;
        letter-spacing: 2px; margin: 2px 0;
    }
    </style>
    <div class="pyramid-container">
        <div class="pyramid-title">📐 Seniority Pyramid</div>
    """

    if total == 0:
        pyramid_html += '<div style="color: #aab0cf; font-style: italic; padding: 20px;">No layers defined. Add a layer below.</div>'
    else:
        pyramid_html += '<div class="seniority-arrow">▲ MOST SENIOR</div>'
        for i, layer in enumerate(grades):
            width_pct = 80 if total <= 1 else int(35 + (i / max(total - 1, 1)) * 55)
            color = layer_colors[min(i, len(layer_colors) - 1)]
            badge_color = color

            pyramid_html += f'<div class="pyramid-layer" style="width: {width_pct}%; background: {color};">'
            pyramid_html += f'<span class="layer-label">L{i + 1}</span>'
            if not layer:
                pyramid_html += '<span class="empty-layer">Empty layer</span>'
            else:
                for g in layer:
                    pyramid_html += f'<div class="grade-badge" style="color: {badge_color};"><span class="grade-code">{g["code"]}</span><span class="grade-name">{g["name"]}</span></div>'
            pyramid_html += '</div>'
        pyramid_html += '<div class="seniority-arrow">▼ LEAST SENIOR</div>'

    pyramid_html += '</div>'
    components.html(pyramid_html, height=max(total * 65 + 100, 200), scrolling=False)

    st.markdown("---")

    # ── Layer Management ──
    col_add_layer, col_remove_layer = st.columns(2)
    with col_add_layer:
        if st.button("➕ Add Layer to Bottom", use_container_width=True):
            st.session_state.grades.append([])
            save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
            notify("Layer added:", detail="New empty layer added to bottom of pyramid")
            st.rerun()
    with col_remove_layer:
        if total > 0:
            if st.button("➖ Remove Bottom Layer", use_container_width=True, disabled=(total == 0)):
                bottom = st.session_state.grades[-1]
                if not bottom:
                    st.session_state.grades.pop()
                    save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                    notify("Layer removed:", detail="Empty bottom layer removed")
                    st.rerun()
                else:
                    st.session_state._confirm_remove_layer = True

    if getattr(st.session_state, '_confirm_remove_layer', False):
        st.warning(f"⚠️ Bottom layer has {len(st.session_state.grades[-1])} grade(s). Removing will delete them.")
        c1, c2 = st.columns(2)
        if c1.button("✅ Confirm Remove", type="primary", use_container_width=True):
            st.session_state.grades.pop()
            st.session_state._confirm_remove_layer = False
            save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
            notify("Layer removed:", detail="Bottom layer and its grades removed")
            st.rerun()
        if c2.button("❌ Cancel", use_container_width=True):
            st.session_state._confirm_remove_layer = False
            st.rerun()

    # ── Per-Layer Grade Management ──
    st.markdown("")
    for i, layer in enumerate(grades):
        color = layer_colors[min(i, len(layer_colors) - 1)]
        with st.expander(f"🔹 Level {i + 1} — {len(layer)} grade(s)", expanded=False):
            # Add grade to this layer
            with st.form(f"add_grade_layer_{i}", clear_on_submit=True):
                fc1, fc2, fc3 = st.columns([1, 2, 1])
                with fc1:
                    new_code = st.text_input("Code", key=f"ng_code_{i}", max_chars=5, placeholder="e.g. SN")
                with fc2:
                    new_name = st.text_input("Full Name", key=f"ng_name_{i}", placeholder="e.g. Senior Nurse")
                with fc3:
                    st.write("")
                    st.write("")
                    submitted = st.form_submit_button("➕ Add Grade", use_container_width=True)
                if submitted and new_code and new_name:
                    # Check for duplicate code across all layers
                    all_codes = [g['code'] for lay in grades for g in lay]
                    if new_code.upper() in all_codes:
                        st.error(f"Grade code '{new_code.upper()}' already exists!")
                    else:
                        st.session_state.grades[i].append({"code": new_code.upper(), "name": new_name})
                        save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                        notify("Grade added:", detail=f"'{new_code.upper()}' added to Level {i + 1}")
                        st.rerun()

            # Existing grades in this layer
            if layer:
                for j, grade in enumerate(layer):
                    gc1, gc2, gc3, gc4, gc5 = st.columns([0.8, 2.5, 0.5, 0.5, 0.5])
                    gc1.code(grade['code'])
                    gc2.write(grade['name'])
                    # Move up within seniority (to upper layer)
                    if i > 0:
                        if gc3.button("⬆️", key=f"mu_{i}_{j}", help="Move to higher layer"):
                            moved = st.session_state.grades[i].pop(j)
                            st.session_state.grades[i - 1].append(moved)
                            save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                            notify("Grade moved:", detail=f"'{grade['code']}' moved to Level {i}")
                            st.rerun()
                    else:
                        gc3.write("")
                    # Move down within seniority (to lower layer)
                    if i < total - 1:
                        if gc4.button("⬇️", key=f"md_{i}_{j}", help="Move to lower layer"):
                            moved = st.session_state.grades[i].pop(j)
                            st.session_state.grades[i + 1].append(moved)
                            save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                            notify("Grade moved:", detail=f"'{grade['code']}' moved to Level {i + 2}")
                            st.rerun()
                    else:
                        gc4.write("")
                    if gc5.button("🗑️", key=f"dg_{i}_{j}", help="Delete this grade"):
                        deleted = st.session_state.grades[i].pop(j)
                        # Clean up empty layers
                        st.session_state.grades = [l for l in st.session_state.grades if l]
                        save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                        notify("Grade deleted:", detail=f"'{deleted['code']}' removed")
                        st.rerun()
            else:
                st.info("No grades in this layer. Add one above or move grades here from other layers.")

            # Move entire layer up/down
            ml, mr = st.columns(2)
            if i > 0:
                if ml.button(f"⬆️ Move Layer {i + 1} Up", key=f"lay_up_{i}", use_container_width=True):
                    st.session_state.grades[i - 1], st.session_state.grades[i] = st.session_state.grades[i], st.session_state.grades[i - 1]
                    save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                    notify("Layer moved:", detail=f"Level {i + 1} moved up")
                    st.rerun()
            if i < total - 1:
                if mr.button(f"⬇️ Move Layer {i + 1} Down", key=f"lay_dn_{i}", use_container_width=True):
                    st.session_state.grades[i], st.session_state.grades[i + 1] = st.session_state.grades[i + 1], st.session_state.grades[i]
                    save_data("grades", GRADES_DATA_FILE, st.session_state.grades)
                    notify("Layer moved:", detail=f"Level {i + 1} moved down")
                    st.rerun()


def render_manage_leave_types():
    with st.expander("Add New Leave Type", expanded=False):
        with st.form("add_leave_form", clear_on_submit=True):
            col_code, col_name, col_paid = st.columns([1, 2, 1])
            with col_code:
                new_code = st.text_input("Code (e.g., ML)", max_chars=5, key="new_leave_code")
            with col_name:
                new_name = st.text_input("Leave Name", key="new_leave_name")
            with col_paid:
                st.write("") # Spacer
                st.write("") # Spacer
                new_is_paid = st.checkbox("Paid Leave", value=True, key="new_leave_paid")
                
            new_desc = st.text_input("Description", key="new_leave_desc")
            new_color = st.color_picker("Color", "#E0E0E0", key="new_leave_color")
            
            if st.form_submit_button("Add Leave Type", use_container_width=True):
                if new_code and new_name:
                    if any(l['code'] == new_code for l in st.session_state.leaves):
                        notify("Add Leave Type Failed", detail="Leave code already exists!", type="error")
                        st.rerun()
                    else:
                        new_leave = {
                            "code": new_code,
                            "name": new_name,
                            "description": new_desc,
                            "color": new_color,
                            "is_paid": new_is_paid
                        }
                        st.session_state.leaves.append(new_leave)
                        save_data("leaves", LEAVES_DATA_FILE, st.session_state.leaves)
                        notify("Leave Type added successfully:", detail=f"{new_code} - {new_name}")
                        
                        # Clear form state and refresh
                        reset_form_keys(["new_leave_code", "new_leave_name", "new_leave_paid", 
                                       "new_leave_desc", "new_leave_color"])
                else:
                    notify("Action Failed", detail="Code and Name are required.", type="warning")

    st.markdown("---")
    st.subheader("Current Leave Types")
    
    # --- Bulk Actions ---
    selected_for_deletion = [l['code'] for l in st.session_state.leaves if st.session_state.get(f"bulk_del_leave_{l['code']}", False)]
    if selected_for_deletion:
        if st.button(f"🗑️ Delete {len(selected_for_deletion)} Selected Leaves", type="primary"):
            for code in selected_for_deletion:
                try: supabase.table("leaves").delete().eq("code", code).execute()
                except: pass
            st.session_state.leaves = [l for l in st.session_state.leaves if l['code'] not in selected_for_deletion]
            save_data("leaves", LEAVES_DATA_FILE, st.session_state.leaves)
            for code in selected_for_deletion:
                if f"bulk_del_leave_{code}" in st.session_state: del st.session_state[f"bulk_del_leave_{code}"]
            notify("Bulk Delete Successful", detail=f"Removed {len(selected_for_deletion)} leave types.")
            st.rerun()
            
    for i, leave in enumerate(st.session_state.leaves):
        l_col_cb, l_col_exp = st.columns([0.5, 9.5])
        with l_col_cb:
            st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
            st.checkbox("", key=f"bulk_del_leave_{leave['code']}", label_visibility="collapsed")
        with l_col_exp:
            with st.expander(f"[{leave['code']}] {leave['name']}", expanded=False):
                col_code, col_name, col_paid = st.columns([1, 2, 1])
                updated = False
                
                with col_code:
                    edit_code = st.text_input("Code", value=leave.get('code', ''), max_chars=5, key=f"leave_code_{i}")
                    
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
                    if edit_code != leave.get('code') or edit_name != leave.get('name') or edit_paid != leave.get('is_paid') or edit_desc != leave.get('description') or edit_color != leave.get('color'):
                        if st.button("Save Changes", key=f"save_leave_{i}", use_container_width=True):
                            old_code = leave.get('code')
                            if edit_code != old_code and any(l['code'] == edit_code for l in st.session_state.leaves):
                                notify("Update Failed", detail="Leave code already exists!", type="error")
                                st.rerun()
                            else:
                                if edit_code != old_code:
                                    try: supabase.table("leaves").update({"code": edit_code}).eq("code", old_code).execute()
                                    except: pass
                                
                                leave['code'] = edit_code
                                leave['name'] = edit_name
                                leave['is_paid'] = edit_paid
                                leave['description'] = edit_desc
                                leave['color'] = edit_color
                            
                                save_data("leaves", LEAVES_DATA_FILE, st.session_state.leaves)
                                notify("Leave type updated successfully:", detail=f"Changes for '{leave['name']}' saved")
                                st.rerun()
                with col_del:
                    if st.button("Delete Type", key=f"del_leave_{i}", type="primary", use_container_width=True):
                        deleted_leave = st.session_state.leaves[i]['name']
                        try:
                            supabase.table("leaves").delete().eq("code", leave.get('code')).execute()
                        except: pass
                        st.session_state.leaves.pop(i)
                        save_data("leaves", LEAVES_DATA_FILE, st.session_state.leaves)
                        notify("Leave type deleted successfully:", detail=f"'{deleted_leave}' removed")
                        st.rerun()

# ---------------------------------------------------------------------
# Staff Management Dialogs
# ---------------------------------------------------------------------

@st.dialog("Edit Employee")
def edit_staff_dialog(staff_member):
    st.write(f"Editing: **{staff_member['name']}** ({staff_member['employee_id']})")
    
    with st.form("edit_staff_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Name", value=staff_member['name'])
        with c2:
            new_id = st.text_input("Employee ID", value=staff_member['employee_id'])
        
        # Grade
        all_grades = [g['code'] for layer in st.session_state.grades for g in layer]
        if not all_grades: all_grades = ["RN"]
        curr_grade_idx = all_grades.index(staff_member['grade']) if staff_member['grade'] in all_grades else 0
        new_grade = st.selectbox("Grade", all_grades, index=curr_grade_idx)
        
        # Department
        dept_names = [d['name'] for d in st.session_state.departments]
        dept_ids = [d['id'] for d in st.session_state.departments]
        curr_dept_idx = dept_ids.index(staff_member.get('department_id')) if staff_member.get('department_id') in dept_ids else 0
        new_dept_idx = st.selectbox("Department", range(len(dept_names)), format_func=lambda idx: dept_names[idx], index=curr_dept_idx)
        
        # Skills
        st.write("Skills")
        skill_options = [f"{skill['code']}" for skill in st.session_state.skills]
        curr_skills = set(staff_member.get('skills', []))
        with st.popover("Select Skills...", use_container_width=True):
            new_skills_dict = {sk: st.checkbox(sk, value=(sk in curr_skills), key=f"es_{staff_member['employee_id']}_{sk}") for sk in skill_options}
        new_skills = [sk for sk, checked in new_skills_dict.items() if checked]
        
        # Constraints
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            new_night = st.toggle("Allow Night Shifts", value=staff_member.get('allow_night_shift', True))
        with c2:
            new_consec = st.number_input("Max Consecutive Days", min_value=1, max_value=14, value=staff_member.get('max_consecutive_work_days', 6))
            
        if st.form_submit_button("Save Changes", use_container_width=True):
            # If the user changed the grade but left the ID as the old one, auto-generate a new ID
            if new_grade != staff_member['grade'] and new_id == staff_member['employee_id']:
                prefix = f"{new_grade}-"
                max_num = 0
                for n in st.session_state.nurses:
                    n_id = n.get('employee_id', '')
                    if n_id.startswith(prefix):
                        suffix = n_id[len(prefix):]
                        if suffix.isdigit():
                            max_num = max(max_num, int(suffix))
                new_id = f"{prefix}{max_num + 1:02d}"

            if new_id != staff_member['employee_id'] and any(n['employee_id'] == new_id for n in st.session_state.nurses):
                st.error(f"Employee ID {new_id} already exists!")
                return
                
            updates = {
                "employee_id": new_id,
                "name": new_name,
                "grade": new_grade,
                "department_id": dept_ids[new_dept_idx],
                "skills": new_skills,
                "allow_night_shift": new_night,
                "max_consecutive_work_days": int(new_consec)
            }
            try:
                staff_db.update_staff(supabase, staff_member['employee_id'], updates)
                # Refresh session state
                updated_staff = staff_db.fetch_all_staff(supabase)
                for s in updated_staff: 
                    s['id'] = s['employee_id'] # Map for compatibility
                st.session_state.nurses = updated_staff
                notify("Employee Updated", f"Changes saved for {new_name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating staff: {e}")

@st.dialog("Delete Employee")
def delete_staff_dialog(staff_member):
    st.warning(f"Are you sure you want to delete **{staff_member['name']}**?")
    st.write(f"Employee ID: {staff_member['employee_id']}")
    st.write("This action cannot be undone and will affect future rosters.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("Delete", type="primary", use_container_width=True):
            try:
                staff_db.delete_staff(supabase, staff_member['employee_id'])
                # Refresh session state
                updated_staff = staff_db.fetch_all_staff(supabase)
                for s in updated_staff: 
                    s['id'] = s['employee_id'] # Map for compatibility
                st.session_state.nurses = updated_staff
                notify("Employee Deleted", f"{staff_member['name']} has been removed.")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting staff: {e}")

def render_manage_staffs():
    st.subheader("👥 Personnel Management")
    
    # --- Custom CSS for Table Styling ---
    st.markdown("""
        <style>
        .staff-table-header {
            display: flex;
            background-color: #F8F9FA;
            padding: 12px 10px;
            border-radius: 8px 8px 0 0;
            font-weight: 700;
            border-bottom: 2px solid #DEE2E6;
            color: #333;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .staff-row {
            padding: 12px 10px;
            border-bottom: 1px solid #EEE;
            transition: background 0.2s ease;
        }
        .staff-row:hover {
            background-color: #F1F3F5;
        }
        [data-testid="stVerticalBlock"] > div:has(div.staff-row) {
            gap: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. Add New Employee Form
    with st.expander("➕ Add New Employee", expanded=False):
        with st.form("add_staff_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                add_name = st.text_input("Name", placeholder="Full Name", key="add_staff_name")
            with c2:
                add_id = st.text_input("Employee ID", placeholder="Leave blank to auto-generate", key="add_staff_id")
            with c3:
                all_grades = [g['code'] for layer in st.session_state.grades for g in layer]
                add_grade = st.selectbox("Grade", all_grades if all_grades else ["RN"], key="add_staff_grade")
            
            c4, c5 = st.columns([2, 1])
            with c4:
                dept_names = [d['name'] for d in st.session_state.departments]
                dept_ids = [d['id'] for d in st.session_state.departments]
                add_dept_idx = st.selectbox("Department", range(len(dept_names)), format_func=lambda i: dept_names[i], key="add_staff_dept")
            with c5:
                skill_options = [skill['code'] for skill in st.session_state.skills]
                st.write("**Skills**")
                with st.popover("Select Skills...", use_container_width=True):
                    add_skills_dict = {sk: st.checkbox(sk, key=f"as_skill_{sk}") for sk in skill_options}
                add_skills = [sk for sk, checked in add_skills_dict.items() if checked]
            
            st.write("---")
            cc1, cc2 = st.columns(2)
            with cc1:
                add_night = st.toggle("Allow Night Shifts", value=True, key="add_staff_night")
            with cc2:
                add_consec = st.number_input("Max Consecutive Days", min_value=1, max_value=14, value=6, key="add_staff_consec")
                
            if st.form_submit_button("Add Personnel", use_container_width=True):
                # Auto-generate ID if left blank
                if not add_id:
                    prefix = f"{add_grade}-"
                    max_num = 0
                    for n in st.session_state.nurses:
                        n_id = n.get('employee_id', '')
                        if n_id.startswith(prefix):
                            suffix = n_id[len(prefix):]
                            if suffix.isdigit():
                                max_num = max(max_num, int(suffix))
                    add_id = f"{prefix}{max_num + 1:02d}"
                
                if add_name and add_id:
                    # Check if ID already exists in session state to prevent duplicates before DB call
                    if any(n['employee_id'] == add_id for n in st.session_state.nurses):
                        st.error(f"Employee ID {add_id} already exists!")
                    else:
                        new_record = {
                            "employee_id": add_id,
                            "name": add_name,
                            "grade": add_grade,
                            "department_id": dept_ids[add_dept_idx],
                            "skills": add_skills,
                            "allow_night_shift": add_night,
                            "max_consecutive_work_days": int(add_consec),
                            "leave_days": []
                        }
                        try:
                            staff_db.insert_staff(supabase, new_record)
                            updated_staff = staff_db.fetch_all_staff(supabase)
                            for s in updated_staff: s['id'] = s['employee_id']
                            st.session_state.nurses = updated_staff
                            notify("Employee Added", f"{add_name} added successfully.")
                            
                            # Clear form keys
                            keys_to_reset = ["add_staff_name", "add_staff_id", "add_staff_grade", "add_staff_dept", "add_staff_night", "add_staff_consec"] + [f"as_skill_{sk}" for sk in skill_options]
                            reset_form_keys(keys_to_reset)
                        except Exception as e:
                            st.error(f"Error adding staff: {e}")
                else:
                    st.error("Name and Employee ID are required.")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Search, Filter, and Sort Bar
    with st.container(border=True):
        sb1, sb2, sb3, sb4, sb5 = st.columns([2, 1, 1, 2, 1.2])
        with sb1:
            search_query = st.text_input("🔍 Search", placeholder="Name or ID").lower()
        with sb2:
            grade_filter = st.selectbox("Grade", ["All"] + sorted(list(set(n.get('grade', 'RN') for n in st.session_state.nurses))))
        with sb3:
            dept_names_map = {d['id']: d['name'] for d in st.session_state.departments}
            dept_ids_list = ["All"] + [d['id'] for d in st.session_state.departments]
            dept_filter_id = st.selectbox("Department", dept_ids_list, format_func=lambda x: dept_names_map.get(x, "All"))
        with sb4:
            skill_options = sorted(list(set(sk['code'] for sk in st.session_state.skills)))
            skill_filter = st.multiselect("Filter by Skills", options=skill_options)
        with sb5:
            sort_by = st.selectbox("Sort By", ["Name", "ID"])

    # 3. Filtering and Sorting Logic
    filtered_staff = st.session_state.nurses
    if search_query:
        filtered_staff = [n for n in filtered_staff if search_query in n['name'].lower() or search_query in n['employee_id'].lower()]
    if grade_filter != "All":
        filtered_staff = [n for n in filtered_staff if n.get('grade') == grade_filter]
    if dept_filter_id != "All":
        filtered_staff = [n for n in filtered_staff if n.get('department_id') == dept_filter_id]
    if skill_filter:
        filtered_staff = [n for n in filtered_staff if all(skill in n.get('skills', []) for skill in skill_filter)]
    
    if sort_by == "Name":
        filtered_staff = sorted(filtered_staff, key=lambda x: x['name'])
    else:
        filtered_staff = sorted(filtered_staff, key=lambda x: x['employee_id'])

    # 4. Table Display with Scrollable Body
    
    # --- Bulk Actions ---
    selected_for_deletion = [s['employee_id'] for s in filtered_staff if st.session_state.get(f"bulk_del_{s['employee_id']}", False)]
    if selected_for_deletion:
        if st.button(f"🗑️ Delete {len(selected_for_deletion)} Selected Personnel", type="primary"):
            for emp_id in selected_for_deletion:
                try: staff_db.delete_staff(supabase, emp_id)
                except: pass
            st.session_state.nurses = staff_db.fetch_all_staff(supabase)
            for s in st.session_state.nurses: s['id'] = s['employee_id']
            # Clear checkboxes
            for emp_id in selected_for_deletion:
                if f"bulk_del_{emp_id}" in st.session_state: del st.session_state[f"bulk_del_{emp_id}"]
            notify("Bulk Delete Successful", detail=f"Removed {len(selected_for_deletion)} personnel.")
            st.rerun()
            
    # Header
    st.markdown("""
        <div class='staff-table-header'>
            <div style='flex: 0.5;'>☑️</div>
            <div style='flex: 2;'>Name</div>
            <div style='flex: 1.5;'>Employee ID</div>
            <div style='flex: 1;'>Grade</div>
            <div style='flex: 1.5;'>Department</div>
            <div style='flex: 2.5;'>Skills</div>
            <div style='flex: 1; text-align: center;'>Actions</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Body
    with st.container(height=500, border=False):
        if not filtered_staff:
            st.info("No personnel found matching the current criteria.")
        else:
            for idx, s in enumerate(filtered_staff):
                with st.container():
                    st.markdown("<div class='staff-row'>", unsafe_allow_html=True)
                    r_col_cb, r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([0.5, 2, 1.5, 1, 1.5, 2.5, 1])
                    
                    with r_col_cb:
                        st.checkbox("", key=f"bulk_del_{s['employee_id']}", label_visibility="collapsed")
                    with r_col1:
                        st.write(f"**{s['name']}**")
                    with r_col2:
                        st.write(f"`{s['employee_id']}`")
                    with r_col3:
                        st.write(s.get('grade', 'RN'))
                    with r_col4:
                        st.write(dept_names_map.get(s.get('department_id'), 'Unassigned'))
                    with r_col5:
                        skills = s.get('skills', [])
                        if skills:
                            skill_html = "".join([f"<span style='background: #E9ECEF; color: #495057; padding: 2px 6px; border-radius: 4px; font-size: 0.75em; margin-right: 4px; border: 1px solid #DEE2E6;'>{sk}</span>" for sk in skills])
                            st.markdown(skill_html, unsafe_allow_html=True)
                        else:
                            st.write("<span style='color: #ADB5BD; font-size: 0.8em;'>None</span>", unsafe_allow_html=True)
                    
                    with r_col6:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✏️", key=f"edit_{s['employee_id']}_{idx}", help="Edit"):
                                edit_staff_dialog(s)
                        with btn_col2:
                            if st.button("🗑️", key=f"del_{s['employee_id']}_{idx}", help="Delete"):
                                delete_staff_dialog(s)
                    st.markdown("</div>", unsafe_allow_html=True)

def render_manage_skills():
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
                new_skill_code = st.text_input("Code", max_chars=5, help="e.g., ICU, ER", key="new_skill_code")
            with col2:
                new_skill_name = st.text_input("Name", help="e.g., ICU Care", key="new_skill_name")
            
            new_skill_desc = st.text_area("Description", help="Brief description", key="new_skill_desc")
            new_skill_color = st.color_picker("Color", "#F0F4F8", key="new_skill_color")

            if st.form_submit_button("Add Skill", use_container_width=True):
                if new_skill_code and new_skill_name:
                    if any(s['code'] == new_skill_code for s in st.session_state.skills):
                        notify("Add Skill Failed", detail="Skill code already exists!", type="error")
                        st.rerun()
                    else:
                        new_skill = {
                            "code": new_skill_code,
                            "name": new_skill_name,
                            "description": new_skill_desc if new_skill_desc else "",
                            "color": new_skill_color,
                            "id": f"skill_{new_skill_code}_{datetime.now().timestamp()}"
                        }
                        st.session_state.skills.append(new_skill)
                        st.session_state.skills.sort(key=lambda x: x['code'].upper())
                        save_data("skills", SKILLS_DATA_FILE, st.session_state.skills)
                        notify("Skill added successfully:", detail=f"{new_skill_code} - {new_skill_name}")
                        
                        # Clear form keys
                        reset_form_keys(["new_skill_code", "new_skill_name", "new_skill_desc", "new_skill_color"])
                else:
                    notify("Action Failed", detail="Code and Name are required.", type="warning")

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
                            <div class="skill-code" style="background-color: {skill.get('color', '#F0F4F8')}66; border: 2px solid {skill.get('color', '#F0F4F8')}; color: #333">
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
                        deleted_skill = st.session_state.skills[i]['name']
                        try:
                            supabase.table("skills").delete().eq("code", skill['code']).execute()
                        except: pass
                        st.session_state.skills.pop(i)
                        save_data("skills", SKILLS_DATA_FILE, st.session_state.skills)
                        notify("Skill deleted successfully:", detail=f"'{deleted_skill}' removed")
                        st.rerun()

            # --- Inline Edit Form ---
            if st.session_state.editing_skill_id == skill['id']:
                with st.form(f"edit_skill_form_{stable_key}"):
                    st.write(f"**Edit Skill: {skill['code']}**")
                    e_col1, e_col2 = st.columns([1, 2])
                    edit_code = e_col1.text_input("Code", value=skill['code'], max_chars=5)
                    edit_name = e_col2.text_input("Name", value=skill['name'])
                    edit_desc = st.text_area("Description", value=skill.get('description', ''))
                    edit_color = st.color_picker("Color", value=skill.get('color', '#F0F4F8'))
                    
                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        if st.form_submit_button("✅ Save Changes", use_container_width=True):
                            old_code = skill['code']
                            if edit_code != old_code and any(s['code'] == edit_code for s in st.session_state.skills):
                                notify("Update Failed", detail="Skill code already exists!", type="error")
                                st.rerun()
                            else:
                                if edit_code != old_code:
                                    try: supabase.table("skills").update({"code": edit_code}).eq("code", old_code).execute()
                                    except: pass
                                    for n in st.session_state.nurses:
                                        if old_code in n.get('skills', []):
                                            n['skills'] = [edit_code if sk == old_code else sk for sk in n['skills']]
                                    import threading
                                    threading.Thread(target=save_data, args=("nurses", NURSES_DATA_FILE, st.session_state.nurses)).start()
                                
                                skill['code'] = edit_code
                                skill['name'] = edit_name
                                skill['description'] = edit_desc
                                skill['color'] = edit_color
                                st.session_state.skills.sort(key=lambda x: x['code'].upper())
                                save_data("skills", SKILLS_DATA_FILE, st.session_state.skills)
                                st.session_state.editing_skill_id = None
                                notify("Skill updated successfully:", detail=f"{edit_code} - {edit_name}")
                                st.rerun()
                    with f_col2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state.editing_skill_id = None
                            st.rerun()
                st.markdown("---")

def render_manage_departments():
    # --- Custom Styling for Department Cards ---
    st.markdown("""
    <style>
    .dept-card {
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
    .dept-card:hover {
        border-color: #DDE;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        transform: translateY(-2px);
    }
    .dept-info {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .dept-icon {
        font-size: 1.5rem;
        padding: 4px 10px;
        border-radius: 6px;
        background-color: #E8F4FD;
        border: 2px solid #B3D9F2;
        min-width: 50px;
        text-align: center;
    }
    .dept-name {
        font-weight: 600;
        color: #333;
        font-size: 1.05rem;
    }
    .dept-count {
        font-size: 0.85rem;
        color: #666;
    }
    </style>
    """, unsafe_allow_html=True)

    st.write("Create and manage departments. Staff members are assigned to one primary department.")
    with st.expander("Add New Department", expanded=False):
        with st.form("add_department_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                new_dept_id = st.text_input("Department ID", help="e.g., ICU, ER, CARD", key="new_dept_id")
            with col2:
                new_dept_name = st.text_input("Department Name", help="e.g., ICU, Emergency, Cardiology", key="new_dept_name")

            if st.form_submit_button("Add Department", use_container_width=True):
                if new_dept_id and new_dept_name:
                    if any(d['id'].lower() == new_dept_id.lower() for d in st.session_state.departments):
                        notify("Add Department Failed", detail="A department with this ID already exists!", type="error")
                        st.rerun()
                    elif any(d['name'].lower() == new_dept_name.lower() for d in st.session_state.departments):
                        notify("Add Department Failed", detail="A department with this name already exists!", type="error")
                        st.rerun()
                    else:
                        new_dept = {
                            "id": new_dept_id,
                            "name": new_dept_name,
                            "description": ""
                        }
                        st.session_state.departments.append(new_dept)
                        st.session_state.departments.sort(key=lambda x: x['name'].upper())
                        save_data("departments", DEPARTMENTS_DATA_FILE, st.session_state.departments)
                        notify("Department added successfully:", detail=f"[{new_dept_id}] {new_dept_name} created")
                        
                        # Clear form keys
                        reset_form_keys(["new_dept_id", "new_dept_name"])
                else:
                    notify("Action Failed", detail="ID and Name are required.", type="warning")

    st.markdown("---")
    st.subheader("Available Departments")

    if 'editing_dept_id' not in st.session_state:
        st.session_state.editing_dept_id = None

    if not st.session_state.departments:
        st.info("No departments defined yet. Add your first department above.")
    else:
        # --- Bulk Actions ---
        selected_for_deletion = [d['id'] for d in st.session_state.departments if st.session_state.get(f"bulk_del_dept_{d['id']}", False)]
        if selected_for_deletion:
            if st.button(f"🗑️ Delete {len(selected_for_deletion)} Selected Departments", type="primary"):
                safe_to_delete = []
                for dept_id in selected_for_deletion:
                    if sum(1 for n in st.session_state.nurses if n.get('department_id') == dept_id) == 0:
                        safe_to_delete.append(dept_id)
                
                if len(safe_to_delete) < len(selected_for_deletion):
                    notify("Partial Deletion", detail=f"{len(selected_for_deletion) - len(safe_to_delete)} departments could not be deleted because staff are assigned to them.", type="warning")
                
                for dept_id in safe_to_delete:
                    try: supabase.table("departments").delete().eq("id", dept_id).execute()
                    except: pass
                
                st.session_state.departments = [d for d in st.session_state.departments if d['id'] not in safe_to_delete]
                save_data("departments", DEPARTMENTS_DATA_FILE, st.session_state.departments)
                
                for dept_id in selected_for_deletion:
                    if f"bulk_del_dept_{dept_id}" in st.session_state: del st.session_state[f"bulk_del_dept_{dept_id}"]
                if safe_to_delete: notify("Bulk Delete Successful", detail=f"Removed {len(safe_to_delete)} departments.")
                st.rerun()

        for i, dept in enumerate(st.session_state.departments):
            # Count nurses in this department
            nurse_count = sum(1 for n in st.session_state.nurses if n.get('department_id') == dept['id'])

            with st.container():
                card_cols = st.columns([0.5, 7.5, 0.8, 0.8])
                
                with card_cols[0]:
                    st.markdown("<div style='padding-top: 25px;'></div>", unsafe_allow_html=True)
                    st.checkbox("", key=f"bulk_del_dept_{dept['id']}", label_visibility="collapsed")

                with card_cols[1]:
                    st.markdown(f"""
                    <div class="dept-card" style="margin-bottom: 0; border: none; box-shadow: none; padding: 0;">
                        <div class="dept-info">
                            <div class="dept-icon" style="font-size: 1rem; border: 2px solid #B3D9F2; background: #E8F4FD; padding: 4px 8px; border-radius: 6px; font-family: monospace;">{dept['id']}</div>
                            <div>
                                <span class="dept-name">{dept['name']}</span><br>
                                <span class="dept-count">{nurse_count} staff member{'s' if nurse_count != 1 else ''}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with card_cols[2]:
                    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("✏️", key=f"edit_dept_{dept['id']}", help="Edit Department"):
                        st.session_state.editing_dept_id = dept['id']

                with card_cols[3]:
                    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_dept_{dept['id']}", help="Delete Department"):
                        if nurse_count > 0:
                            notify("Delete Failed", detail=f"Cannot delete '{dept['name']}' — {nurse_count} staff member{'s are' if nurse_count != 1 else ' is'} still assigned. Reassign them first.", type="error")
                            st.rerun()
                        else:
                            deleted_name = dept['name']
                            try:
                                supabase.table("departments").delete().eq("id", dept['id']).execute()
                            except: pass
                            st.session_state.departments.pop(i)
                            save_data("departments", DEPARTMENTS_DATA_FILE, st.session_state.departments)
                            notify("Department deleted successfully:", detail=f"'{deleted_name}' removed")
                            st.rerun()

            # --- Inline Edit Form ---
            if st.session_state.editing_dept_id == dept['id']:
                with st.form(f"edit_dept_form_{dept['id']}"):
                    st.write(f"**Edit Department: {dept['name']}**")
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        edit_id = st.text_input("ID", value=dept['id'])
                    with col2:
                        edit_name = st.text_input("Name", value=dept['name'])

                    f_col1, f_col2 = st.columns(2)
                    with f_col1:
                        if st.form_submit_button("✅ Save Changes", use_container_width=True):
                            old_id = dept['id']
                            if edit_id != old_id and any(d['id'].lower() == edit_id.lower() for d in st.session_state.departments):
                                notify("Update Failed", detail="A department with this ID already exists!", type="error")
                                st.rerun()
                            elif edit_name != dept['name'] and any(d['name'].lower() == edit_name.lower() for d in st.session_state.departments if d['id'] != old_id):
                                notify("Update Failed", detail="A department with this name already exists!", type="error")
                                st.rerun()
                            else:
                                if edit_id != old_id:
                                    # Rename the ID directly in supabase to cascade FOREIGN KEY changes
                                    try: supabase.table("departments").update({"id": edit_id}).eq("id", old_id).execute()
                                    except: pass
                                    # Cascade locally to nurses
                                    for n in st.session_state.nurses:
                                        if n.get("department_id") == old_id:
                                            n["department_id"] = edit_id
                                    # Background save nurses to sync the local cascade
                                    import threading
                                    threading.Thread(target=save_data, args=("nurses", NURSE_DATA_FILE, st.session_state.nurses)).start()
                                    
                                dept['id'] = edit_id
                                dept['name'] = edit_name
                                st.session_state.departments.sort(key=lambda x: x['name'].upper())
                                save_data("departments", DEPARTMENTS_DATA_FILE, st.session_state.departments)
                                
                                st.session_state.editing_dept_id = None
                                notify("Department updated successfully:", detail=f"[{edit_id}] {edit_name}")
                                st.rerun()
                    with f_col2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state.editing_dept_id = None
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
                        if pd.notna(row.get('Skill')) and pd.notna(row.get('Min Count')):
                            try:
                                # Clamp min count to total
                                count = min(int(row['Min Count']), new_total)
                                new_skill_dict[row['Skill']] = count
                            except (ValueError, TypeError):
                                continue
                    st.session_state.demand["default"][shift_code] = new_skill_dict
                else:
                    if st.button(f"Add Skill Requirement...", key=f"add_skill_btn_{shift_code}"):
                        st.session_state.demand["default"][shift_code][st.session_state.skills[0]['code']] = 1
                        notify("Skill requirement added:", detail="Please select the skill and count in the table below")
                        st.rerun()

        if st.button("Save Default Demand", type="primary"):
            save_data("demand", DEMAND_DATA_FILE, st.session_state.demand)
            notify("Default demand saved:", detail="Minimum coverage requirements updated successfully")
            st.rerun()

    with tab2:
        st.write("Modify requirements for **specific dates**.")
        target_date = st.date_input("Select Date", value=st.session_state.roster_start_date, min_value=st.session_state.roster_start_date, max_value=st.session_state.roster_end_date)
        date_str = target_date.strftime("%Y-%m-%d")

        # Load current override or copy from default if new
        if st.button("Create/Edit Override for this Date", key="btn_create_ov"):
            if date_str not in st.session_state.demand["overrides"]:
                st.session_state.demand["overrides"][date_str] = json.loads(json.dumps(st.session_state.demand["default"]))
                notify("Override created:", detail=f"Custom requirements set for {date_str}")
            else:
                notify("Editing Override:", detail=f"Loading existing requirements for {date_str}")
            st.rerun()

        if date_str in st.session_state.demand["overrides"]:
            # Keeping the warning as a clear indicator of state while editing
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
                        if pd.notna(row.get('Skill')) and pd.notna(row.get('Min Count')):
                            try:
                                count = min(int(row['Min Count']), ov_total)
                                new_ov_dict[row['Skill']] = count
                            except (ValueError, TypeError):
                                continue
                    st.session_state.demand["overrides"][date_str][shift_code] = new_ov_dict

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Override", type="primary"):
                    save_data("demand", DEMAND_DATA_FILE, st.session_state.demand)
                    notify("Override saved:", detail=f"Custom requirements for {date_str} updated")
                    st.rerun()
            with col2:
                if st.button("Delete Override", type="secondary"):
                    del st.session_state.demand["overrides"][date_str]
                    save_data("demand", DEMAND_DATA_FILE, st.session_state.demand)
                    notify("Override deleted:", detail=f"Custom requirements for {date_str} removed")
                    st.rerun()
        else:
            st.info("No override set for this date. Default demand will be used.")


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Generate Schedule'

with st.sidebar:

    st.markdown('### Main Page')
    st.button("🚀 Generate Schedule", on_click=lambda: st.session_state.update(current_page='Generate Schedule'), use_container_width=True, type="primary")

    st.markdown('### Settings')

    with st.expander("⚙️ General Settings", expanded=False):
        st.button("🎨 Theme", on_click=lambda: st.session_state.update(current_page='Theme'), use_container_width=True)
        st.button("ℹ️ Hard Constraints", on_click=lambda: st.session_state.update(current_page='Hard Constraints'), use_container_width=True)
        st.button("⚖️ Soft Constraints", on_click=lambda: st.session_state.update(current_page='Soft Constraints'), use_container_width=True)

    with st.expander("🔐 Admin Database", expanded=False):
        st.button("🏢 Manage Departments", on_click=lambda: st.session_state.update(current_page='Manage Departments'), use_container_width=True)
        st.button("🗓️ Manage Shifts", on_click=lambda: st.session_state.update(current_page='Manage Shifts'), use_container_width=True)
        st.button("🔧 Manage Skills", on_click=lambda: st.session_state.update(current_page='Manage Skills'), use_container_width=True)
        st.button("🏆 Grades Hierarchy", on_click=lambda: st.session_state.update(current_page='Grades Hierarchy'), use_container_width=True)
        st.button("🏖️ Leave Types", on_click=lambda: st.session_state.update(current_page='Leave Types'), use_container_width=True)
        st.button("👥 Manage Staffs", on_click=lambda: st.session_state.update(current_page='Manage Staffs'), use_container_width=True)
        st.button("📊 Minimum Demand", on_click=lambda: st.session_state.update(current_page='Minimum Demand'), use_container_width=True)

    st.markdown("---")
    if st.sidebar.button("✨ Reset Tutorial", use_container_width=True):
        tutorial_manager.reset_tutorial()
        st.rerun()

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
                notify("Theme changed successfully:", detail=f"Applied {theme_name} theme to the application")
                st.rerun()
        with col2:
            st.write(theme_descriptions[theme_name])

    st.caption(f"Current theme: **{st.session_state.theme}**")


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

elif st.session_state.current_page == 'Manage Departments':
    st.header("Manage Departments")
    render_manage_departments()

elif st.session_state.current_page == 'Minimum Demand':
    st.header("Minimum Demand")
    render_manage_demand()

elif st.session_state.current_page == 'Hard Constraints':
    st.header("🛡️ Hard Constraints")
    st.write("These rules are **always** enforced — the solver will never violate them. If a solution is found, you can be 100% sure these rules were respected.")

    st.markdown('''
### 🚫 Strict Work Rules
- **Max 6 Shifts/Week:** No nurse works more than 6 days in a static **Monday-to-Sunday** week. This ensures at least one day off per calendar week.
- **Max 7 Consecutive Days:** No nurse works more than 7 days in a row, even if those days span across two different weeks.
- **Max 1 Shift/Day:** No nurse works more than 1 shift per day.
- **Leave Compliance:** Nurses on leave are not assigned.

### 🌙 Night Shift Recovery
The system enforces strict recovery periods after working night shifts to ensure staff well-being:
- **Max 4 consecutive night shifts.**
- **1 Night** → 1 Day Off
- **2-3 Nights** → 2 Days Off
- **4 Nights** → 3 Days Off
    ''')

elif st.session_state.current_page == 'Soft Constraints':
    st.header("⚖️ Soft Constraints (Scheduling Priorities)")
    st.write("Adjust the priorities below to guide the optimization. These are goals the solver tries to achieve while respecting all Hard Constraints.")
    
    with st.container(border=True):
        st.subheader("🎯 Optimization Weights")
        st.write("Higher values give more priority to each goal. Use these to balance workload and utilization.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.session_state.schedule_weights['utilization'] = st.slider(
                "📈 **Maximize Utilization**", 1, 10, st.session_state.schedule_weights.get('utilization', 10),
                help="Assign extra nurses to shifts beyond minimums if capacity allows.",
                key="soft_wt_util"
            )
            st.session_state.schedule_weights['overall_fairness'] = st.slider(
                "⚖️ **Overall Fairness**", 1, 10, st.session_state.schedule_weights.get('overall_fairness', 5),
                help="Balance total number of shifts among all staff.",
                key="soft_wt_fair"
            )
        with col_w2:
            st.session_state.schedule_weights['night_fairness'] = st.slider(
                "🌙 **Night Shift Fairness**", 1, 10, st.session_state.schedule_weights.get('night_fairness', 5),
                help="Distribute night shifts as evenly as possible.",
                key="soft_wt_night"
            )
            st.session_state.schedule_weights['weekend_fairness'] = st.slider(
                "🗓️ **Weekend Fairness**", 1, 10, st.session_state.schedule_weights.get('weekend_fairness', 5),
                help="Distribute Saturday/Sunday shifts evenly.",
                key="soft_wt_weekend"
            )
        
        if st.button("💾 Save Priority Settings", type="primary", use_container_width=True):
            notify("Settings Saved", detail="Scheduling priorities have been updated and will be used for the next generation.")
            # Weights are already in session_state via the keys, but we ensure they persist if needed.
            st.rerun()

    st.info("💡 **Tip:** If you care most about staff satisfaction, increase the Fairness weights. If you have a high patient load, increase the Utilization weight.")


elif st.session_state.current_page == 'Generate Schedule':
    st.header("Generate Schedule")
    
    # --- 0. Local Date & Data Sync ---
    roster_start = st.session_state.roster_start_date
    roster_end = st.session_state.roster_end_date
    planning_horizon = (roster_end - roster_start).days + 1
    date_labels = [(roster_start + timedelta(days=d)).strftime("%a, %b %d") for d in range(planning_horizon)]

    # --- 1. Schedule Setup Section (Top) ---
    with st.container(border=True):
        st.subheader("🛠️ Schedule Setup")
        col_s1, col_s2 = st.columns([1, 1])
        
        with col_s1:
            dept_options = {d['id']: d['name'] for d in st.session_state.departments}
            selected_dept_id = st.selectbox(
                "Select Department",
                options=list(dept_options.keys()),
                format_func=lambda x: dept_options[x],
                key="gen_dept_selector"
            )
            selected_dept_name = dept_options.get(selected_dept_id, "Unknown")
            
            # Filter nurses for display metrics
            dept_nurses = [n for n in st.session_state.nurses if n.get('department_id') == selected_dept_id]
            st.info(f"👥 **{len(dept_nurses)}** Nurses | 📅 **{planning_horizon}** Days")

        with col_s2:
            selected_range = st.date_input(
                "Roster Period",
                value=(roster_start, roster_end),
                min_value=date(2024, 1, 1),
                max_value=date(2026, 12, 31),
                key="gen_date_picker"
            )
            if isinstance(selected_range, tuple) and len(selected_range) == 2:
                if selected_range[0] != roster_start or selected_range[1] != roster_end:
                    st.session_state.roster_start_date, st.session_state.roster_end_date = selected_range
                    st.session_state.last_schedule = None # Reset to trigger auto-load/fresh gen
                    st.rerun()
            st.write(f"**Selected Range:** {roster_start.strftime('%d %b')} – {roster_end.strftime('%d %b')}")

        st.markdown("<br>", unsafe_allow_html=True)
        gen_btn = st.button("🚀 Generate Optimized Schedule", type="primary", use_container_width=True)

    # --- 2. Scheduling Priorities Section ---
    with st.expander("📝 Scheduling Priorities & Rules", expanded=False):
        st.write("The algorithm optimizes for the following rules and constraints:")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.checkbox("✅ Coverage requirements per day", value=True, disabled=True)
            st.checkbox("✅ Fair shift distribution (Utilization)", value=True, disabled=True)
            st.checkbox("✅ Night shift balancing", value=True, disabled=True)
        with p_col2:
            st.checkbox("✅ Weekend shift balancing", value=True, disabled=True)
            st.checkbox("✅ Locked shifts respected", value=True, disabled=True)
            st.checkbox("✅ Leave requests respected", value=True, disabled=True)
        st.caption("💡 Adjust priority weights in **General Settings > Soft Constraints**.")

    # --- 3. Automated Roster Loading ---
    def fetch_latest_roster(dept_id, start, end):
        try:
            res = supabase.table("rosters").select("*") \
                .eq("department_id", dept_id) \
                .eq("start_date", start.strftime("%Y-%m-%d")) \
                .eq("end_date", end.strftime("%Y-%m-%d")) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if res.data:
                latest = res.data[0]
                st.session_state.last_schedule = latest['schedule_data']
                st.session_state.last_stats = None 
                st.session_state.locked_assignments = {}
                return True
            return False
        except Exception as e:
            st.error(f"Fetch failed: {e}")
            return False

    if st.session_state.get('last_schedule') is None and selected_dept_id:
        if fetch_latest_roster(selected_dept_id, roster_start, roster_end):
            notify("Roster Auto-Loaded", detail=f"Fetched the latest saved roster for **{selected_dept_name}**.", type="success")
            st.rerun()

    if 'last_schedule' not in st.session_state:
        st.session_state.last_schedule = None
    if 'last_stats' not in st.session_state:
        st.session_state.last_stats = None
    if 'locked_assignments' not in st.session_state:
        st.session_state.locked_assignments = {}

    # --- 4. Sync Stats if Missing ---
    if st.session_state.last_schedule and st.session_state.last_stats is None:
        try:
            stats = []
            total_assigned_all = 0
            min_shifts = float('inf')
            max_shifts = float('-inf')
            night_codes = [s['code'] for s in st.session_state.shifts if s.get('type') == 'Night']
            nurse_night_counts = []
            nurse_weekend_counts = []
            weekend_days = [d for d in range(planning_horizon) if (roster_start + timedelta(days=d)).weekday() >= 5]
            
            for nurse_name, shifts in st.session_state.last_schedule.items():
                total_s = sum(1 for s in shifts if s != '-')
                night_s = sum(1 for s in shifts if s in night_codes)
                weekend_s = sum(1 for d_idx in weekend_days if d_idx < len(shifts) and shifts[d_idx] != '-')
                stats.append({'Nurse': nurse_name, 'Total Shifts': total_s, 'Night Shifts': night_s, 'Weekend Shifts': weekend_s})
                total_assigned_all += total_s
                nurse_night_counts.append(night_s)
                nurse_weekend_counts.append(weekend_s)
                min_shifts = min(min_shifts, total_s)
                max_shifts = max(max_shifts, total_s)
            
            st.session_state.last_stats = {
                'df': pd.DataFrame(stats),
                'total': total_assigned_all,
                'fairness': f"{min_shifts}-{max_shifts} shifts/nurse",
                'night_fairness': f"{min(nurse_night_counts)}-{max(nurse_night_counts)} n/nurse",
                'weekend_fairness': f"{min(nurse_weekend_counts)}-{max(nurse_weekend_counts)} w/nurse"
            }
        except Exception as e:
            st.error(f"Stats sync error: {e}")
            
    # --- Automated Roster Loading ---
    # --- 5. Roster Table & Control Buttons ---
    if st.session_state.last_schedule:
        st.markdown("---")
        st.subheader("📅 Optimized Roster")
        
        # --- 5.1 Table Controls ---
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
        
        with ctrl_col1:
            if st.button("🔄 Regenerate", use_container_width=True, help="Re-solve the model while keeping manual locks"):
                gen_btn = True # Trigger generation logic below
        
        with ctrl_col2:
            # Excel Export handled later in the script (usually at the end of the page)
            pass 

        with ctrl_col3:
            if st.button("🧼 Reset Edits", use_container_width=True, help="Revert all manual changes since last generation"):
                if fetch_latest_roster(selected_dept_id, roster_start, roster_end):
                    notify("Edits Reset", "Reloaded the original generated roster.", type="info")
                    st.rerun()

        with ctrl_col4:
            if st.button("🔓 Clear Locks", use_container_width=True, help="Unlock all manual assignments"):
                st.session_state.locked_assignments = {}
                notify("Locks cleared", "All cells unlocked. They can now be changed by the solver.", type="success")
                st.rerun()

        # Zoom & Painter handled inside the render block below
        pass

    st.markdown("<br>", unsafe_allow_html=True)
    
    if gen_btn:
        if not dept_nurses:
            notify("Generation Failed", detail=f"No staff assigned to '{selected_dept_name}'. Add staff to this department first.", type="error")
            st.rerun()
        with st.spinner(f"Optimizing schedule for {selected_dept_name}..."):
            
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

            # Convert UI locks (Nurse Name -> index) to model locks (Nurse Index -> index)
            model_locked_assignments = {}
            for (n_name, d_idx), s_code in st.session_state.locked_assignments.items():
                try:
                    n_idx = next(i for i, n in enumerate(dept_nurses) if n['name'] == n_name)
                    model_locked_assignments[(n_idx, d_idx)] = s_code
                except StopIteration:
                    pass

            try:
                model = NurseRosteringModel(
                    num_nurses=len(dept_nurses),
                    num_days=planning_horizon,
                    nurses_list=dept_nurses,
                    shift_requirements=shift_requirements,
                    shifts_config=st.session_state.shifts,
                    grade_hierarchy=st.session_state.grades,
                    start_date=st.session_state.roster_start_date,
                    locked_assignments=model_locked_assignments,
                    weights=st.session_state.schedule_weights
                )
            except TypeError as te:
                st.error(f"Initialization Error: {te}")
                import traceback
                st.code(traceback.format_exc())
                st.stop()
            
            try:
                model.build_model()
                model.add_constraints()
                status = model.solve_model()
                
                # Weights are already persistent in st.session_state.schedule_weights
                
                from ortools.sat.python import cp_model
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    schedule = model.extract_solution(status)
                    st.session_state.last_schedule = schedule
                    
                    # Pre-calculate stats for persistence
                    stats = []
                    total_assigned_all = 0
                    min_shifts = float('inf')
                    max_shifts = float('-inf')
                    
                    # Night & Weekend stats
                    night_codes = [s['code'] for s in st.session_state.shifts if s.get('type') == 'Night']
                    nurse_night_counts = []
                    nurse_weekend_counts = []
                    
                    weekend_days = []
                    for d in range(planning_horizon):
                        if (st.session_state.roster_start_date + timedelta(days=d)).weekday() >= 5:
                            weekend_days.append(d)

                    for nurse_name, shifts in schedule.items():
                        total_shifts = sum(1 for s in shifts if s != '-')
                        night_shifts = sum(1 for s in shifts if s in night_codes)
                        weekend_shifts = sum(1 for d_idx in weekend_days if shifts[d_idx] != '-')
                        
                        stats.append({
                            'Nurse': nurse_name, 
                            'Total Shifts': total_shifts,
                            'Night Shifts': night_shifts,
                            'Weekend Shifts': weekend_shifts
                        })
                        
                        total_assigned_all += total_shifts
                        nurse_night_counts.append(night_shifts)
                        nurse_weekend_counts.append(weekend_shifts)
                        min_shifts = min(min_shifts, total_shifts)
                        max_shifts = max_shifts if max_shifts > total_shifts else total_shifts
                    
                    n_min = min(nurse_night_counts) if nurse_night_counts else 0
                    n_max = max(nurse_night_counts) if nurse_night_counts else 0

                    st.session_state.last_stats = {
                        'df': pd.DataFrame(stats),
                        'total': total_assigned_all,
                        'fairness': f"{min_shifts}-{max_shifts} shifts/nurse",
                        'night_fairness': f"{min(nurse_night_counts)}-{max(nurse_night_counts)} n/nurse",
                        'weekend_fairness': f"{min(nurse_weekend_counts)}-{max(nurse_weekend_counts)} w/nurse"
                    }

                    # --- Automated Save on Generation ---
                    try:
                        name = f"Auto-Saved {selected_dept_name} {roster_start.strftime('%b %d')}"
                        supabase.table("rosters").insert({
                            "name": name,
                            "start_date": roster_start.strftime("%Y-%m-%d"),
                            "end_date": roster_end.strftime("%Y-%m-%d"),
                            "schedule_data": schedule,
                            "department_id": selected_dept_id
                        }).execute()
                        notify("Schedule Generated & Saved", detail=f"Optimized roster for {selected_dept_name} is now persistent.", type="success")
                    except Exception as save_err:
                        notify("Generation Success (Save Failed)", detail=str(save_err), type="warning")
                    
                    st.rerun() 
                else:
                    st.session_state.last_schedule = None
                    st.session_state.last_stats = None
                    notify("Schedule generation failed:", detail="No feasible solution found. Try adding more nurses or reducing requirements.", type="error")
                    st.rerun()
                    
            except Exception as e:
                import traceback
                st.error(f"An error occurred during generation: {e}\n{traceback.format_exc()}")

    # --- Persistent Rendering (Outside Button) ---
    if st.session_state.get('last_schedule'):
        st.markdown("---")
        st.subheader("📅 Optimized Roster")
        
        try:
            schedule_data = st.session_state.last_schedule
            df_schedule = pd.DataFrame.from_dict(schedule_data, orient='index')
            
            # Safety check: Match columns to date_labels
            if len(df_schedule.columns) == len(date_labels):
                df_schedule.columns = date_labels
            else:
                st.warning(f"⚠️ Roster date range mismatch (Last: {len(df_schedule.columns)} days, System: {len(date_labels)} days). Please regenerate.")
            
            st.info("💡 You can manually change shifts below. Any manual edits will be **🔒 locked** and respected during regeneration.")
            
            if st.session_state.locked_assignments:
                if st.button("🔓 Clear All Manual Locks"):
                    st.session_state.locked_assignments = {}
                    notify("Locks cleared", "All manual assignments unlocked. You can now regenerate the schedule.", type="success")
                    st.rerun()

            shift_options = ['-'] + [s['code'] for s in st.session_state.shifts]

            # --- Roster Control Bar (Zoom & Painter) ---
            ctrl_col1, ctrl_col2 = st.columns([1, 2])
            with ctrl_col1:
                st.session_state.zoom_level = st.select_slider(
                    "🔍 Zoom Level", 
                    options=[50, 75, 90, 100, 110, 125, 150], 
                    value=st.session_state.zoom_level
                )
            
            with ctrl_col2:
                st.write("🖌️ **Shift Painter**")
                p_cols = st.columns(len(shift_options))
                shift_colors_map = {s['code']: s.get('color', '#E0E0E0') for s in st.session_state.shifts}
                for idx, opt in enumerate(shift_options):
                    is_active = st.session_state.painter_shift == opt
                    btn_type = "primary" if is_active else "secondary"
                    # Add a colored dot if it's a shift
                    color_dot = "⚪" if opt == "-" else "●"
                    btn_label = f"{color_dot} {opt}"
                    if p_cols[idx].button(btn_label, key=f"painter_{opt}", type=btn_type, use_container_width=True):
                        st.session_state.painter_shift = opt if not is_active else None
                        st.rerun()

            # Prepare data for component
            nurse_names = list(df_schedule.index)
            locked_comp_data = {}
            for (n_name, d_idx) in st.session_state.locked_assignments:
                if n_name not in locked_comp_data:
                    locked_comp_data[n_name] = {}
                locked_comp_data[n_name][d_idx] = True

            shift_colors = {s['code']: s.get('color', '#E0E0E0') for s in st.session_state.shifts}
            shift_colors['-'] = '#FFFFFF'

            # Render Custom Component
            edit_event = professional_roster(
                nurse_names=nurse_names,
                date_labels=date_labels,
                schedule_data=df_schedule.to_dict(orient='list'),
                shift_colors=shift_colors,
                locked_assignments=locked_comp_data,
                zoom_level=st.session_state.zoom_level,
                painter_shift=st.session_state.painter_shift,
                key="professional_roster_grid"
            )

            if edit_event:
                # edit_event is {nurse: str, day: int, shift: str}
                n_name = edit_event['nurse']
                d_idx = edit_event['day']
                new_shift = edit_event['shift']
                
                # Update locks
                st.session_state.locked_assignments[(n_name, d_idx)] = new_shift
                # Update schedule data immediately for the next render
                st.session_state.last_schedule[n_name][d_idx] = new_shift
                
                # --- Automated Save on Edit ---
                try:
                    name = f"Updated {selected_dept_name} {roster_start.strftime('%b %d')}"
                    supabase.table("rosters").insert({
                        "name": name,
                        "start_date": roster_start.strftime("%Y-%m-%d"),
                        "end_date": roster_end.strftime("%Y-%m-%d"),
                        "schedule_data": st.session_state.last_schedule,
                        "department_id": selected_dept_id
                    }).execute()
                except Exception as e:
                    notify("Manual Change Saved Locally", detail="Cloud sync failed, change persists in session only.", type="warning")
                
                st.rerun()

            # --- 6. Coverage Indicator ---
            st.markdown("---")
            st.subheader("📊 Coverage Indicator")
            
            # Pre-calculate coverage
            coverage_data = []
            for d_idx in range(planning_horizon):
                target_date = roster_start + timedelta(days=d_idx)
                date_str = target_date.strftime("%Y-%m-%d")
                day_demand = st.session_state.demand["overrides"].get(date_str, st.session_state.demand["default"])
                
                required_total = sum(req.get("Total", 1) for s, req in day_demand.items() if s != 'OFF')
                actual_total = sum(1 for n_name in nurse_names if schedule_data[n_name][d_idx] != '-')
                
                status = "Fully Staffed" if actual_total >= required_total else "Understaffed"
                color = "green" if actual_total >= required_total else ("red" if actual_total < required_total * 0.7 else "orange")
                coverage_data.append({"Date": date_labels[d_idx], "Req": required_total, "Act": actual_total, "Status": status, "Color": color})

            # Display as a horizontal status row
            cov_cols = st.columns(min(7, planning_horizon))
            for i, data in enumerate(coverage_data):
                with cov_cols[i % 7]:
                    st.markdown(f"""
                        <div style="background-color: {data['Color']}; color: white; padding: 4px; border-radius: 4px; text-align: center; font-size: 0.7rem; margin-bottom: 4px;">
                            {data['Date']}<br><b>{data['Act']}/{data['Req']}</b>
                        </div>
                    """, unsafe_allow_html=True)

            # --- 7. Conflict Warnings ---
            st.markdown("---")
            st.subheader("⚠️ Conflict Warnings")
            conflicts = []
            night_codes = [s['code'] for s in st.session_state.shifts if s.get('type') == 'Night']
            
            for n_name in nurse_names:
                shifts = schedule_data[n_name]
                # Check Consecutive Nights
                consecutive_nights = 0
                for d_idx, s in enumerate(shifts):
                    if s in night_codes:
                        consecutive_nights += 1
                        if consecutive_nights > 4:
                            conflicts.append(f"🚩 **{n_name}**: Exceeds max 4 consecutive night shifts at {date_labels[d_idx]}")
                    else:
                        # Check Night Recovery
                        if consecutive_nights > 0:
                            needed_off = 1 if consecutive_nights == 1 else (2 if consecutive_nights <= 3 else 3)
                            off_found = 0
                            for next_d in range(d_idx, min(d_idx + needed_off, planning_horizon)):
                                if shifts[next_d] == '-': off_found += 1
                                else: break
                            if off_found < needed_off:
                                conflicts.append(f"🚩 **{n_name}**: Insufficient recovery ({off_found}/{needed_off} days) after {consecutive_nights} nights at {date_labels[d_idx-1]}")
                        consecutive_nights = 0
                
                # Check Max 7 Consecutive Days
                consecutive_days = 0
                for d_idx, s in enumerate(shifts):
                    if s != '-':
                        consecutive_days += 1
                        if consecutive_days > 7:
                            conflicts.append(f"🚩 **{n_name}**: Exceeds max 7 consecutive working days at {date_labels[d_idx]}")
                    else:
                        consecutive_days = 0
            
            if conflicts:
                for msg in conflicts[:10]: # Limit to 10 warnings
                    st.warning(msg)
                if len(conflicts) > 10:
                    st.info(f"Showing 10 of {len(conflicts)} conflict warnings.")
            else:
                st.success("✅ No soft constraint violations detected in this roster.")

            # --- 8. Fairness Analysis ---
            st.markdown("---")
            st.subheader("⚖️ Fairness Analysis")
            if st.session_state.last_stats:
                stat_df = st.session_state.last_stats['df']
                st.dataframe(stat_df, hide_index=True, use_container_width=True)
                
                # Visualization
                st.markdown("#### Shift Distribution")
                st.bar_chart(stat_df.set_index('Nurse')['Total Shifts'])
                
            # Excel Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Save the visible/edited dataframe
                df_schedule.to_excel(writer, sheet_name='Roster')
            excel_data = output.getvalue()
            
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                st.download_button(
                    label="📥 Download Roster as Excel",
                    data=excel_data,
                    file_name=f"roster_{roster_start.strftime('%Y%m%d')}_to_{roster_end.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with dl_col2:
                if st.button("☁️ Save Roster to Cloud", use_container_width=True):
                    try:
                        name = f"Schedule {roster_start.strftime('%b %d')} to {roster_end.strftime('%b %d')}"
                        supabase.table("rosters").insert({
                            "name": name,
                            "start_date": roster_start.strftime("%Y-%m-%d"),
                            "end_date": roster_end.strftime("%Y-%m-%d"),
                            "schedule_data": st.session_state.last_schedule,
                            "department_id": selected_dept_id
                        }).execute()
                        notify("Saved to Cloud", detail=f"'{name}' has been securely saved to Supabase.", type="success")
                        st.rerun()
                    except Exception as e:
                        notify("Save Failed", detail=str(e), type="error")
                        st.rerun()
            
            # Note: Save and Stats are already integrated into sections above.
            # Roster is auto-saved on generation and edit.
            
        except Exception as display_err:
            st.error(f"Display Error: {display_err}")
            st.button("Clear Saved Roster", on_click=lambda: st.session_state.update(last_schedule=None))
    elif st.session_state.current_page == 'Generate Schedule':
        st.info("No schedule generated yet. Click the button above to start.")
