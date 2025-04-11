from collections import defaultdict, deque
import random
import copy

class TimeTableCSP:
    def __init__(self):
        """
        Initialize the TimeTable Constraint Satisfaction Problem with all necessary data structures
        - Define days, slots, courses, requirements
        - Create variables and their domains
        - Set up constraints
        """
        # Days of the week for the timetable
        self.days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        
        # Time slots available per day (Tuesday has only 3 slots as specified in the problem)
        self.slots_per_day = {
            "Sunday": 5,
            "Monday": 5,
            "Tuesday": 3,  # As per problem specification, Tuesday has only 3 slots in the morning
            "Wednesday": 5,
            "Thursday": 5
        }
        
        # Generate all possible time slots based on days and slots per day
        self.all_slots = []
        for day in self.days:
            for slot in range(1, self.slots_per_day[day] + 1):
                self.all_slots.append((day, slot))
        
        # Define courses and their requirements (lectures, TDs, TPs, and assigned teachers)
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
        
        # Create variables based on course requirements
        # Each variable represents a specific session (lecture, TD, or TP) for a course
        self.variables = []
        for course, requirements in self.courses.items():
            if course in ["Réseaux 2", "Artificial Intelligence"]:
                # These two courses have special treatment with different teachers for lectures/TDs and TPs
                if requirements.get("lecture", 0) > 0:
                    self.variables.append(f"{course}_lecture")
                if requirements.get("td", 0) > 0:
                    self.variables.append(f"{course}_td")
                if requirements.get("tp", 0) > 0:
                    self.variables.append(f"{course}_tp")
            else:
                # Standard courses with single teacher for all sessions
                if requirements.get("lecture", 0) > 0:
                    self.variables.append(f"{course}_lecture")
                if requirements.get("td", 0) > 0:
                    self.variables.append(f"{course}_td")
        
        # Initialize domains for each variable (initially all time slots are possible)
        self.domains = {var: copy.deepcopy(self.all_slots) for var in self.variables}
        
        # Track teacher assignments to help with constraints like consecutive slots
        self.teacher_slots = defaultdict(list)
        
        # Initialize the list of constraints between variables
        self.constraints = []
        self._create_constraints()
    
    def _create_constraints(self):
        """
        Create all binary constraints between variables.
        Each constraint is a tuple (var1, var2, constraint_function)
        where constraint_function takes two values and returns True if the constraint is satisfied.
        """
        # 1. Different sessions should be scheduled in different slots
        # This ensures no conflicts in the timetable for the same group
        for i, var1 in enumerate(self.variables):
            for var2 in self.variables[i+1:]:
                self.constraints.append((var1, var2, lambda a, b: a != b))
        
        # 2. Lectures and TDs of the same course should not be in the same slot
        # This ensures sessions of the same course are distributed properly
        for course in self.courses:
            if course in ["Réseaux 2", "Artificial Intelligence"]:
                # For these courses, we need to handle lecture, TD, and TP
                session_types = []
                if self.courses[course].get("lecture", 0) > 0:
                    session_types.append(f"{course}_lecture")
                if self.courses[course].get("td", 0) > 0:
                    session_types.append(f"{course}_td")
                if self.courses[course].get("tp", 0) > 0:
                    session_types.append(f"{course}_tp")
                
                # Create constraints between all pairs of sessions for this course
                for i, var1 in enumerate(session_types):
                    for var2 in session_types[i+1:]:
                        self.constraints.append((var1, var2, lambda a, b: a != b))
            else:
                # For standard courses, just ensure lecture and TD are in different slots
                lecture_var = f"{course}_lecture"
                td_var = f"{course}_td"
                if lecture_var in self.variables and td_var in self.variables:
                    self.constraints.append((lecture_var, td_var, lambda a, b: a != b))
    
    def get_teacher_for_session(self, var):
        """
        Get the teacher responsible for a specific session.
        
        Args:
            var (str): The variable name representing a course session
            
        Returns:
            str: The teacher assigned to this session
        """
        # Parse the variable name to get course name and session type
        parts = var.split('_')
        course_name = parts[0]
        if len(parts) > 2:  # For courses with spaces in their names
            course_name += " " + parts[1]
            session_type = parts[2]
        else:
            session_type = parts[1]
        
        # Return the appropriate teacher based on the course and session type
        if course_name in ["Réseaux 2", "Artificial Intelligence"]:
            if session_type in ["lecture", "td"]:
                return self.courses[course_name]["teacher_lecture_td"]
            elif session_type == "tp":
                # For simplicity, we'll assign the first TP teacher
                # In a more advanced version, you could distribute TPs among multiple teachers
                return self.courses[course_name]["teacher_tp"][0]
        else:
            return self.courses[course_name]["teacher"]
    
    def ac3(self):
        """
        Arc Consistency Algorithm #3 (AC3) for preprocessing.
        Reduces domains by eliminating values that cannot be part of any solution.
        
        Returns:
            bool: True if the CSP is still solvable after domain reduction, False otherwise
        """
        # Initialize a queue with all binary constraints
        queue = deque(self.constraints)
        
        while queue:
            # Pop a constraint from the queue
            (xi, xj, constraint) = queue.popleft()
            
            # Try to reduce the domain of xi based on the constraint with xj
            if self.revise(xi, xj, constraint):
                # If xi's domain becomes empty, the problem is unsolvable
                if len(self.domains[xi]) == 0:
                    return False
                
                # If xi's domain changed, we need to check all constraints involving xi
                for xk, xl, c in self.constraints:
                    if xk == xi and xl != xj:
                        queue.append((xl, xi, c))
                    elif xl == xi and xk != xj:
                        queue.append((xk, xi, c))
        return True
    
    def revise(self, xi, xj, constraint):
        """
        Revise the domain of xi with respect to xj based on the constraint.
        Remove values from xi's domain that violate the constraint with all values in xj's domain.
        
        Args:
            xi (str): First variable
            xj (str): Second variable
            constraint (function): Binary constraint function
            
        Returns:
            bool: True if xi's domain was changed, False otherwise
        """
        revised = False
        domain_copy = copy.deepcopy(self.domains[xi])
        
        for x in domain_copy:
            # If no value in xj's domain satisfies the constraint with x
            # Then x cannot be part of any solution and should be removed
            if not any(constraint(x, y) for y in self.domains[xj]):
                self.domains[xi].remove(x)
                revised = True
        
        return revised
    
    def mrv_heuristic(self, unassigned_vars):
        """
        Minimum Remaining Values (MRV) heuristic.
        Selects the variable with the fewest legal values remaining in its domain.
        
        Args:
            unassigned_vars (list): List of unassigned variables
            
        Returns:
            str: The variable with the smallest domain size
        """
        return min(unassigned_vars, key=lambda var: len(self.domains[var]))
    
    def lcv_heuristic(self, var):
        """
        Least Constraining Value (LCV) heuristic.
        Orders domain values based on how much they constrain future variables.
        Values that rule out fewer choices for neighboring variables are tried first.
        
        Args:
            var (str): The variable to find LCV ordering for
            
        Returns:
            list: Sorted list of values from least constraining to most constraining
        """
        # Count how many values would be eliminated from the domains of other variables
        # for each possible value of var
        def count_conflicts(value):
            conflicts = 0
            for other_var, _, constraint in self.constraints:
                if other_var != var:
                    for other_value in self.domains[other_var]:
                        if not constraint(value, other_value):
                            conflicts += 1
            return conflicts
        
        # Return values sorted by the number of conflicts they would cause
        # (least constraining values first)
        return sorted(self.domains[var], key=count_conflicts)
    
    def check_successive_slots(self, assignment, var, value):
        """
        Check if assigning value to var would create more than 3 consecutive slots for a teacher.
        This is a hard constraint from the problem definition.
        
        Args:
            assignment (dict): Current partial assignment
            var (str): Variable to be assigned
            value (tuple): Value (day, slot) to be assigned to var
            
        Returns:
            bool: True if the constraint is satisfied, False otherwise
        """
        teacher = self.get_teacher_for_session(var)
        day = value[0]
        slot = value[1]
        
        # Get all slots for this teacher on this day (including the new assignment)
        teacher_day_slots = [s[1] for v, s in assignment.items() 
                            if self.get_teacher_for_session(v) == teacher and s[0] == day]
        teacher_day_slots.append(slot)
        
        # Sort slots to check for consecutive sequences
        teacher_day_slots.sort()
        
        # Check for sequences of 4 or more consecutive slots
        consecutive_slots = 1
        max_consecutive = 1  # Track the maximum consecutive slots
        
        for i in range(1, len(teacher_day_slots)):
            if teacher_day_slots[i] == teacher_day_slots[i-1] + 1:
                consecutive_slots += 1
                max_consecutive = max(max_consecutive, consecutive_slots)
            else:
                consecutive_slots = 1
        
        # If we have more than 3 consecutive slots, the constraint is violated
        return max_consecutive <= 3
    
    def check_teacher_workdays(self, assignment, var, value):
        """
        Check if assigning value to var would exceed the maximum of two workdays for a teacher.
        This is a soft constraint - we'll allow it to be violated if necessary.
        
        Args:
            assignment (dict): Current partial assignment
            var (str): Variable to be assigned
            value (tuple): Value (day, slot) to be assigned to var
            
        Returns:
            bool: True if the constraint is satisfied, False otherwise
        """
        teacher = self.get_teacher_for_session(var)
        day = value[0]
        
        # Get all days for this teacher (including the new assignment)
        teacher_days = {s[0] for v, s in assignment.items() 
                       if self.get_teacher_for_session(v) == teacher}
        teacher_days.add(day)
        
        # Return True if constraint is satisfied (max 2 days), False otherwise
        return len(teacher_days) <= 2
    
    def is_consistent(self, var, value, assignment):
        """
        Check if assigning value to var is consistent with the current assignment.
        Checks all constraints involving var.
        
        Args:
            var (str): Variable to be assigned
            value (tuple): Value (day, slot) to be assigned to var
            assignment (dict): Current partial assignment
            
        Returns:
            bool: True if the assignment is consistent, False otherwise
        """
        # Check binary constraints with already assigned variables
        for var2, val2 in assignment.items():
            for var_i, var_j, constraint in self.constraints:
                if (var_i == var and var_j == var2) or (var_i == var2 and var_j == var):
                    if var_i == var:
                        if not constraint(value, val2):
                            return False
                    else:
                        if not constraint(val2, value):
                            return False
        
        # Check hard constraint: No more than 3 successive slots for a teacher
        if not self.check_successive_slots(assignment, var, value):
            return False
        
        # Check soft constraint: teacher should have a maximum of two days
        # We track this but don't enforce it strictly as it's a soft constraint
        if not self.check_teacher_workdays(assignment, var, value):
            # Soft constraint violation, but we'll allow it for now
            pass
        
        return True
    
    def backtracking_search(self):
        """
        Main backtracking search algorithm with MRV and LCV heuristics.
        
        Returns:
            dict: Complete assignment if a solution is found, None otherwise
        """
        # Apply AC3 for preprocessing to reduce domains
        if not self.ac3():
            return None  # No solution exists after AC3 preprocessing
        
        # Start the recursive backtracking search
        return self._backtrack({})
    
    def _backtrack(self, assignment):
        """
        Recursive backtracking algorithm to find a solution.
        
        Args:
            assignment (dict): Current partial assignment
            
        Returns:
            dict: Complete assignment if found, None otherwise
        """
        # If all variables are assigned, we have a complete solution
        if len(assignment) == len(self.variables):
            return assignment
        
        # Select unassigned variable using MRV heuristic
        unassigned = [var for var in self.variables if var not in assignment]
        var = self.mrv_heuristic(unassigned)
        
        # Try values in order of least constraining (LCV heuristic)
        for value in self.lcv_heuristic(var):
            # Check if this assignment is consistent with current assignment
            if self.is_consistent(var, value, assignment):
                # Make the assignment
                assignment[var] = value
                
                # Recursive call to continue with next variable
                result = self._backtrack(assignment)
                if result is not None:
                    return result
                
                # If no solution found, backtrack by removing the assignment
                del assignment[var]
        
        return None  # No solution found
    
    def print_solution(self, solution):
        """
        Print the timetable solution in a readable format.
        Also evaluates how well the soft constraints are satisfied.
        
        Args:
            solution (dict): The complete assignment of variables to values
        """
        if solution is None:
            print("No solution found.")
            return
        
        # Create empty timetable structure
        timetable = {day: {slot: [] for slot in range(1, self.slots_per_day[day] + 1)} 
                     for day in self.days}
        
        # Fill timetable with assigned sessions
        for var, (day, slot) in solution.items():
            # Parse variable name to get course and session type
            parts = var.split('_')
            course = parts[0]
            if len(parts) > 2:  # For courses with spaces in their names
                course += " " + parts[1]
                session_type = parts[2]
            else:
                session_type = parts[1]
            
            # Get the teacher for this session
            teacher = self.get_teacher_for_session(var)
            timetable[day][slot].append(f"{course} ({session_type}) - {teacher}")
        
        # Print timetable in a readable format
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
        
        # Check and display how well the soft constraints are satisfied
        self._evaluate_soft_constraints(solution)
        # Check and display information about consecutive slots
        self._check_consecutive_slots(solution)
    
    def _evaluate_soft_constraints(self, solution):
        """
        Evaluate how well the soft constraints are satisfied in the solution.
        
        Args:
            solution (dict): The complete assignment of variables to values
        """
        # Check teacher workday constraint (max 2 days per teacher)
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
    
    def _check_consecutive_slots(self, solution):
        """
        Check and display information about consecutive slots for each teacher.
        
        Args:
            solution (dict): The complete assignment of variables to values
        """
        print("\nConsecutive Slots Check (Hard Constraint - Max 3 consecutive slots):")
        
        # Group slots by teacher and day
        teacher_day_slots = defaultdict(lambda: defaultdict(list))
        
        for var, (day, slot) in solution.items():
            teacher = self.get_teacher_for_session(var)
            teacher_day_slots[teacher][day].append(slot)
        
        # Check consecutive slots for each teacher on each day
        for teacher, days in teacher_day_slots.items():
            print(f"  {teacher}:")
            for day, slots in days.items():
                slots.sort()  # Sort slots to find consecutive sequences
                
                # Find the longest sequence of consecutive slots
                max_consecutive = 1
                consecutive = 1
                
                for i in range(1, len(slots)):
                    if slots[i] == slots[i-1] + 1:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 1
                
                # Print information about consecutive slots
                print(f"    {day}: {slots} (Max consecutive: {max_consecutive})")
                if max_consecutive > 3:
                    print("      WARNING: More than 3 consecutive slots - Hard constraint violated!")

# Main execution
if __name__ == "__main__":
    # Create and solve the CSP
    csp = TimeTableCSP()
    solution = csp.backtracking_search()
    csp.print_solution(solution)