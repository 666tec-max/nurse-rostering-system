"""
staff_db.py — Supabase CRUD operations for the Staff table.
"""

def fetch_all_staff(supabase, owner_id):
    """Fetch all staff records from Supabase for a specific owner."""
    response = supabase.table("staff").select("*").eq("owner_user_id", owner_id).execute()
    return response.data or []


def insert_staff(supabase, record, owner_id):
    """Insert a single staff record into Supabase with an owner_user_id."""
    record["owner_user_id"] = owner_id
    supabase.table("staff").insert(record).execute()


def update_staff(supabase, employee_id, updates, owner_id):
    """Update a staff record by employee_id for a specific owner."""
    supabase.table("staff").update(updates).eq("employee_id", employee_id).eq("owner_user_id", owner_id).execute()


def delete_staff(supabase, employee_id, owner_id):
    """Delete a staff record by employee_id for a specific owner."""
    supabase.table("staff").delete().eq("employee_id", employee_id).eq("owner_user_id", owner_id).execute()


def fetch_grades(supabase, owner_id):
    """Fetch all grades from Supabase for a specific owner, ordered by hierarchy."""
    response = supabase.table("grades").select("*").eq("owner_user_id", owner_id).order("layer_index").execute()
    return response.data or []


def fetch_departments(supabase, owner_id):
    """Fetch all departments from Supabase for a specific owner."""
    response = supabase.table("departments").select("*").eq("owner_user_id", owner_id).execute()
    return response.data or []


def fetch_skills(supabase, owner_id):
    """Fetch all skills from Supabase for a specific owner."""
    response = supabase.table("skills").select("*").eq("owner_user_id", owner_id).execute()
    return response.data or []
