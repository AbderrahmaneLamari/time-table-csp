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
        
        # Add additional constraints
        self._add_lecture_distribution_constraint()
        self._add_student_consecutive_slots_constraint()
    
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
    
    def _add_lecture_distribution_constraint(self):
        """
        Add constraints to ensure:
        1. Lectures are in slots by themselves (no other sessions at same time)
        2. Lectures are distributed across different time slots
        """
        # Get all lecture variables
        lecture_vars = [var for var in self.variables if var.endswith('_lecture')]
        
        # Add binary constraints between each pair of lecture variables
        for i, var1 in enumerate(lecture_vars):
            for var2 in lecture_vars[i+1:]:
                self.constraints.append((var1, var2, lambda a, b: a != b))
            
            # Add constraints between lectures and all group sessions
            for group_num in range(1, self.num_groups + 1):
                for var2 in [var for var in self.variables if f"_group{group_num}" in var]:
                    self.constraints.append((var1, var2, lambda a, b: a != b))
    
    def _add_student_consecutive_slots_constraint(self):
        """
        Add constraints to prevent students from having more than 3 consecutive slots.
        """
        # For each group, ensure no more than 3 consecutive slots are filled
        for group_num in range(1, self.num_groups + 1):
            group_vars = [var for var in self.variables if f"_group{group_num}" in var]
            
            # For each day, we'll need to check sequences of slots
            for day in self.days:
                day_vars = [var for var in group_vars if var in self.domains and any(slot[0] == day for slot in self.domains[var])]
                
                # We'll model this as a constraint that no 4 consecutive slots can all be assigned
                # This is a complex constraint that we'll need to check during search
                pass  # Actual checking happens in is_consistent()
    
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
        if course1 == course2 and ((session_type1 == "lecture" and session_type2 in ["td", "tp"]) or
                                   (session_type2 == "lecture" and session_type1 in ["td", "tp"])):
            return True
        
        return False
    
    def _parse_variable(self, var):
        """
        Parse a variable name to extract course, session type, and group.
        """
        parts = var.split('_')
        
        # Handle courses with spaces in their names
        if len(parts) > 2 and parts[1] not in ["lecture", "td", "tp"]:
            course_parts = []
            session_idx = 0
            
            for i, part in enumerate(parts):
                if part in ["lecture", "td", "tp"]:
                    session_idx = i
                    break
                course_parts.append(part)
            
            course = " ".join(course_parts)
            session_type = parts[session_idx]
            remaining_parts = parts[session_idx+1:]
        else:
            course = parts[0]
            session_type = parts[1]
            remaining_parts = parts[2:]
        
        # Check for group information
        group = None
        for part in remaining_parts:
            if part.startswith("group"):
                try:
                    group = int(part[5:])  # Extract group number from "group1"
                    break
                except ValueError:
                    pass
        
        return course, session_type, group
    
    def get_teacher_for_session(self, var):
        """
        Get the teacher responsible for a specific session.
        """
        course, session_type, group = self._parse_variable(var)
        
        if course not in self.courses:
            return f"Unknown_Teacher_{var}"
        
        if session_type == "lecture":
            return self.courses[course]["teacher_lecture"]
        elif session_type == "td":
            # If it's a group-specific TD session
            if group is not None and "group_teachers_td" in self.courses[course]:
                return self.courses[course]["group_teachers_td"][group - 1]
            return self.courses[course].get("teacher_td", self.courses[course]["teacher_lecture"])
        elif session_type == "tp":
            # If it's a group-specific TP session
            if group is not None and "group_teachers_tp" in self.courses[course]:
                return self.courses[course]["group_teachers_tp"][group - 1]
            if "teacher_tp" in self.courses[course] and isinstance(self.courses[course]["teacher_tp"], list):
                return self.courses[course]["teacher_tp"][0]
            return f"Unknown_TP_Teacher_{var}"
        
        return f"Unknown_Teacher_{var}"
    
    def ac3(self):
        """
        Arc Consistency Algorithm #3 (AC3) for preprocessing.
        """
        queue = deque(self.constraints)
        
        while queue:
            (xi, xj, constraint) = queue.popleft()
            
            if self.revise(xi, xj, constraint):
                if len(self.domains[xi]) == 0:
                    return False
                
                for xk, xl, c in self.constraints:
                    if xk == xi and xl != xj:
                        queue.append((xl, xi, c))
                    elif xl == xi and xk != xj:
                        queue.append((xk, xi, c))
        return True
    
    def revise(self, xi, xj, constraint):
        """
        Revise the domain of xi with respect to xj based on the constraint.
        """
        revised = False
        domain_copy = copy.deepcopy(self.domains[xi])
        
        for x in domain_copy:
            if not any(constraint(x, y) for y in self.domains[xj]):
                self.domains[xi].remove(x)
                revised = True
        
        return revised
    
    def mrv_heuristic(self, unassigned_vars):
        """
        Minimum Remaining Values (MRV) heuristic.
        """
        return min(unassigned_vars, key=lambda var: len(self.domains[var]))
    
    def lcv_heuristic(self, var):
        """
        Least Constraining Value (LCV) heuristic.
        """
        def count_conflicts(value):
            conflicts = 0
            for other_var, v2, constraint in [(v1, v2, c) for v1, v2, c in self.constraints 
                                           if v1 == var or v2 == var]:
                if other_var in self.domains:
                    for other_value in self.domains[other_var]:
                        if not constraint(value, other_value):
                            conflicts += 1
            return conflicts
        
        return sorted(self.domains[var], key=count_conflicts)
    
    def check_successive_slots(self, assignment, var, value):
        """
        Check if assigning value to var would create more than 3 consecutive slots for a teacher.
        """
        teacher = self.get_teacher_for_session(var)
        day = value[0]
        slot = value[1]
        
        teacher_day_slots = [s[1] for v, s in assignment.items() 
                            if self.get_teacher_for_session(v) == teacher and s[0] == day]
        teacher_day_slots.append(slot)
        teacher_day_slots.sort()
        
        consecutive_slots = 1
        max_consecutive = 1
        
        for i in range(1, len(teacher_day_slots)):
            if teacher_day_slots[i] == teacher_day_slots[i-1] + 1:
                consecutive_slots += 1
                max_consecutive = max(max_consecutive, consecutive_slots)
            else:
                consecutive_slots = 1
        
        return max_consecutive <= 3
    
    def check_student_consecutive_slots(self, assignment, var, value):
        """
        Check if assigning value to var would create more than 3 consecutive slots for students.
        """
        _, _, group = self._parse_variable(var)
        if group is None:  # Lectures affect all groups
            groups_to_check = range(1, self.num_groups + 1)
        else:
            groups_to_check = [group]
        
        day = value[0]
        slot = value[1]
        
        for group_num in groups_to_check:
            group_slots = [s[1] for v, s in assignment.items() 
                          if (self._parse_variable(v)[2] == group_num or 
                              (self._parse_variable(v)[2] is None and v.endswith('_lecture'))) 
                          and s[0] == day]
            group_slots.append(slot)
            group_slots = list(set(group_slots))  # Remove duplicates from lectures
            group_slots.sort()
            
            consecutive_slots = 1
            max_consecutive = 1
            
            for i in range(1, len(group_slots)):
                if group_slots[i] == group_slots[i-1] + 1:
                    consecutive_slots += 1
                    max_consecutive = max(max_consecutive, consecutive_slots)
                else:
                    consecutive_slots = 1
            
            if max_consecutive > 3:
                return False
        
        return True
    
    def check_teacher_workdays(self, assignment, var, value):
        """
        Check if assigning value to var would exceed the maximum of two workdays for a teacher.
        """
        teacher = self.get_teacher_for_session(var)
        day = value[0]
        
        teacher_days = {s[0] for v, s in assignment.items() 
                       if self.get_teacher_for_session(v) == teacher}
        teacher_days.add(day)
        
        return len(teacher_days) <= 2
    
    def is_consistent(self, var, value, assignment):
        """
        Check if assigning value to var is consistent with the current assignment.
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
        
        # Check hard constraint: No more than 3 consecutive slots for students
        if not self.check_student_consecutive_slots(assignment, var, value):
            return False
        
        # Check soft constraint: teacher should have a maximum of two days
        if not self.check_teacher_workdays(assignment, var, value):
            pass  # Soft constraint violation, but we'll allow it
        
        return True
    
    def backtracking_search(self):
        """
        Main backtracking search algorithm with MRV and LCV heuristics.
        """
        if not self.ac3():
            return None
        
        self._distribute_lecture_domains()
        return self._backtrack({})
    
    def _distribute_lecture_domains(self):
        """
        Distribute lecture domains to favor spreading them across the week.
        """
        lecture_vars = [var for var in self.variables if var.endswith('_lecture')]
        days = list(self.slots_per_day.keys())
        random.shuffle(days)
        
        for i, var in enumerate(lecture_vars):
            preferred_day = days[i % len(days)]
            preferred_slots = [(preferred_day, slot) for slot in range(1, self.slots_per_day[preferred_day] + 1)]
            other_slots = [slot for slot in self.domains[var] if slot not in preferred_slots]
            self.domains[var] = preferred_slots + other_slots
    
    def _backtrack(self, assignment):
        """
        Recursive backtracking algorithm to find a solution.
        """
        if len(assignment) == len(self.variables):
            return assignment
        
        unassigned = [var for var in self.variables if var not in assignment]
        var = self.mrv_heuristic(unassigned)
        
        for value in self.lcv_heuristic(var):
            if self.is_consistent(var, value, assignment):
                assignment[var] = value
                result = self._backtrack(assignment)
                if result is not None:
                    return result
                del assignment[var]
        
        return None
    
    def print_solution(self, solution):
        """
        Print the timetable solution in a readable format.
        """
        if solution is None:
            print("No solution found.")
            return
        
        group_timetables = {}
        for group_num in range(1, self.num_groups + 1):
            group_timetables[group_num] = {day: {slot: [] for slot in range(1, self.slots_per_day[day] + 1)} 
                                         for day in self.days}
        
        for var, (day, slot) in solution.items():
            course, session_type, group = self._parse_variable(var)
            teacher = self.get_teacher_for_session(var)
            
            if session_type == "lecture":
                for group_num in range(1, self.num_groups + 1):
                    group_timetables[group_num][day][slot].append(f"{course} (lecture) - {teacher}")
            elif group is not None:
                group_timetables[group][day][slot].append(f"{course} ({session_type}) - {teacher}")
        
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
        
        self._evaluate_soft_constraints(solution)
        self._check_consecutive_slots(solution)
        self._show_lecture_distribution(solution)
        self._check_student_consecutive_slots(solution)
    
    def _evaluate_soft_constraints(self, solution):
        """
        Evaluate how well the soft constraints are satisfied in the solution.
        """
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
        Check consecutive slots for teachers.
        """
        print("\nTeacher Consecutive Slots Check (Hard Constraint - Max 3 consecutive slots):")
        
        teacher_day_slots = defaultdict(lambda: defaultdict(list))
        
        for var, (day, slot) in solution.items():
            teacher = self.get_teacher_for_session(var)
            teacher_day_slots[teacher][day].append(slot)
        
        all_satisfied = True
        for teacher, days in teacher_day_slots.items():
            print(f"  {teacher}:")
            for day, slots in days.items():
                slots.sort()
                max_consecutive = 1
                consecutive = 1
                
                for i in range(1, len(slots)):
                    if slots[i] == slots[i-1] + 1:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 1
                
                print(f"    {day}: {slots} (Max consecutive: {max_consecutive})")
                if max_consecutive > 3:
                    print("      WARNING: More than 3 consecutive slots - Hard constraint violated!")
                    all_satisfied = False
        
        print(f"\nTeacher Consecutive Slots Constraint: {'All Satisfied' if all_satisfied else 'Some Not Satisfied'}")
    
    def _check_student_consecutive_slots(self, solution):
        """
        Check consecutive slots for students.
        """
        print("\nStudent Consecutive Slots Check (Hard Constraint - Max 3 consecutive slots):")
        
        group_day_slots = defaultdict(lambda: defaultdict(list))
        
        for var, (day, slot) in solution.items():
            _, _, group = self._parse_variable(var)
            if group is not None:
                group_day_slots[group][day].append(slot)
            else:  # Lectures affect all groups
                for g in range(1, self.num_groups + 1):
                    group_day_slots[g][day].append(slot)
        
        all_satisfied = True
        for group, days in group_day_slots.items():
            print(f"  Group {group}:")
            for day, slots in days.items():
                slots = list(set(slots))  # Remove duplicates from lectures
                slots.sort()
                max_consecutive = 1
                consecutive = 1
                
                for i in range(1, len(slots)):
                    if slots[i] == slots[i-1] + 1:
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 1
                
                print(f"    {day}: {slots} (Max consecutive: {max_consecutive})")
                if max_consecutive > 3:
                    print("      WARNING: More than 3 consecutive slots - Hard constraint violated!")
                    all_satisfied = False
        
        print(f"\nStudent Consecutive Slots Constraint: {'All Satisfied' if all_satisfied else 'Some Not Satisfied'}")
    
    def _show_lecture_distribution(self, solution):
        """
        Display how lectures are distributed across the week.
        """
        lecture_vars = [var for var in self.variables if var.endswith('_lecture')]
        lecture_assignments = {var: solution[var] for var in lecture_vars if var in solution}
        
        print("\nLecture Distribution:")
        for day in self.days:
            day_lectures = [(var, slot) for var, (d, slot) in lecture_assignments.items() if d == day]
            day_lectures.sort(key=lambda x: x[1])
            
            print(f"  {day}:")
            for var, slot in day_lectures:
                course, _, _ = self._parse_variable(var)
                print(f"    Slot {slot}: {course}")
        
        used_days = {day for day, _ in lecture_assignments.values()}
        print(f"\nNumber of days used for lectures: {len(used_days)} out of {len(self.days)}")


if __name__ == "__main__":
    print("Initializing timetable CSP for 6 groups...")
    csp = MultiGroupTimeTableCSP(num_groups=6)
    print(f"Created {len(csp.variables)} variables.")
    print(f"Created {len(csp.constraints)} constraints.")
    print("\nSolving CSP with backtracking search (this may take a while)...")
    solution = csp.backtracking_search()
    csp.print_solution(solution)