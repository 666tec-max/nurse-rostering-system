-- Nurse Rostering System Multi-User Isolation Migration
-- Run this in the Supabase SQL Editor to add owner_user_id columns.

ALTER TABLE public.staff ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.departments ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.grades ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.skills ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.shifts ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.demand ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.rosters ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.leaves ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
ALTER TABLE public.leave_requests ADD COLUMN IF NOT EXISTS owner_user_id TEXT;

-- Index for better performance when filtering by owner
CREATE INDEX IF NOT EXISTS idx_staff_owner ON public.staff(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_departments_owner ON public.departments(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_grades_owner ON public.grades(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_skills_owner ON public.skills(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_shifts_owner ON public.shifts(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_demand_owner ON public.demand(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_rosters_owner ON public.rosters(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_leaves_owner ON public.leaves(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_owner ON public.leave_requests(owner_user_id);

-- Optional: Associate existing data with a default user if needed
-- UPDATE public.staff SET owner_user_id = 'admin' WHERE owner_user_id IS NULL;
-- (Repeat for other tables)
