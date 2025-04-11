from collections import defaultdict, deque
import random
import copy

class MultiGroupTimeTableCSP:
    def __init__(self, num_groups=6):
        """
        Initialize the TimeTable Constraint Satisfaction Problem for multiple groups
        - Define days, slots, courses, requirements
        - Create variables and their domains for shared lectures and group-specific TDs/TPs
        - Set up constraints
        
        Args:
            num_groups (int): Number of student groups to schedule
        """
        self.num_groups = num_groups
        
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
        # For simplicity, we'll keep the same teachers for all groups
        self.courses = {
            "Sécurité": {"lecture": 1, "td": 1, "teacher_lecture": "Teacher 1", "teacher_td": "Teacher 1"},
            "Méthodes formelles": {"lecture": 1, "td": 1, "teacher_lecture": "Teacher 2", "teacher_td": "Teacher 2"},
            "Analyse numérique": {"lecture": 1, "td": 1, "teacher_lecture": "Teacher 3", "teacher_td": "Teacher 3"},
            "Entrepreneuriat": {"lecture": 1, "td": 0, "teacher_lecture": "Teacher 4"},
            "Recherche opérationnelle 2": {"lecture": 1, "td": 1, "teacher_lecture": "Teacher 5", "teacher_td": "Teacher 5"},
            "Distributed Architecture & Intensive Computing": {"lecture": 1, "td": 1, "teacher_lecture": "Teacher 6", "teacher_td": "Teacher 6"},
            "Réseaux 2": {"lecture": 1, "td": 1, "tp": 1, 
                          "teacher_lecture": "Teacher 7", 
                          "teacher_td": "Teacher 7", 
                          "teacher_tp": ["Teacher 8", "Teacher 9", "Teacher 10"]},
            "Artificial Intelligence": {"lecture": 1, "td": 1, "tp": 1, 
                                       "teacher_lecture": "Teacher 11", 
                                       "teacher_td": "Teacher 11", 
                                       "teacher_tp": ["Teacher 12", "Teacher 13", "Teacher 14"]}
        }
        
        # Assign additional teachers for TD/TP sessions for multiple groups
        # In a real scenario, you would have different teachers for different groups
        # Here we'll simulate by extending the original teachers
        self._assign_group_teachers()
        
        # Create variables based on course requirements
        self.variables = []
        self._create_variables()
        
        # Initialize domains for each variable (initially all time slots are possible)
        self.domains = {var: copy.deepcopy(self.all_slots) for var in self.variables}
        
        # Track teacher assignments to help with constraints like consecutive slots
        self.teacher_slots = defaultdict(list)
        
        # Initialize the list of constraints between variables
        self.constraints = []
        self._create_constraints()
    
    def _assign_group_teachers(self):
        """
        Assign teachers for TD/TP sessions for multiple groups.
        For simplicity, we'll create derived teacher names based on the original ones.
        """
        # For courses with TD sessions
        for course, details in self.courses.items():
            if "td" in details and details["td"] > 0:
                base_teacher = details.get("teacher_td", details.get("teacher_lecture"))
                details["group_teachers_td"] = [f"{base_teacher}_Group{g}" for g in range(1, self.num_groups + 1)]
            
            # For courses with TP sessions
            if "tp" in details and details["tp"] > 0:
                details["group_teachers_tp"] = []
                for g in range(1, self.num_groups + 1):
                    # Rotate through available TP teachers
                    base_teachers = details["teacher_tp"]
                    teacher_idx = g % len(base_teachers)
                    details["group_teachers_tp"].append(f"{base_teachers[teacher_idx]}_Group{g}")
    
    def _create_variables(self):
        """
        Create variables for all course sessions.
        - Lectures are shared among all groups
        - TD and TP sessions are specific to each group
        """
        # Create shared lecture variables (one lecture for all groups)
        for course in self.courses:
            if self.courses[course].get("lecture", 0) > 0:
                self.variables.append(f"{course}_lecture")
        
        # Create group-specific TD and TP variables
        for group_num in range(1, self.num_groups + 1):
            for course, requirements in self.courses.items():
                if requirements.get("td", 0) > 0:
                    self.variables.append(f"{course}_td_group{group_num}")
                if requirements.get("tp", 0) > 0:
                    self.variables.append(f"{course}_tp_group{group_num}")
    
    def _create_constraints(self):
        """
        Create all constraints between variables.
        1. Different sessions shouldn't be in the same time slot
        2. Group-specific sessions (TDs/TPs) for the same course shouldn't be at the same time as the lecture
        3. Sessions for the same group shouldn't be at the same time
        4. Teachers can't teach multiple sessions at the same time
        """
        # 1. All variables need different time slots if they involve the same group or teacher
        for i, var1 in enumerate(self.variables):
            for var2 in self.variables[i+1:]:
                # Check if the variables belong to the same group or have the same teacher
                if self._should_add_constraint(var1, var2):
                    self.constraints.append((var1, var2, lambda a, b: a != b))
    
    def _should_add_constraint(self, var1, var2):
        """
        Determine if a constraint should be added between two variables.
        
        Args:
            var1, var2 (str): Variable names
            
        Returns:
            bool: True if a constraint should be added
        """
        # Extract course, session type, and group from variable names
        course1, session_type1, group1 = self._parse_variable(var1)
        course2, session_type2, group2 = self._parse_variable(var2)
        
        # Case 1: Same group can't have multiple sessions at the same time
        if group1 == group2 and group1 is not None:
            return True
        
        # Case 2: Same teacher can't teach multiple sessions at the same time
        teacher1 = self.get_teacher_for_session(var1)
        teacher2 = self.get_teacher_for_session(var2)
        if teacher1 == teacher2:
            return True
        
        # Case 3: Lecture and group sessions of the same course need different times
        if course1 == course2 and ((session_type1 == "lecture" and group2 is not None) or
                                   (session_type2 == "lecture" and group1 is not None)):
            return True
        
        return False
    
    def _parse_variable(self, var):
        """
        Parse a variable name to extract course, session type, and group.
        
        Args:
            var (str): Variable name (e.g., "Sécurité_lecture" or "Sécurité_td_group1")
            
        Returns:
            tuple: (course_name, session_type, group_number)
        """
        parts = var.split('_')
        
        # Handle courses with spaces in their names
        if len(parts) > 2 and parts[1] not in ["lecture", "td", "tp"]:
            course = f"{parts[0]} {parts[1]}"
            parts = [course] + parts[2:]
        else:
            course = parts[0]
        
        session_type = parts[1]  # lecture, td, or tp
        
        # Check for group information
        group = None
        if len(parts) > 2 and parts[2].startswith("group"):
            group = int(parts[2][5:])  # Extract group number from "group1"
        
        return course, session_type, group
    
    def get_teacher_for_session(self, var):
        """
        Get the teacher responsible for a specific session.
        
        Args:
            var (str): The variable name representing a course session
            
        Returns:
            str: The teacher assigned to this session
        """
        course, session_type, group = self._parse_variable(var)
        
        if session_type == "lecture":
            return self.courses[course]["teacher_lecture"]
        elif session_type == "td":
            # If it's a group-specific TD session
            if group is not None:
                return self.courses[course]["group_teachers_td"][group - 1]
            # For courses where the same teacher does lectures and TDs
            return self.courses[course].get("teacher_td", self.courses[course]["teacher_lecture"])
        elif session_type == "tp":
            # If it's a group-specific TP session
            if group is not None:
                return self.courses[course]["group_teachers_tp"][group - 1]
            # For single-group scenarios
            return self.courses[course]["teacher_tp"][0]
    
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
        def count_conflicts(value):
            conflicts = 0
            for other_var, v2, constraint in [(v1, v2, c) for v1, v2, c in self.constraints 
                                           if v1 == var or v2 == var]:
                other = other_var if other_var != var else v2
                if other in self.domains:  # Make sure the other variable still has a domain
                    for other_value in self.domains[other]:
                        if not constraint(value, other_value):
                            conflicts += 1
            return conflicts
        
        # Return values sorted by the number of conflicts they would cause
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
        
        # Create timetables for each group
        group_timetables = {}
        for group_num in range(1, self.num_groups + 1):
            group_timetables[group_num] = {day: {slot: [] for slot in range(1, self.slots_per_day[day] + 1)} 
                                         for day in self.days}
        
        # Fill timetables with assigned sessions
        for var, (day, slot) in solution.items():
            course, session_type, group = self._parse_variable(var)
            teacher = self.get_teacher_for_session(var)
            
            # For lectures (shared among all groups)
            if session_type == "lecture":
                for group_num in range(1, self.num_groups + 1):
                    group_timetables[group_num][day][slot].append(f"{course} (lecture) - {teacher}")
            # For group-specific sessions (TD/TP)
            elif group is not None:
                group_timetables[group][day][slot].append(f"{course} ({session_type}) - {teacher}")
        
        # Print timetables for each group
        for group_num, timetable in group_timetables.items():
            print(f"\n===== TIMETABLE FOR GROUP {group_num} =====")
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
        all_satisfied = True
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
                    all_satisfied = False
        
        print(f"\nConsecutive Slots Constraint: {'All Satisfied' if all_satisfied else 'Some Not Satisfied'}")


# Main execution
if __name__ == "__main__":
    # Create and solve the CSP for multiple groups
    print("Initializing timetable CSP for 6 groups...")
    csp = MultiGroupTimeTableCSP(num_groups=6)
    print(f"Created {len(csp.variables)} variables.")
    print(f"Created {len(csp.constraints)} constraints.")
    print("\nSolving CSP with backtracking search (this may take a while)...")
    solution = csp.backtracking_search()
    csp.print_solution(solution)