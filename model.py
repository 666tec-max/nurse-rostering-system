from ortools.sat.python import cp_model

class NurseRosteringModel:
    def __init__(self, num_nurses, num_days, nurses_list, shift_requirements=None, shifts_config=None, allow_multiple_shifts=False, grade_hierarchy=None):
        """
        Initialize the Nurse Rostering Model.
        
        Args:
            num_nurses (int): Number of nurses.
            num_days (int): Planning horizon in days.
            nurses_list (list): List of dictionaries, each containing nurse info (e.g., 'name', 'leave_days').
            shift_requirements (dict): Dictionary mapping (day, shift) to required count.
            shifts_config (list): List of dicts with shift details. 
                                  Example: [{'code': 'M', 'type': 'Day', 'duration': 420}, ...]
            allow_multiple_shifts (bool): If True, allows nurses to work multiple non-overlapping shifts in a day.
            grade_hierarchy (list): List of lists representing grade ranks, top to bottom.
        """
        self.num_nurses = num_nurses
        self.num_days = num_days
        self.nurses = nurses_list
        self.shift_requirements = shift_requirements
        self.allow_multiple_shifts = allow_multiple_shifts
        self.grade_hierarchy = grade_hierarchy
        
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

    def _get_overlapping_shift_pairs(self):
        """Find all pairs of shifts that overlap in time."""
        from datetime import datetime, timedelta
        
        overlapping_pairs = []
        
        # Helper to convert "HH:MM" to minutes from midnight
        def get_mins(time_str):
            t = datetime.strptime(time_str, "%H:%M")
            return t.hour * 60 + t.minute

        for i, s1 in enumerate(self.shifts_info):
            s1_start = get_mins(s1.get('start', '07:00'))
            s1_end = s1_start + s1.get('duration', 480)
            
            for j in range(i + 1, len(self.shifts_info)):
                s2 = self.shifts_info[j]
                s2_start = get_mins(s2.get('start', '07:00'))
                s2_end = s2_start + s2.get('duration', 480)
                
                # Check for overlap.
                # Shift 1 overlaps with Shift 2 if Shift 1 starts before Shift 2 ends
                # AND Shift 1 ends after Shift 2 starts.
                # (We use > and < to allow shifts to end/start exactly at the same minute seamlessly)
                if s1_start < s2_end and s1_end > s2_start:
                    overlapping_pairs.append((s1['code'], s2['code']))
                    
        return overlapping_pairs

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

        # 1. Shifts per day constraint
        if self.allow_multiple_shifts:
            # If allowed, a nurse can take multiple shifts, BUT they cannot overlap in time.
            overlapping_pairs = self._get_overlapping_shift_pairs()
            for n in range(self.num_nurses):
                for d in range(self.num_days):
                    for s1_code, s2_code in overlapping_pairs:
                        # Cannot work both overlapping shifts on the same day
                        self.model.Add(self.x[(n, d, s1_code)] + self.x[(n, d, s2_code)] <= 1)
        else:
            # Default: Max 1 shift per nurse per day
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

    def solve_model(self):
        """Solve the model using lexicographic objectives: maximize utilization, then minimize deviations."""
        self.solver = cp_model.CpSolver()
        
        # --- Step 1: Define variables ---
        max_shifts_per_day = len(self.shifts) if self.allow_multiple_shifts else 1
        nurse_total_shifts = []
        for n in range(self.num_nurses):
            total_shifts = self.model.NewIntVar(0, self.num_days * max_shifts_per_day, f'total_shifts_n{n}')
            self.model.Add(
                total_shifts == sum(self.x[(n, d, s)] for d in range(self.num_days) for s in self.shifts)
            )
            nurse_total_shifts.append(total_shifts)
        
        total_assignments = self.model.NewIntVar(0, self.num_nurses * self.num_days * max_shifts_per_day, 'total_assignments')
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
        
        # --- Step 3: Step 1 – Maximize utilization ---
        self.model.Maximize(total_assignments)
        status1 = self.solver.Solve(self.model)
        
        if status1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return status1  # No feasible solution
        
        max_total_assignments = self.solver.Value(total_assignments)
        
        # --- Step 4: Step 2 – Minimize deviations while keeping utilization ---
        # Add constraint: total_assignments == max_total_assignments
        self.model.Add(total_assignments == max_total_assignments)
        self.model.Minimize(sum(deviations))
        
        # Solve again
        status2 = self.solver.Solve(self.model)
        return status2                
    
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
