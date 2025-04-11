from collections import defaultdict, deque
import random
import copy

class TimeTableCSP:
    def __init__(self):
        # Days of the week
        self.days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        
        # Time slots per day (Tuesday has only 3 slots)
        self.slots_per_day = {
            "Sunday": 5,
            "Monday": 5,
            "Tuesday": 3,
            "Wednesday": 5,
            "Thursday": 5
        }
        
        # All possible time slots
        self.all_slots = []
        for day in self.days:
            for slot in range(1, self.slots_per_day[day] + 1):
                self.all_slots.append((day, slot))
        
        # Define courses and their requirements
        self.courses = {
            "Sécurité": {"lecture": 1, "td": 1, "teacher": "Teacher 1"},
            "Méthodes formelles": {"lecture": 1, "td": 1, "teacher": "Teacher 2"},
            "Analyse numérique": {"lecture": 1, "td": 1, "teacher": "Teacher 3"},
            "Entrepreneuriat": {"lecture": 1, "td": 0, "teacher": "Teacher 4"},
            "Recherche opérationnelle 2": {"lecture": 1, "td": 1, "teacher": "Teacher 5"},
            "Distributed Architecture & Intensive Computing": {"lecture": 1, "td": 1, "teacher": "Teacher 6"},
            "Réseaux 2": {"lecture": 1, "td": 1, "tp": 1, "teacher_lecture_td": "Teacher 7", 
                         "teacher_tp": ["Teacher 8", "Teacher 9", "Teacher 10"]},
            "Artificial Intelligence": {"lecture": 1, "td": 1, "tp": 1, "teacher_lecture_td": "Teacher 11", 
                                       "teacher_tp": ["Teacher 12", "Teacher 13", "Teacher 14"]}
        }
        
        # Create variables for each session
        self.variables = []
        for course, requirements in self.courses.items():
            if course in ["Réseaux 2", "Artificial Intelligence"]:
                if requirements.get("lecture", 0) > 0:
                    self.variables.append(f"{course}_lecture")
                if requirements.get("td", 0) > 0:
                    self.variables.append(f"{course}_td")
                if requirements.get("tp", 0) > 0:
                    self.variables.append(f"{course}_tp")
            else:
                if requirements.get("lecture", 0) > 0:
                    self.variables.append(f"{course}_lecture")
                if requirements.get("td", 0) > 0:
                    self.variables.append(f"{course}_td")
        
        # Initialize domains for each variable (initially all slots are possible)
        self.domains = {var: copy.deepcopy(self.all_slots) for var in self.variables}
        
        # Keep track of teachers' assigned slots
        self.teacher_slots = defaultdict(list)
        
        # Binary constraints between variables
        self.constraints = []
        self._create_constraints()
    
    def _create_constraints(self):
        """Create all binary constraints between variables"""
        # 1. Different sessions should be scheduled in different slots
        for i, var1 in enumerate(self.variables):
            for var2 in self.variables[i+1:]:
                self.constraints.append((var1, var2, lambda a, b: a != b))
        
        # 2. Lectures and TDs of the same course should not be in the same slot
        for course in self.courses:
            if course in ["Réseaux 2", "Artificial Intelligence"]:
                session_types = []
                if self.courses[course].get("lecture", 0) > 0:
                    session_types.append(f"{course}_lecture")
                if self.courses[course].get("td", 0) > 0:
                    session_types.append(f"{course}_td")
                if self.courses[course].get("tp", 0) > 0:
                    session_types.append(f"{course}_tp")
                
                for i, var1 in enumerate(session_types):
                    for var2 in session_types[i+1:]:
                        self.constraints.append((var1, var2, lambda a, b: a != b))
            else:
                lecture_var = f"{course}_lecture"
                td_var = f"{course}_td"
                if lecture_var in self.variables and td_var in self.variables:
                    self.constraints.append((lecture_var, td_var, lambda a, b: a != b))
    
    def get_teacher_for_session(self, var):
        """Get the teacher for a specific session"""
        course_name = var.split('_')[0]
        if len(var.split('_')) > 2:  # For courses with spaces in their names
            course_name += " " + var.split('_')[1]
            session_type = var.split('_')[2]
        else:
            session_type = var.split('_')[1]
        
        if course_name in ["Réseaux 2", "Artificial Intelligence"]:
            if session_type in ["lecture", "td"]:
                return self.courses[course_name]["teacher_lecture_td"]
            elif session_type == "tp":
                # For TP, we'll use the first teacher in the list for simplicity
                return self.courses[course_name]["teacher_tp"][0]
        else:
            return self.courses[course_name]["teacher"]
    
    def ac3(self):
        """AC3 algorithm to reduce domains"""
        queue = deque(self.constraints)
        
        while queue:
            (xi, xj, constraint) = queue.popleft()
            if self.revise(xi, xj, constraint):
                if len(self.domains[xi]) == 0:
                    return False
                
                # Add all constraints involving xi to the queue
                for xk, xl, c in self.constraints:
                    if xk == xi and xl != xj:
                        queue.append((xl, xi, c))
                    elif xl == xi and xk != xj:
                        queue.append((xk, xi, c))
        return True
    
    def revise(self, xi, xj, constraint):
        """Revise the domain of xi with respect to xj"""
        revised = False
        domain_copy = copy.deepcopy(self.domains[xi])
        
        for x in domain_copy:
            # If no value in xj's domain satisfies the constraint with x
            if not any(constraint(x, y) for y in self.domains[xj]):
                self.domains[xi].remove(x)
                revised = True
        
        return revised
    
    def mrv_heuristic(self, unassigned_vars):
        """Minimum Remaining Values heuristic"""
        return min(unassigned_vars, key=lambda var: len(self.domains[var]))
    
    def lcv_heuristic(self, var):
        """Least Constraining Value heuristic"""
        # Count how many values would be eliminated from the domains of neighboring variables
        # for each possible value of var
        def count_conflicts(value):
            conflicts = 0
            for other_var, _, constraint in self.constraints:
                if other_var != var:
                    for other_value in self.domains[other_var]:
                        if not constraint(value, other_value):
                            conflicts += 1
            return conflicts
        
        return sorted(self.domains[var], key=count_conflicts)
    
    def check_successive_slots(self, assignment, var, value):
        """Check if assigning value to var would create more than 3 consecutive slots for a teacher"""
        teacher = self.get_teacher_for_session(var)
        day = value[0]
        
        # Get all slots for this teacher on this day (including the new assignment)
        teacher_day_slots = [s[1] for v, s in assignment.items() if self.get_teacher_for_session(v) == teacher and s[0] == day]
        teacher_day_slots.append(value[1])
        
        # Check if there are more than 3 consecutive slots
        teacher_day_slots.sort()
        consecutive_count = 1
        for i in range(1, len(teacher_day_slots)):
            if teacher_day_slots[i] == teacher_day_slots[i-1] + 1:
                consecutive_count += 1
            else:
                consecutive_count = 1
            
            if consecutive_count > 3:
                return False
        
        return True
    
    def check_teacher_workdays(self, assignment, var, value):
        """Check if assigning value to var would exceed the maximum of two workdays for a teacher (soft constraint)"""
        teacher = self.get_teacher_for_session(var)
        
        # Get all days for this teacher (including the new assignment)
        teacher_days = {s[0] for v, s in assignment.items() if self.get_teacher_for_session(v) == teacher}
        teacher_days.add(value[0])
        
        # Return True if constraint is satisfied (max 2 days), False otherwise
        return len(teacher_days) <= 2
    
    def is_consistent(self, var, value, assignment):
        """Check if assigning value to var is consistent with the current assignment"""
        # Check binary constraints
        for var2, val2 in assignment.items():
            for var_i, var_j, constraint in self.constraints:
                if (var_i == var and var_j == var2) or (var_i == var2 and var_j == var):
                    if var_i == var:
                        if not constraint(value, val2):
                            return False
                    else:
                        if not constraint(val2, value):
                            return False
        
        # Check no more than 3 successive slots
        if not self.check_successive_slots(assignment, var, value):
            return False
        
        # Check soft constraint: teacher should have a maximum of two days
        # Note: We might want to handle soft constraints differently in a real-world application
        if not self.check_teacher_workdays(assignment, var, value):
            # Soft constraint violation, but we'll allow it for now
            pass
        
        return True
    
    def backtracking_search(self):
        """Backtracking search algorithm with MRV and LCV heuristics"""
        # Apply AC3 for preprocessing
        if not self.ac3():
            return None  # No solution exists
        
        return self._backtrack({})
    
    def _backtrack(self, assignment):
        """Recursive backtracking algorithm"""
        if len(assignment) == len(self.variables):
            return assignment  # Solution found
        
        # Select unassigned variable (MRV heuristic)
        unassigned = [var for var in self.variables if var not in assignment]
        var = self.mrv_heuristic(unassigned)
        
        # Try values in order of least constraining (LCV heuristic)
        for value in self.lcv_heuristic(var):
            if self.is_consistent(var, value, assignment):
                assignment[var] = value
                
                # Recursive call
                result = self._backtrack(assignment)
                if result is not None:
                    return result
                
                # If no solution found, backtrack
                del assignment[var]
        
        return None  # No solution found
    
    def print_solution(self, solution):
        """Print the timetable solution in a readable format"""
        if solution is None:
            print("No solution found.")
            return
        
        # Create empty timetable
        timetable = {day: {slot: [] for slot in range(1, self.slots_per_day[day] + 1)} 
                     for day in self.days}
        
        # Fill timetable with assigned sessions
        for var, (day, slot) in solution.items():
            course = var.split('_')[0]
            if len(var.split('_')) > 2:  # For courses with spaces in their names
                course += " " + var.split('_')[1]
                session_type = var.split('_')[2]
            else:
                session_type = var.split('_')[1]
            
            teacher = self.get_teacher_for_session(var)
            timetable[day][slot].append(f"{course} ({session_type}) - {teacher}")
        
        # Print timetable
        print("Timetable Solution:")
        print("-" * 80)
        
        for day in self.days:
            print(f"{day}:")
            for slot in range(1, self.slots_per_day[day] + 1):
                print(f"  Slot {slot}:", end=" ")
                if timetable[day][slot]:
                    print(", ".join(timetable[day][slot]))
                else:
                    print("Empty")
            print("-" * 80)
        
        # Check soft constraint: teachers should have a maximum of two workdays
        self._evaluate_soft_constraints(solution)
    
    def _evaluate_soft_constraints(self, solution):
        """Evaluate how well the soft constraints are satisfied"""
        # Check teacher workday constraint
        teacher_days = defaultdict(set)
        
        for var, (day, slot) in solution.items():
            teacher = self.get_teacher_for_session(var)
            teacher_days[teacher].add(day)
        
        print("\nTeacher Workday Evaluation (Soft Constraint):")
        all_satisfied = True
        for teacher, days in teacher_days.items():
            satisfied = len(days) <= 2
            print(f"  {teacher}: {len(days)} workdays ({'Satisfied' if satisfied else 'Not Satisfied'})")
            if not satisfied:
                all_satisfied = False
        
        print(f"\nSoft Constraint Overall: {'All Satisfied' if all_satisfied else 'Some Not Satisfied'}")

# Main execution
if __name__ == "__main__":
    csp = TimeTableCSP()
    solution = csp.backtracking_search()
    csp.print_solution(solution)