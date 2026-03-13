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


# ──────────────────────────────────────────────
# Login Page
# ──────────────────────────────────────────────

def render_login_page(supabase):
    """Render a centred login form. Returns True when the user logs in."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .login-wrap {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; padding: 60px 20px;
    }
    .login-card {
        background: white; border-radius: 20px; padding: 40px 48px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12); width: 100%; max-width: 420px;
        font-family: 'Inter', sans-serif;
    }
    .login-logo { font-size: 2.5rem; text-align: center; margin-bottom: 8px; }
    .login-title { font-size: 1.5rem; font-weight: 700; text-align: center;
        color: #1a1a2e; margin-bottom: 4px; }
    .login-sub { font-size: 0.85rem; color: #666; text-align: center; margin-bottom: 28px; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="login-card">
            <div class="login-logo">🏥</div>
            <div class="login-title">Nurse Rostering System</div>
            <div class="login-sub">Hospital Staff Scheduler — Please sign in to continue</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            user_id = st.text_input("User ID", placeholder="e.g. Admin")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not user_id or not password:
                st.error("Please enter both User ID and Password.")
                return False

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
                st.rerun()
            else:
                st.error("Invalid User ID or Password.")
                log_audit(supabase, user_id, "LOGIN_FAILED", {"reason": "bad credentials"})
                return False

    return st.session_state.get("logged_in", False)
