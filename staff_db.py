"""
staff_db.py — Supabase CRUD operations for the Staff table.
"""

def fetch_all_staff(supabase):
    """Fetch all staff records from Supabase."""
    response = supabase.table("staff").select("*").execute()
    return response.data or []


def insert_staff(supabase, record):
    """Insert a single staff record into Supabase."""
    supabase.table("staff").insert(record).execute()


def update_staff(supabase, employee_id, updates):
    """Update a staff record by employee_id."""
    supabase.table("staff").update(updates).eq("employee_id", employee_id).execute()


def delete_staff(supabase, employee_id):
    """Delete a staff record by employee_id."""
    supabase.table("staff").delete().eq("employee_id", employee_id).execute()


def fetch_grades(supabase):
    """Fetch all grades from Supabase, ordered by hierarchy."""
    response = supabase.table("grades").select("*").order("layer_index").execute()
    return response.data or []


def fetch_departments(supabase):
    """Fetch all departments from Supabase."""
    response = supabase.table("departments").select("*").execute()
    return response.data or []


def fetch_skills(supabase):
    """Fetch all skills from Supabase."""
    response = supabase.table("skills").select("*").execute()
    return response.data or []
