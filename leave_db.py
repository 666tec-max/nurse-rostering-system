"""
leave_db.py — CRUD helpers for the leave_requests table.
"""
from datetime import date, timedelta


def fetch_leave_requests(supabase, owner_id, employee_id=None, start_date=None, end_date=None):
    """Fetch leave requests for a specific owner, optionally filtered by employee and/or date overlap."""
    try:
        q = supabase.table("leave_requests").select("*").eq("owner_user_id", owner_id)
        if employee_id:
            q = q.eq("employee_id", employee_id)
        res = q.order("start_date").execute()
        rows = res.data or []

        # Filter to overlapping date range if both provided
        if start_date and end_date:
            def overlaps(row):
                rs = date.fromisoformat(row["start_date"])
                re = date.fromisoformat(row["end_date"])
                return rs <= end_date and re >= start_date
            rows = [r for r in rows if overlaps(r)]

        return rows
    except Exception:
        return []


def insert_leave_request(supabase, owner_id, employee_id, start_date, end_date, leave_type="AL",
                          status="Approved", remarks=""):
    try:
        supabase.table("leave_requests").insert({
            "owner_user_id": owner_id,
            "employee_id": employee_id,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "leave_type": leave_type,
            "status": status,
            "remarks": remarks,
        }).execute()
        return True
    except Exception as e:
        return str(e)


def delete_leave_request(supabase, owner_id, leave_id):
    try:
        supabase.table("leave_requests").delete().eq("id", str(leave_id)).eq("owner_user_id", owner_id).execute()
        return True
    except Exception as e:
        return str(e)


def get_leave_days_for_nurse(supabase, owner_id, employee_id, roster_start, roster_end):
    """
    Returns a list of day-indices (0-based from roster_start) that fall within
    approved leave for the given nurse and date range, scoped to the owner.
    """
    rows = fetch_leave_requests(supabase, owner_id=owner_id, employee_id=employee_id,
                                 start_date=roster_start, end_date=roster_end)
    leave_indices = set()
    for row in rows:
        if row.get("status") != "Approved":
            continue
        rs = date.fromisoformat(row["start_date"])
        re = date.fromisoformat(row["end_date"])
        d = max(rs, roster_start)
        while d <= min(re, roster_end):
            idx = (d - roster_start).days
            leave_indices.add(idx)
            d += timedelta(days=1)
    return sorted(leave_indices)
