from model import NurseRosteringModel
from ortools.sat.python import cp_model

def test_night_shift_restriction():
    print("Testing Night Shift Restriction...")
    nurses = [
        {'name': 'NoNightNurse', 'allow_night_shift': False, 'grade': 'RN', 'skills': []},
        {'name': 'AllowNightNurse', 'allow_night_shift': True, 'grade': 'RN', 'skills': []}
    ]
    # Shifts: M, E, N
    shifts_config = [
        {'code': 'M', 'type': 'Day', 'duration': 480},
        {'code': 'E', 'type': 'Day', 'duration': 480},
        {'code': 'N', 'type': 'Night', 'duration': 600}
    ]
    
    # Requirement: 1 N shift on Day 0
    shift_reqs = {
        (0, 'N'): {'Total': 1}
    }
    
    model = NurseRosteringModel(2, 1, nurses, shift_reqs, shifts_config)
    model.build_model()
    model.add_constraints()
    status = model.solve_model()
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = model.extract_solution(status)
        print("Schedule:", schedule)
        if schedule['NoNightNurse'][0] == 'N':
            print("FAIL: NoNightNurse was assigned a night shift!")
        elif schedule['AllowNightNurse'][0] == 'N':
            print("SUCCESS: Only AllowNightNurse was assigned the night shift.")
    else:
        print("FAIL: No solution found (but one should exist).")

def test_max_consecutive_days():
    print("\nTesting Max Consecutive Days...")
    # Nurse limited to 2 consecutive days.
    nurses = [
        {'name': 'LimitedNurse', 'max_consecutive_work_days': 2},
    ]
    
    # Requirement: 1 M shift every day for 4 days.
    # This should be impossible for one nurse if they must have a day off after 2 days.
    # But wait, if only 1 nurse exists and 1 is required, it will be INFEASIBLE.
    shift_reqs = {
        (0, 'M'): {'Total': 1},
        (1, 'M'): {'Total': 1},
        (2, 'M'): {'Total': 1},
        (3, 'M'): {'Total': 1}
    }
    
    model = NurseRosteringModel(1, 4, nurses, shift_reqs)
    model.build_model()
    model.add_constraints()
    status = model.solve_model()
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print("FAIL: Found a solution where LimitedNurse worked 4 days in a row!")
        schedule = model.extract_solution(status)
        print("Schedule:", schedule)
    else:
        print("SUCCESS: Correctly identified as infeasible (LimitedNurse cannot work 4 days in a row).")

    # Now test feasibility with 2 nurses.
    nurses_2 = [
        {'name': 'NurseA', 'max_consecutive_work_days': 2},
        {'name': 'NurseB', 'max_consecutive_work_days': 2}
    ]
    model_2 = NurseRosteringModel(2, 4, nurses_2, shift_reqs)
    model_2.build_model()
    model_2.add_constraints()
    status_2 = model_2.solve_model()
    
    if status_2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule_2 = model_2.extract_solution(status_2)
        print("Schedule (2 nurses):", schedule_2)
        # Verify no one works > 2 days in a row.
        for name, shifts in schedule_2.items():
            work_days = [1 if s != '-' else 0 for s in shifts]
            for i in range(len(work_days)-2):
                if sum(work_days[i:i+3]) > 2:
                    print(f"FAIL: {name} worked > 2 days in a row: {work_days}")
                    return
        print("SUCCESS: No nurse worked more than 2 consecutive days.")
    else:
        print("FAIL: Could not find a feasible solution for 2 nurses.")

if __name__ == "__main__":
    test_night_shift_restriction()
    test_max_consecutive_days()
