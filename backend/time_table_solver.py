from collections import defaultdict, deque
import random
import copy
import sys
sys.setrecursionlimit(42000)

SLOTS = [
        (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
        (3, 1), (3, 2), (3, 3),
        (4, 1), (4, 2), (4, 3), (4, 4), (4, 5),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5)
        ]
TEACHERS = list(range(1, 15))

# Groups from 1 to 6
GROUPS = list(range(1, 7))

from collections import defaultdict

from collections import defaultdict

def serialize_schedule(schedule: dict) -> dict:
    """
    Transform a CSP-style schedule dict into a JSON-friendly format
    grouped by group number, then by course name.

    Args:
        schedule (dict): A dict with keys like ('Course_type', group_id)
                         and values like [((day, slot), teacher_id, group_id)]

    Returns:
        dict: A structured dict in the form:
              {
                  "1": {
                      "CourseName": [
                          {
                              "course_type": ...,
                              "day": ...,
                              "slot": ...,
                              "teacher_id": ...
                          }
                      ],
                      ...
                  },
                  ...
              }
    """
    grouped_schedule = defaultdict(lambda: defaultdict(list))

    # Iterate over the schedule dictionary
    for (course_type, group_id), entries in schedule.items():
        for (day_slot, teacher_id, group) in entries:
            # Extract the course name (before the first '_')
            course_name = course_type.split("_")[0]
            
            # Create the dictionary structure for each group and course
            grouped_schedule[str(group)][course_name].append({
                "course_type": course_type,
                "day": day_slot[0],
                "slot": day_slot[1],
                "teacher_id": teacher_id
            })

    return dict(grouped_schedule)



