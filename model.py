from ortools.sat.python import cp_model

class NurseRosteringModel:
    def __init__(self, num_nurses, num_days, nurses_list, shift_requirements=None, shifts_config=None, grade_hierarchy=None, start_date=None, locked_assignments=None):
        """
        Initialize the Nurse Rostering Model.
        
        Args:
            num_nurses (int): Number of nurses.
            num_days (int): Planning horizon in days.
            nurses_list (list): List of dictionaries, each containing nurse info.
            shift_requirements (dict): Dictionary mapping (day, shift) to required count.
            shifts_config (list): List of dicts with shift details.
            grade_hierarchy (list): List of lists representing grade ranks.
            start_date (date): The starting date of the roster (to identify weekends).
            locked_assignments (dict): Dictionary mapping (nurse_idx, day_idx) to shift_code or '-'.
        """
        self.num_nurses = num_nurses
        self.num_days = num_days
        self.nurses = nurses_list
        self.shift_requirements = shift_requirements
        self.grade_hierarchy = grade_hierarchy
        self.start_date = start_date
        self.locked_assignments = locked_assignments or {}
        
        # Parse shifts configuration
        if shifts_config:
            self.shifts_info = shifts_config
        else:
            # Default shifts if not provided
            self.shifts_info = [
                {'code': 'M', 'type': 'Day', 'duration': 480},
                {'code': 'E', 'type': 'Day', 'duration': 480},
                {'code': 'N', 'type': 'Night', 'duration': 600}
            ]
            
        self.shifts = [s['code'] for s in self.shifts_info]
        self.shift_durations = {s['code']: s['duration'] for s in self.shifts_info}
        self.night_shifts = [s['code'] for s in self.shifts_info if s.get('type') == 'Night']
        self.day_shifts = [s['code'] for s in self.shifts_info if s.get('type') != 'Night']
        
        self.model = None
        self.solver = None
        self.x = {}  # Decision variables: x[(nurse_idx, day, shift)]


    def _add_night_recovery_constraints(self):
        """Add night shift recovery constraints."""
        for n in range(self.num_nurses):
            # Create a boolean variable for "is working night on day d"
            is_night = []
            for d in range(self.num_days):
                night_var = self.model.NewBoolVar(f'is_night_n{n}_d{d}')
                self.model.Add(night_var == sum(self.x[(n, d, s)] for s in self.night_shifts))
                is_night.append(night_var)

            # 3a. Max 4 consecutive night shifts
            for d in range(self.num_days - 4):
                self.model.Add(sum(is_night[d + k] for k in range(5)) <= 4)
                
            # 3b. Recovery Rules
            # Rule 1: No Day shift immediately after Night shift (Basic Recovery)
            for d in range(self.num_days - 1):
                self.model.Add(
                    sum(self.x[(n, d + 1, s)] for s in self.day_shifts) == 0
                ).OnlyEnforceIf(is_night[d])
            
            # Count consecutive nights
            consec_nights = [self.model.NewIntVar(0, 4, f'consec_nights_n{n}_d{d}') for d in range(self.num_days)]
            
            for d in range(self.num_days):
                if d == 0:
                    self.model.Add(consec_nights[d] == is_night[d])
                else:
                    self.model.Add(consec_nights[d] == consec_nights[d-1] + 1).OnlyEnforceIf(is_night[d])
                    self.model.Add(consec_nights[d] == 0).OnlyEnforceIf(is_night[d].Not())

            # Enforce extended recovery days
            for d in range(self.num_days - 1):
                is_end_of_block = self.model.NewBoolVar(f'end_block_n{n}_d{d}')
                self.model.AddBoolAnd([is_night[d], is_night[d+1].Not()]).OnlyEnforceIf(is_end_of_block)
                self.model.AddBoolOr([is_night[d].Not(), is_night[d+1]]).OnlyEnforceIf(is_end_of_block.Not())
                
                # Rule 2: 2-3 nights -> 2 days off
                if d + 2 < self.num_days:
                    trigger_2off = self.model.NewBoolVar(f'trigger_2off_n{n}_d{d}')
                    self.model.Add(consec_nights[d] >= 2).OnlyEnforceIf(trigger_2off)
                    self.model.Add(consec_nights[d] < 2).OnlyEnforceIf(trigger_2off.Not())
                    for s in self.shifts:
                        self.model.Add(self.x[(n, d+2, s)] == 0).OnlyEnforceIf([is_end_of_block, trigger_2off])

                # Rule 3: 4 nights -> 3 days off
                if d + 3 < self.num_days:
                    trigger_3off = self.model.NewBoolVar(f'trigger_3off_n{n}_d{d}')
                    self.model.Add(consec_nights[d] == 4).OnlyEnforceIf(trigger_3off)
                    self.model.Add(consec_nights[d] != 4).OnlyEnforceIf(trigger_3off.Not())
                    for s in self.shifts:
                        self.model.Add(self.x[(n, d+2, s)] == 0).OnlyEnforceIf([is_end_of_block, trigger_3off])
                        self.model.Add(self.x[(n, d+3, s)] == 0).OnlyEnforceIf([is_end_of_block, trigger_3off])

    def build_model(self):
        """Initialize the CP-SAT model and decision variables."""
        self.model = cp_model.CpModel()
        
        # Create decision variables x[e,d,s]
        for n in range(self.num_nurses):
            for d in range(self.num_days):
                for s in self.shifts:
                    self.x[(n, d, s)] = self.model.NewBoolVar(f'x_n{n}_d{d}_s{s}')

    def add_constraints(self):
        """Add hard constraints to the model."""
        if not self.model:
            raise ValueError("Model not built. Call build_model() first.")

        # 1. Max 1 shift per nurse per day
        # sum_{s ∈ {M,E,N}} x[e,d,s] ≤ 1 for all e, d
        for n in range(self.num_nurses):
            for d in range(self.num_days):
                self.model.Add(sum(self.x[(n, d, s)] for s in self.shifts) <= 1)

        # 2. Leave compliance
        # x[e,L,s] = 0 for all s ∈ {M,E,N} where L is a leave day
        for n_idx, nurse in enumerate(self.nurses):
            # Leave days
            for leave_day in nurse.get('leave_days', []):
                # Ensure leave day is within the planning horizon
                if 0 <= leave_day < self.num_days:
                    for s in self.shifts:
                        self.model.Add(self.x[(n_idx, leave_day, s)] == 0)
            
            # Must-have shifts
            # Expecting 'must_have_shifts' to be a list of dicts: [{'day': 0, 'shift': 'M'}, ...]
            for req in nurse.get('must_have_shifts', []):
                d = req.get('day')
                s = req.get('shift')
                if d is not None and s in self.shifts and 0 <= d < self.num_days:
                    # Hard constraint: x[e,d,s] = 1
                    self.model.Add(self.x[(n_idx, d, s)] == 1)

        # 3. Night recovery: Max 4 consecutive night shifts
        # And recovery rules:
        # 1 night -> 1 day off
        # 2-3 nights -> 2 days off
        # 4 nights -> 3 days off
        
        # Only apply night recovery rules if night shifts are defined
        if self.night_shifts:
            self._add_night_recovery_constraints()

        # 4. Max 6 working days per week (Static 7-day blocks)
        for n in range(self.num_nurses):
            for w in range(0, self.num_days, 7):
                week_days = range(w, min(w + 7, self.num_days))
                # Sum of all shifts for this nurse in this week
                self.model.Add(
                    sum(
                        self.x[(n, d, s)] 
                        for d in week_days 
                        for s in self.shifts
                    ) <= 6
                )

        # 4b. Max 6 consecutive working days (Sliding 7-day window)
        # For each nurse, in every sliding 7-day window, sum of assigned shifts <= 6
        for n in range(self.num_nurses):
            # Window size = 7
            # We iterate d from 0 to num_days - 7
            for start_day in range(self.num_days - 6):
                window_days = range(start_day, start_day + 7)
                self.model.Add(
                    sum(
                        self.x[(n, d, s)]
                        for d in window_days
                        for s in self.shifts
                    ) <= 6
                )

        # 5. Shift coverage requirements (Hard Constraint: Minimum Coverage)
        # sum_{e} x[e,d,s] >= required[(d,s)]
        if self.shift_requirements:
            for d in range(self.num_days):
                for s in self.shifts:
                    req = self.shift_requirements.get((d, s), 0)
                    # Handle backward compatibility: req might be an int or a dict like {"Total": 1}
                    if isinstance(req, dict):
                        req_val = req.get("Total", 0)
                    else:
                        req_val = req
                    self.model.Add(
                        sum(self.x[(n, d, s)] for n in range(self.num_nurses)) >= req_val
                    )

        # 6. Skill compatibility constraint
        # A nurse can only be assigned to a shift if they have at least one of the required skills
        for n_idx, nurse in enumerate(self.nurses):
            nurse_skills = set(nurse.get('skills', []))
            
            for d in range(self.num_days):
                for shift_config in self.shifts_info:
                    shift_code = shift_config['code']
                    required_skills = shift_config.get('required_skills', [])
                    
                    # If shift has required skills and nurse doesn't have any of them
                    if required_skills and not any(skill in nurse_skills for skill in required_skills):
                        # Nurse cannot be assigned to this shift
                        self.model.Add(self.x[(n_idx, d, shift_code)] == 0)

        # 7. Locked Assignments (Manual Overrides)
        for (n_idx, d_idx), shift_code in self.locked_assignments.items():
            if 0 <= n_idx < self.num_nurses and 0 <= d_idx < self.num_days:
                if shift_code == '-':
                    # Enforce OFF day
                    for s in self.shifts:
                        self.model.Add(self.x[(n_idx, d_idx, s)] == 0)
                elif shift_code in self.shifts:
                    # Enforce specific shift
                    self.model.Add(self.x[(n_idx, d_idx, shift_code)] == 1)

    def solve_model(self):
        """Solve the model using lexicographic objectives: maximize utilization, then minimize deviations."""
        self.solver = cp_model.CpSolver()
        
        # --- Step 1: Define variables ---
        nurse_total_shifts = []
        for n in range(self.num_nurses):
            total_shifts = self.model.NewIntVar(0, self.num_days, f'total_shifts_n{n}')
            self.model.Add(
                total_shifts == sum(self.x[(n, d, s)] for d in range(self.num_days) for s in self.shifts)
            )
            nurse_total_shifts.append(total_shifts)
        
        total_assignments = self.model.NewIntVar(0, self.num_nurses * self.num_days, 'total_assignments')
        self.model.Add(total_assignments == sum(nurse_total_shifts))
        
        # --- Step 2: Define deviations for fairness ---
        deviations = []
        N = self.num_nurses
        max_dev = N * self.num_days
        
        for n in range(self.num_nurses):
            dev = self.model.NewIntVar(0, max_dev, f'dev_n{n}')
            self.model.Add(dev >= (N * nurse_total_shifts[n]) - total_assignments)
            self.model.Add(dev >= total_assignments - (N * nurse_total_shifts[n]))
            deviations.append(dev)
        
        # --- Step 3: Define Night Shifts Per Nurse ---
        night_shifts_per_nurse = []
        for n in range(self.num_nurses):
            ns = self.model.NewIntVar(0, self.num_days, f'night_shifts_n{n}')
            # Count night shifts if any are defined
            if self.night_shifts:
                self.model.Add(ns == sum(self.x[(n, d, s)] for d in range(self.num_days) for s in self.night_shifts))
            else:
                self.model.Add(ns == 0)
            night_shifts_per_nurse.append(ns)

        # --- Step 4: Step 1 – Maximize utilization ---
        self.model.Maximize(total_assignments)
        status1 = self.solver.Solve(self.model)
        
        if status1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return status1  # No feasible solution
        
        # Fix utilization for next steps
        self.model.Add(total_assignments == int(self.solver.Value(total_assignments)))
        
        # --- Step 5: Step 2 – Minimize overall deviations (General Fairness) ---
        self.model.Minimize(sum(deviations))
        status2 = self.solver.Solve(self.model)
        
        if status2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return status2
            
        # Fix general fairness for last step
        self.model.Add(sum(deviations) == int(self.solver.Value(sum(deviations))))
        
        # --- Step 6: Step 3 – Minimize night shift difference (Night Fairness) ---
        min_nights = self.model.NewIntVar(0, self.num_days, 'min_nights')
        max_nights = self.model.NewIntVar(0, self.num_days, 'max_nights')
        self.model.AddMinEquality(min_nights, night_shifts_per_nurse)
        self.model.AddMaxEquality(max_nights, night_shifts_per_nurse)
        
        night_diff = self.model.NewIntVar(0, self.num_days, 'night_diff')
        self.model.Add(night_diff == max_nights - min_nights)
        
        self.model.Minimize(night_diff)
        status3 = self.solver.Solve(self.model)
        
        if status3 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return status3
            
        # Fix night fairness for last step
        self.model.Add(night_diff == int(self.solver.Value(night_diff)))
        
        # --- Step 7: Step 4 – Minimize weekend shift difference (Weekend Fairness) ---
        weekend_shifts_per_nurse = []
        weekend_indices = []
        if self.start_date:
            from datetime import timedelta
            for d in range(self.num_days):
                curr_date = self.start_date + timedelta(days=d)
                if curr_date.weekday() >= 5: # Saturday=5, Sunday=6
                    weekend_indices.append(d)
        
        for n in range(self.num_nurses):
            ws = self.model.NewIntVar(0, self.num_days, f'weekend_shifts_n{n}')
            if weekend_indices:
                self.model.Add(ws == sum(self.x[(n, d, s)] for d in weekend_indices for s in self.shifts))
            else:
                self.model.Add(ws == 0)
            weekend_shifts_per_nurse.append(ws)
            
        min_weekends = self.model.NewIntVar(0, self.num_days, 'min_weekends')
        max_weekends = self.model.NewIntVar(0, self.num_days, 'max_weekends')
        self.model.AddMinEquality(min_weekends, weekend_shifts_per_nurse)
        self.model.AddMaxEquality(max_weekends, weekend_shifts_per_nurse)
        
        weekend_diff = self.model.NewIntVar(0, self.num_days, 'weekend_diff')
        self.model.Add(weekend_diff == max_weekends - min_weekends)
        
        self.model.Minimize(weekend_diff)
        
        # Final Solve
        status4 = self.solver.Solve(self.model)
        return status4
    
    def extract_solution(self, status):
        """Extract the schedule if a solution exists."""
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            schedule = {}
            for n in range(self.num_nurses):
                nurse_name = self.nurses[n]['name']
                schedule[nurse_name] = []
                for d in range(self.num_days):
                    assigned = []
                    for s in self.shifts:
                        if self.solver.Value(self.x[(n, d, s)]) == 1:
                            assigned.append(s)
                    
                    if assigned:
                        schedule[nurse_name].append(", ".join(assigned))
                    else:
                        schedule[nurse_name].append('-')
            return schedule
        return None
