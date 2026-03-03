from model import NurseRosteringModel
from ortools.sat.python import cp_model

def test_must_have_shifts():
    print("Testing Must-Have Shift Requests...")
    
    # 1. Setup: 2 nurses, 5 days
    nurses = [
        {'name': 'N1', 'leave_days': [], 'must_have_shifts': [{'day': 0, 'shift': 'M'}, {'day': 2, 'shift': 'N'}]},
        {'name': 'N2', 'leave_days': [], 'must_have_shifts': []}
    ]
    num_days = 5
    
    # Minimal requirements to allow flexibility
    shift_reqs = {
        (0, 'M'): 1, (0, 'E'): 0, (0, 'N'): 0,
        (1, 'M'): 0, (1, 'E'): 0, (1, 'N'): 0,
        (2, 'M'): 0, (2, 'E'): 0, (2, 'N'): 1, # Day 2 Night required
        (3, 'M'): 0, (3, 'E'): 0, (3, 'N'): 0,
        (4, 'M'): 0, (4, 'E'): 0, (4, 'N'): 0,
    }
    
    print("Building model...")
    model = NurseRosteringModel(
        num_nurses=2,
        num_days=num_days,
        nurses_list=nurses,
        shift_requirements=shift_reqs
    )
    
    model.build_model()
    model.add_constraints()
    
    print("Solving...")
    status = model.solve_model()
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Solution found.")
        schedule = model.extract_solution(status)
        n1_sched = schedule['N1']
        print(f"N1 Schedule: {n1_sched}")
        
        # Verify N1 requests
        # Day 0 should be M
        # Day 2 should be N
        success = True
        if n1_sched[0] != 'M':
            print("FAILURE: N1 requested M on Day 0, got", n1_sched[0])
            success = False
        else:
            print("SUCCESS: N1 got requested M on Day 0.")
            
        if n1_sched[2] != 'N':
            print("FAILURE: N1 requested N on Day 2, got", n1_sched[2])
            success = False
        else:
            print("SUCCESS: N1 got requested N on Day 2.")
            
        if success:
            print("All must-have requests honored.")
            
    else:
        print("No feasible solution found.")

if __name__ == "__main__":
    test_must_have_shifts()