class MultiGroupTimeTableCSP:

    def assign_lectures_across_week(self, variables, slots):
        # Extract lecture variables
        lecture_vars = [var for var in variables if "_lecture" in var[0]]
        lecture_vars.sort()

        # Get all (day, 1) slots — first slot of each day
        first_slots = [slot for slot in slots if slot[1] == 1]
        first_slots.sort()  # Ensure (1,1), (2,1), ... in order

        schedule = {}
        total_days = len(first_slots)
        lec_index = 0

        # Double loop: outer over days, inner over lectures until all are scheduled
        while lec_index < len(lecture_vars):
            for slot in first_slots:
                if lec_index >= len(lecture_vars):
                    break
                schedule[lecture_vars[lec_index]] = slot
                lec_index += 1

        return schedule


    def filter_domains_by_group(self, domains):
        filtered_domains = {}

        for key, values in domains.items():
            course_name, group_id = key
            filtered = [val for val in values if val[2] == group_id]
            filtered_domains[key] = filtered
        return filtered_domains
    
    def __init__(self, num_groups=6):
        self.num_groups = num_groups
        
        
        
        self.courses = {
            "Sécurité": {"lecture": 1, "td": 1, "tp": 0, "teacher_lecture": 1, "teacher_td": 1},
            "Méthodes formelles": {"lecture": 1, "td": 1, "tp": 0, "teacher_lecture": 2, "teacher_td": 2},
            "Analyse numérique": {"lecture": 1, "td": 1, "tp": 0, "teacher_lecture": 3, "teacher_td": 3},
            "Entrepreneuriat": {"lecture": 1, "td": 0, "tp": 0, "teacher_lecture": 4},
            "Recherche opérationnelle 2": {"lecture": 1, "td": 1, "tp": 0, "teacher_lecture": 5, "teacher_td": 5},
            "Distributed Architecture & Intensive Computing": {"lecture": 1, "td": 1, "tp": 0, "teacher_lecture": 6, "teacher_td": 6},
            "Réseaux 2": {"lecture": 1, "td": 1, "tp": 1, 
                          "teacher_lecture": 7, 
                          "teacher_td": 7, 
                          "teacher_tp": [8, 9, 10]},
            "Artificial Intelligence": {"lecture": 1, "td": 1, "tp": 1, 
                                       "teacher_lecture": 11, 
                                       "teacher_td": 11, 
                                       "teacher_tp": [12, 13, 14]}
        }
        

        self.variables = []
        self._create_variables()
        self.mega_domain = [(day_slot, teacher, group) for day_slot in SLOTS for teacher in TEACHERS for group in GROUPS]
        self.domains = {var: copy.deepcopy(self.mega_domain) for var in self.variables}

        ## domain filtering:

        

        self.domains = self.filter_domains_by_group(self.domains)




        self.assignments = {('Sécurité_lecture', 1): [((1, 1), 1, 1),((1, 1), 1, 2),((1, 1), 1, 3),((1, 1), 1, 4),((1, 1), 1, 5),((1, 1), 1, 6)], ('Méthodes formelles_lecture', 1): [((1, 3), 2, 1),((1, 3), 2, 2),((1, 3), 2, 3),((1, 3), 2, 4),((1, 3), 2, 5),((1, 3), 2, 6)], ('Analyse numérique_lecture', 1): [((2, 1), 3, 1),((2, 1), 3, 2),((2, 1), 3,3),((2, 1), 3, 4),((2, 1), 3, 5),((2, 1), 3, 6)], ('Entrepreneuriat_lecture', 1): [((2, 3), 4, 1),((2, 3), 4, 2),((2, 3), 4, 3),((2, 3), 4, 4),((2, 3), 4, 5),((2, 3), 4, 6)], ('Recherche opérationnelle 2_lecture', 1): [((2, 5), 5, 1),((2, 5), 5, 2),((2, 5), 5, 3),((2, 5), 5, 4),((2, 5), 5, 5),((2, 5), 5, 6)], ('Distributed Architecture & Intensive Computing_lecture', 1): [((3, 2), 6, 1),((3, 2), 6, 2),((3, 2), 6, 3),((3, 2), 6, 4),((3, 2), 6, 5),((3, 2), 6, 6)], ('Réseaux 2_lecture', 1): [((4, 1), 7, 1),((4, 1), 7, 2),((4, 1), 7, 3),((4, 1), 7, 4),((4, 1), 7, 6)], ('Artificial Intelligence_lecture', 1): [((4, 5), 11, 1),((4, 5), 11, 2),((4, 5), 11, 3),((4, 5), 11, 4),((4, 5), 11, 5),((4, 5), 11, 6)]}
        # create constraints.
        self.constraint_functions = [self.teacher_same_slot_diff_group, self.diffrent_lectre_same_groupe]

        self.constraints = [ (thing1, thing2, thing3) for thing1 in self.domains for thing2 in self.domains for thing3 in self.constraint_functions]

            # expresses the same teacher teaching two diffrent groups in the same time-slot
            # returns TRUE if satisfied, FALSE if violated
    def teacher_same_slot_diff_group(self, sched1, sched2):
            # sched1 ((a,b), teacher, group)
            # sched2 ((a,b), teacher, group)

            cren1, t1, g1 = sched1
            cren2, t2, g2 = sched2

            if t1 == t2 and cren1 == cren2:
                return False
            else:
                return True

            # expresses: the same group should have only one lecture in a time slot:
            # returns TRUE if satisfied, returns FALSE if violated

    def diffrent_lectre_same_groupe(self, sched1, sched2):
            # sched1 ((a,b), teacher, group)
            # sched2 ((a,b), teacher, group)

            cren1, t1, g1 = sched1
            cren2, t2, g2 = sched2

            if g1 == g2 and cren1 == cren2: 
                return False
            else: 
                return True

    
   
    def _create_variables(self):
    

        for course, data in self.courses.items():
            # One lecture for the whole group (shared)
            if data.get("lecture", 0) > 0:
                self.variables.append((f"{course}_lecture", 1))  # assuming lecture is for group 1 or global group

            # TD sessions: one per group
            if data.get("td", 0) > 0:
                for group_id in range(1, 7):  # groups 1 to 6
                    self.variables.append((f"{course}_td", group_id))

            # TP sessions: one per group
            if data.get("tp", 0) > 0:
                for group_id in range(1, 7):
                    self.variables.append((f"{course}_tp", group_id))

    
  
    def ac3(self):
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
        revised = False
        domain_copy = copy.deepcopy(self.domains[xi])
        
        for x in domain_copy:
            if not any(constraint(x, y) for y in self.domains[xj]):
                self.domains[xi].remove(x)
                revised = True
        
        return revised
    

    def mrv_heuristic(self, unassigned_vars):
        return min(unassigned_vars, key=lambda var: len(self.domains[var]))

    def select_unassigned_variable(self, assignment):
        unassigned_vars = [var for var in self.variables if var not in assignment or len(assignment.get(var, [])) == 0]
        return self.mrv_heuristic(unassigned_vars)

   
    def lcv_heuristic(self, var):
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
    
   
    def print_solution(self, solution):
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
        self._check_teacher_group_assignments(solution)
    
    # checks if the value to be assigned is consistent with the rest in the assignments dictionary:
    # returns TRUE if satisfied, FALSE if violated
    # - Now checking if there is more than 3 continueous slot usages
    # - checking if there is a td/tp lecture in the same slot as a Mo7adarah (Cours)
    
    

    def get_teacher_consecutive_slots(self, assignments):
        teacher_schedule = defaultdict(lambda: defaultdict(set))  # teacher -> day -> set of slot numbers

        # Fill the teacher's schedule
        for key, entries in assignments.items():
            if not isinstance(entries, list):
                entries = [entries]
            for (day, slot), teacher, group in entries:
                teacher_schedule[teacher][day].add(slot)


        # Compute max consecutive slots for each teacher per day
        teacher_consec = {}

        for teacher, days in teacher_schedule.items():
            teacher_consec[teacher] = {}
            for day, slots in days.items():
                sorted_slots = sorted(slots)
                max_consec = self.count_max_consecutive_slots(sorted_slots)
                teacher_consec[teacher][day] = max_consec

        return teacher_consec


    def get_group_consecutive_slots(self, assignments):
        group_schedule = defaultdict(lambda: defaultdict(set))  # group -> day -> set of slot numbers

        # Fill the group's schedule
        for key, entries in assignments.items():
            for (day, slot), teacher, group in entries:
                group_schedule[group][day].add(slot)

        # Compute max consecutive slots for each teacher per day
        group_consec = {}

        for group, days in group_schedule.items():
            group_consec[group] = {}
            for day, slots in days.items():
                sorted_slots = sorted(slots)
                max_consec = self.count_max_consecutive_slots(sorted_slots)
                group_consec[group][day] = max_consec

        return group_consec
    # should be private function
    def count_max_consecutive_slots(self, slots):
        if not slots:
            return 0
        max_count = count = 1
        for i in range(1, len(slots)):
            if slots[i] == slots[i-1] + 1:
                count += 1
                max_count = max(max_count, count)
            else:
                count = 1
        return max_count


    ## checks the consistency of the assinments
    # - teacher cannot work more than 3 consecutive hours
    # - group cannot study more that 3 consecutive hours
    def is_consistent(self, var, value, assignment):
        slot, teacher_id, group_id = value
        course_key, group = var  # var is a tuple (course_type_key, group_id)
        # check if the teacher is one of the appointed ones:
        # Extract course name and type

        if "_lecture" in course_key:
            course_name = course_key.replace("_lecture", "")
            teacher_allowed = self.courses[course_name]["teacher_lecture"]

        elif "_td" in course_key:
            course_name = course_key.replace("_td", "")
            teacher_allowed = self.courses[course_name]["teacher_td"]
        elif "_tp" in course_key:
            course_name = course_key.replace("_tp", "")
            teacher_allowed = self.courses[course_name]["teacher_tp"]
        else:
            return False  # Unknown type

        # Check if teacher is one of the allowed
        if isinstance(teacher_allowed, list):
            if teacher_id not in teacher_allowed:
                return False
        else:
            if teacher_id != teacher_allowed:
                return False
    
    
        # Check for slot conflicts with existing assignments
        for other_var, entries in assignment.items():
            for (other_slot, other_teacher, other_group) in entries:
                if slot == other_slot:
                    # Same time slot, check for teacher or group overlap
                    if teacher_id == other_teacher:
                        return False  # Same teacher at same time
                    if group_id == other_group:
                        return False  # Same group at same time


        # if lecture group is not the group being assigned. return FALSE
        if var[1] != value[2]:
            return False



        # Temporarily simulate assignment
        temp_assignment = assignment.copy()
        temp_assignment[var] = [value]

        # Check teacher's max consecutive hours
        teachers_hours = self.get_teacher_consecutive_slots(temp_assignment)
        for hours in teachers_hours.get(teacher_id, {}).values():
            if hours >= 4 and "lecture" not in var[0]:
                return False

        # Check group's max consecutive hours
        group_hours = self.get_group_consecutive_slots(temp_assignment)
        for hours in group_hours.get(group_id, {}).values():
            if hours >= 4:
                return False

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
        return  self.backtrack(self.assignments)
        # return self.complete_lecture_assignments(solution)

                    
    def complete_lecture_assignments(self, assignment, num_groups=6):
        new_assignment = assignment.copy()

        for key, value in list(assignment.items()):
            course_name, group_id = key
            if "lecture" in course_name:
                # Get base course name (e.g., "Sécurité_lecture" → "Sécurité_lecture")
                slot_info = value[0]  # ((day, slot), teacher, group)

                for g in range(1, num_groups + 1):
                    new_key = (course_name, g)
                    if new_key not in new_assignment:
                        # Copy same slot and teacher, just change group
                        (slot, teacher, _) = slot_info
                        new_assignment[new_key] = [(slot, teacher, g)]

        return new_assignment

    def backtrack(self, assignment):

        if len(assignment) == len(self.variables):
            return assignment
            
        var = self.select_unassigned_variable(assignment)

        for value in self.domains[var]:
            if not self.is_consistent(var, value, assignment):
                continue

            # Check if it's a lecture
            if "lecture" in var:
                # Assign the same slot and teacher to all groups (1 to 6)
                slot, teacher_id, _ = value
                group_values = [((slot[0], slot[1]), teacher_id, group_id) for group_id in range(1, 7)]
                
                # Check that all these values are consistent before assigning
                if all(self.is_consistent(var, gv, assignment) for gv in group_values):
                    assignment[var] = group_values
                    result = self.backtrack(assignment)
                    if result is not None:
                        return result
                    del assignment[var]
            else:
                # For TD and TP, just assign one value
                assignment[var] = [value]
                result = self.backtrack(assignment)
                if result is not None:
                    return result
                del assignment[var]


if __name__ == "__main__":
    print("Initializing timetable CSP for 6 groups...")
    csp = MultiGroupTimeTableCSP(num_groups=6)
    # print(f"Created {len(csp.variables)} variables.")
    # print(f"Created {len(csp.constraints)} constraints.")
    # print("\nSolving CSP with backtracking search (this may take a while)...")
    # solution = csp.backtracking_search()
    # csp.print_solution(solution)

    solution = csp.backtracking_search()
    
    lectures = {var: solution[var] for var in solution if "_lecture" in var[0]}

    print(serialize_schedule(lectures))

    # print(csp.variables)
    


