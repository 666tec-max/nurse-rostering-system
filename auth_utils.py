"""
auth_utils.py — Login, logout, audit log helpers for the Nurse Rostering System.
"""
import streamlit as st
from datetime import datetime

# ──────────────────────────────────────────────
# Audit Log
# ──────────────────────────────────────────────

def log_audit(supabase, user_id: str, action: str, details: dict = None):
    """Write an entry to the audit_log table (non-blocking; ignores errors)."""
    try:
        supabase.table("audit_log").insert({
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception:
        pass  # Audit failures should never block the user


# ──────────────────────────────────────────────
# User Credentials
# ──────────────────────────────────────────────

def load_user(supabase, user_id: str):
    """Return the user_credentials row or None."""
    try:
        res = supabase.table("user_credentials").select("*").eq("user_id", user_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def save_user_prefs(supabase, user_id: str, theme: str = None, soft_constraint_profile: dict = None):
    """Persist per-user preferences to Supabase."""
    updates = {}
    if theme is not None:
        updates["theme"] = theme
    if soft_constraint_profile is not None:
        updates["soft_constraint_profile"] = soft_constraint_profile
    if not updates:
        return
    try:
        supabase.table("user_credentials").update(updates).eq("user_id", user_id).execute()
    except Exception:
        pass


def set_current_user(supabase, user_id: str):
    """Set the Postgres session variable app.current_user_id via RPC.
    
    This enables RLS policies that use current_setting('app.current_user_id', true)
    to correctly filter rows by owner. Must be called at the start of each
    Streamlit page render after the user is authenticated.
    """
    try:
        supabase.rpc("set_app_user", {"user_id": user_id}).execute()
    except Exception:
        pass  # Non-blocking; app-level .eq() filters still apply as fallback


# ──────────────────────────────────────────────
# Login Page
# ──────────────────────────────────────────────

def render_login_page(supabase):
    """Render a centred login form with a modern hospital theme."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Center the login container */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
    }
    
    /* Hide sidebar during login */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
        width: 100%;
    }
    
    .login-card {
        background: white;
        border-radius: 1.5rem;
        padding: 3rem;
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        width: 100%;
        max-width: 450px;
        text-align: center;
        border: 1px solid #E2E8F0;
    }
    
    .login-logo {
        background: #DBEAFE;
        color: #2563EB;
        width: 64px;
        height: 64px;
        border-radius: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin: 0 auto 1.5rem auto;
    }
    
    .login-title {
        font-family: 'Inter', sans-serif;
        font-size: 1.875rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.5rem;
    }
    
    .login-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 2.5rem;
    }
    
    /* Style Streamlit inputs */
    .stTextInput > div > div > input {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
    }
    
    .stButton > button {
        background-color: #2563EB !important;
        color: white !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        margin-top: 1rem !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Use a container to center everything
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Outer column layout to push the card to center
    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">🏥</div>
            <div class="login-title">Nurse Rostering System</div>
            <div class="login-subtitle">Hospital Management Dashboard</div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", border=False):
            user_id = st.text_input("User ID", placeholder="Admin", label_visibility="visible")
            password = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="visible")
            
            # Button is centered by CSS and container width
            submitted = st.form_submit_button("Log In", use_container_width=True)
            
            if submitted:
                if not user_id or not password:
                    st.error("Please enter both User ID and Password.")
                else:
                    user = load_user(supabase, user_id)
                    if user and user.get("password_hash") == password:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user_id
                        # Load per-user preferences
                        st.session_state.theme = user.get("theme", "Eye Comfort")
                        profile = user.get("soft_constraint_profile") or {}
                        st.session_state.schedule_weights = {
                            "utilization": profile.get("utilization", 10),
                            "overall_fairness": profile.get("overall_fairness", 5),
                            "night_fairness": profile.get("night_fairness", 5),
                            "weekend_fairness": profile.get("weekend_fairness", 5),
                        }
                        log_audit(supabase, user_id, "LOGIN", {"status": "success"})
                        set_current_user(supabase, user_id)  # Set RLS session variable
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Password.")
                        log_audit(supabase, user_id, "LOGIN_FAILED", {"reason": "bad credentials"})
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return st.session_state.get("logged_in", False)
