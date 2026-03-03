from model import NurseRosteringModel

def test_model():
    print("Testing Nurse Rostering Model...")
    # Test case: 3 nurses, 3 days
    nurses = [{'name': 'N1', 'leave_days': [], 'skills': ['ICU']}, {'name': 'N2', 'leave_days': [0], 'skills': ['ER']}, {'name': 'N3', 'leave_days': [], 'skills': ['ICU']}]
    # Structured requirements: (day, shift) -> { 'Total': X, 'Skill': Y }
    shift_reqs = {
        (0, 'M'): {'Total': 1, 'ICU': 1},
        (1, 'M'): {'Total': 2, 'ER': 1},
        (2, 'M'): {'Total': 1}
    }
    model = NurseRosteringModel(num_nurses=3, num_days=3, nurses_list=nurses, shift_requirements=shift_reqs)
    
    print("Building model...")
    model.build_model()
    
    print("Adding constraints...")
    model.add_constraints()
    
    print("Solving...")
    status = model.solve_model()
    
    from ortools.sat.python import cp_model
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution found:")
        schedule = model.extract_solution(status)
        for nurse, shifts in schedule.items():
            print(f"{nurse}: {shifts}")
        
        # specific check: N2 has leave on day 0, so should be '-'
        if schedule['N2'][0] != '-':
            print("ERROR: Leave constraint failed for N2 on day 0")
        else:
            print("Leave constraint verified.")
    else:
        print("No solution found.")

def test_grade_substitution():
    print("\nTesting Grade Substitution...")
    grade_hierarchy = [[{"code": "SN"}], [{"code": "RN"}]]
    nurses = [
        {'name': 'Senior', 'grade': 'SN', 'skills': ['ICU']},
        {'name': 'Junior', 'grade': 'RN', 'skills': []}
    ]
    
    # Requirement: 1 SN on Day 0, 1 RN on Day 1
    shift_reqs = {
        (0, 'M'): {'Total': 1, 'Grade': 'SN'},
        (1, 'M'): {'Total': 1, 'Grade': 'RN'}
    }
    
    model = NurseRosteringModel(2, 2, nurses, shift_reqs, grade_hierarchy=grade_hierarchy)
    model.build_model()
    model.add_constraints()
    status = model.solve_model()
    
    from ortools.sat.python import cp_model
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = model.extract_solution(status)
        print("Schedule:", schedule)
        # On Day 0, only Senior can work M
        if schedule['Junior'][0] == 'M':
             print("FAIL: Junior worked a Senior-only shift.")
        elif schedule['Senior'][0] == 'M':
             print("SUCCESS: Senior fulfilled Senior requirement.")
        
        # On Day 1, Senior or Junior can work M.
        if schedule['Senior'][1] == 'M' or schedule['Junior'][1] == 'M':
             print("SUCCESS: Junior or Senior fulfilled Junior requirement.")
    else:
        print("FAIL: No solution found.")

def test_grade_and_skill():
    print("\nTesting Grade + Skill combination...")
    grade_hierarchy = [[{"code": "SN"}], [{"code": "RN"}]]
    nurses = [
        {'name': 'Senior_ICU', 'grade': 'SN', 'skills': ['ICU']},
        {'name': 'Senior_Basic', 'grade': 'SN', 'skills': []},
        {'name': 'Junior_ICU', 'grade': 'RN', 'skills': ['ICU']}
    ]
    
    # Need 1 nurse who is BOTH SN AND ICU.
    # Only 'Senior_ICU' can fulfill this.
    shift_reqs = {
        (0, 'M'): {'Total': 1, 'Grade': 'SN', 'ICU': 1}
    }
    
    model = NurseRosteringModel(3, 1, nurses, shift_reqs, grade_hierarchy=grade_hierarchy)
    model.build_model()
    model.add_constraints()
    status = model.solve_model()
    
    from ortools.sat.python import cp_model
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = model.extract_solution(status)
        print("Schedule:", schedule)
        if schedule['Senior_ICU'][0] == 'M':
            print("SUCCESS: Senior_ICU fulfilled combined requirement.")
        else:
            print("FAIL: Wrong nurse assigned.")
    else:
        print("FAIL: No solution found.")

if __name__ == "__main__":
    test_model()
    test_grade_substitution()
    test_grade_and_skill()
