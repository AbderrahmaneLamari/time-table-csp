from constraint import Problem, AllDifferentConstraint

# Define the courses and their components
courses = {
    "Sécurité": ["lecture", "td"],
    "Méthodes_formelles": ["lecture", "td"],
    "Analyse_numerique": ["lecture", "td"],
    "Entrepreneuriat": ["lecture"],
    "Recherche_operationnelle": ["lecture", "td"],
    "Distributed_Architecture": ["lecture", "td"],
    "Reseaux_2": ["lecture", "td", "tp"],
    "Artificial_Intelligence": ["lecture", "td", "tp"]
}

# Teachers for each course component
teachers = {
    "Sécurité_lecture": "teacher 1",
    "Sécurité_td": "teacher 1",
    "Méthodes_formelles_lecture": "teacher 2",
    "Méthodes_formelles_td": "teacher 2",
    "Analyse_numerique_lecture": "teacher 3",
    "Analyse_numerique_td": "teacher 3",
    "Entrepreneuriat_lecture": "teacher 4",
    "Recherche_operationnelle_lecture": "teacher 5",
    "Recherche_operationnelle_td": "teacher 5",
    "Distributed_Architecture_lecture": "teacher 6",
    "Distributed_Architecture_td": "teacher 6",
    "Reseaux_lecture": "teacher 7",
    "Reseaux_td": "teacher 7",
    "Reseaux_tp": ["teacher 8", "teacher 9", "teacher 10"],
    "Artificial_Intelligence_lecture": "teacher 11",
    "Artificial_Intelligence_td": "teacher 11",
    "Artificial_Intelligence_tp": ["teacher 12", "teacher 13", "teacher 14"]
}

# Time slots as a list of tuples (day, period)
SLOTS = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
         (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
         (3, 1), (3, 2), (3, 3),
         (4, 1), (4, 2), (4, 3), (4, 4), (4, 5),
         (5, 1), (5, 2), (5, 3), (5, 4), (5, 5)]

# Create the problem instance
problem = Problem()

# Define the variables: Each course component (e.g., "Sécurité_lecture", "Sécurité_td", etc.)
variables = []
for course, components in courses.items():
    for component in components:
        var = f"{course}_{component}"
        variables.append(var)
        problem.addVariable(var, SLOTS)  # All variables can take any time slot


lectures = [var for var in variables if "_lecture" in var]
print(lectures)

problem.addConstraint(AllDifferentConstraint, lectures)

