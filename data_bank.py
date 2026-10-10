"""
All data lives here: subjects, questions, resources, tutor notes, demo profiles.
"""

import re


# ---------------- subjects and prerequisites ----------------

SUBJECTS = {
    "Python": [
        "Python: Variables & Types",
        "Python: Conditionals",
        "Python: Loops",
    ],
    "Java": [
        "Java: Variables & Types",
        "Java: Classes & Objects",
        "Java: Inheritance",
    ],
    "C": [
        "C: Arrays",
        "C: Pointers",
        "C: Functions",
    ],
    "SQL": [
        "SQL: SELECT & WHERE",
        "SQL: JOINs",
        "SQL: GROUP BY",
    ],
    "DSA": [
        "DSA: Arrays",
        "DSA: Linked Lists",
        "DSA: Sorting & Complexity",
    ],
    "Web Development": [
        "Web: HTML",
        "Web: CSS",
        "Web: JavaScript",
    ],
    "AI & Machine Learning": [
        "AI: Types of Learning",
        "AI: Model Evaluation",
        "AI: Overfitting",
    ],
}

TOPIC_SUBJECT = {
    topic: subject
    for subject, topics in SUBJECTS.items()
    for topic in topics
}

# topic -> topics that must be understood first
PREREQS = {
    "Python: Conditionals": ["Python: Variables & Types"],
    "Python: Loops": ["Python: Conditionals", "Python: Variables & Types"],
    "Java: Classes & Objects": ["Java: Variables & Types"],
    "Java: Inheritance": ["Java: Classes & Objects"],
    "C: Pointers": ["C: Arrays"],
    "C: Functions": ["C: Pointers"],
    "SQL: JOINs": ["SQL: SELECT & WHERE"],
    "SQL: GROUP BY": ["SQL: SELECT & WHERE"],
    "DSA: Linked Lists": ["DSA: Arrays"],
    "DSA: Sorting & Complexity": ["DSA: Arrays"],
    "Web: CSS": ["Web: HTML"],
    "Web: JavaScript": ["Web: HTML"],
    "AI: Model Evaluation": ["AI: Types of Learning"],
    "AI: Overfitting": ["AI: Model Evaluation"],
}


# ---------------- question bank ----------------

QUESTIONS = []


def Q(topic, difficulty, question_text, options, answer_index, misconceptions):
    QUESTIONS.append({
        "id": f"q{len(QUESTIONS) + 1}",
        "topic": topic,
        "subject": TOPIC_SUBJECT[topic],
        "difficulty": difficulty,
        "q": question_text,
        "options": options,
        "answer": answer_index,
        "mis": misconceptions,
    })


T = "Python: Variables & Types"
Q(
    T,
    "easy",
    "What is the type of x after `x = 5 / 2` in Python 3?",
    ["int", "float", "str", "double"],
    1,
    {
        0: "Believes division always returns an integer",
        3: "Confuses Python with languages that have double",
    },
)

Q(
    T,
    "easy",
    "Which is a valid variable name in Python?",
    ["2value", "my-var", "_count", "class"],
    2,
    {
        0: "Thinks names can start with a digit",
        1: "Confuses hyphen with underscore",
        3: "Does not know reserved keywords",
    },
)

T = "Python: Conditionals"
Q(
    T,
    "easy",
    "What happens with `if x = 3:` in Python?",
    ["Compares x to 3", "Assigns 3 to x, then runs", "SyntaxError", "Always False"],
    2,
    {
        0: "Confuses = with ==",
        1: "Confuses = with ==",
    },
)

Q(
    T,
    "easy",
    "Which keyword adds a second condition after `if`?",
    ["else if", "elif", "elseif", "otherwise"],
    1,
    {
        0: "Mixes syntax from other languages",
        2: "Mixes syntax from other languages",
    },
)

T = "Python: Loops"
Q(
    T,
    "easy",
    "How many times does `for i in range(3):` run?",
    ["2", "3", "4", "Infinite"],
    1,
    {
        0: "Off-by-one with range",
        2: "Off-by-one with range",
    },
)

Q(
    T,
    "medium",
    "What does `break` do inside a loop?",
    ["Skips this iteration", "Exits the loop", "Restarts the loop", "Ends the program"],
    1,
    {
        0: "Confuses break with continue",
        3: "Thinks break ends the whole program",
    },
)

T = "Java: Variables & Types"
Q(
    T,
    "easy",
    "Which line declares an integer in Java?",
    ["int x = 5;", "x = 5;", "var x := 5;", "integer x = 5;"],
    0,
    {
        1: "Forgets Java needs declared types",
        3: "Mixes syntax from other languages",
    },
)

Q(
    T,
    "easy",
    "What is `7 / 2` in Java when both are int?",
    ["3.5", "3", "4", "3.0"],
    1,
    {
        0: "Believes integer division gives decimals",
        2: "Thinks division rounds up",
    },
)

T = "Java: Classes & Objects"
Q(
    T,
    "easy",
    "Which keyword creates an object in Java?",
    ["make", "new", "create", "object"],
    1,
    {
        0: "Mixes syntax from other languages",
        2: "Mixes syntax from other languages",
        3: "Mixes syntax from other languages",
    },
)

Q(
    T,
    "medium",
    "What is a constructor?",
    [
        "A method that runs when an object is created",
        "A method that deletes an object",
        "A variable type",
        "A kind of loop",
    ],
    0,
    {
        1: "Confuses constructor with destructor",
        2: "Confuses methods with variables",
    },
)

T = "Java: Inheritance"
Q(
    T,
    "easy",
    "Which keyword makes a class inherit from another?",
    ["implements", "extends", "inherits", "super"],
    1,
    {
        0: "Confuses extends with implements",
        3: "Confuses super with extends",
    },
)

Q(
    T,
    "medium",
    "What does `super()` call?",
    [
        "The parent class constructor",
        "The child class constructor",
        "The main method",
        "A static block",
    ],
    0,
    {
        1: "Confuses parent and child class",
    },
)

T = "C: Arrays"
Q(
    T,
    "easy",
    "What is the index of the first element of a C array?",
    ["1", "0", "-1", "It depends"],
    1,
    {
        0: "Believes indexing starts at 1",
    },
)

Q(
    T,
    "easy",
    "Given `int a[5];` which access is out of bounds?",
    ["a[0]", "a[4]", "a[5]", "a[2]"],
    2,
    {
        1: "Off-by-one with array length",
    },
)

T = "C: Pointers"
Q(
    T,
    "medium",
    "What does `&x` give?",
    ["The value of x", "The address of x", "The size of x", "A pointer to a pointer"],
    1,
    {
        0: "Confuses address-of with value",
    },
)

Q(
    T,
    "medium",
    "If `int *p = &x;` what is `*p`?",
    ["The address of x", "The value stored in x", "The address of p", "Garbage"],
    1,
    {
        0: "Confuses dereference with address-of",
    },
)

T = "C: Functions"
Q(
    T,
    "easy",
    "What does a `void` function return?",
    ["0", "Nothing", "NULL", "-1"],
    1,
    {
        0: "Confuses void with zero",
    },
)

Q(
    T,
    "medium",
    "Are C arguments passed by value by default?",
    ["Yes, a copy is passed", "No, by reference", "Only arrays", "Only pointers"],
    0,
    {
        1: "Believes C passes by reference",
    },
)

T = "SQL: SELECT & WHERE"
Q(
    T,
    "easy",
    "Which clause filters rows?",
    ["ORDER BY", "WHERE", "GROUP BY", "LIMIT"],
    1,
    {
        0: "Confuses SQL clauses",
        2: "Confuses SQL clauses",
    },
)

Q(
    T,
    "easy",
    "Which query returns all columns from `users`?",
    ["SELECT * FROM users", "SELECT ALL users", "GET * FROM users", "SHOW users"],
    0,
    {
        2: "Mixes syntax from other languages",
    },
)

T = "SQL: JOINs"
Q(
    T,
    "medium",
    "Which join returns only rows that match in both tables?",
    ["INNER JOIN", "LEFT JOIN", "FULL JOIN", "CROSS JOIN"],
    0,
    {
        1: "Confuses INNER and LEFT join",
        2: "Confuses INNER and FULL join",
    },
)

Q(
    T,
    "medium",
    "LEFT JOIN keeps...",
    ["Only matching rows", "All rows of the left table", "All rows of the right table", "No rows"],
    1,
    {
        0: "Confuses LEFT with INNER join",
        2: "Confuses left and right",
    },
)

T = "SQL: GROUP BY"
Q(
    T,
    "easy",
    "Which function counts rows?",
    ["SUM", "COUNT", "TOTAL", "ADD"],
    1,
    {
        0: "Confuses SUM with COUNT",
    },
)

Q(
    T,
    "medium",
    "Which clause filters groups after GROUP BY?",
    ["WHERE", "HAVING", "FILTER", "ORDER BY"],
    1,
    {
        0: "Uses WHERE on aggregated values",
    },
)

T = "DSA: Arrays"
Q(
    T,
    "easy",
    "Time to access an array element by index?",
    ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
    0,
    {
        1: "Thinks array access needs scanning",
    },
)

Q(
    T,
    "medium",
    "Cost of inserting at the start of an array of n elements?",
    ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
    1,
    {
        0: "Ignores element shifting",
    },
)

T = "DSA: Linked Lists"
Q(
    T,
    "easy",
    "What does a singly linked list node store?",
    ["Data and a next pointer", "Data only", "Data and an index", "Two data values"],
    0,
    {
        2: "Confuses linked list with array",
    },
)

Q(
    T,
    "medium",
    "Time to reach the k-th element of a linked list?",
    ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
    1,
    {
        0: "Believes linked lists have random access",
    },
)

T = "DSA: Sorting & Complexity"
Q(
    T,
    "medium",
    "Worst-case time of bubble sort?",
    ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
    2,
    {
        1: "Confuses bubble sort with merge sort",
    },
)

Q(
    T,
    "medium",
    "Which sort is O(n log n) on average?",
    ["Bubble sort", "Merge sort", "Insertion sort", "Selection sort"],
    1,
    {
        0: "Believes simple sorts are fast",
    },
)

T = "Web: HTML"
Q(
    T,
    "easy",
    "Which tag creates a hyperlink?",
    ["`<link>`", "`<a>`", "`<href>`", "`<url>`"],
    1,
    {
        0: "Confuses <link> with the anchor tag",
        2: "Confuses an attribute with a tag",
    },
)

Q(
    T,
    "easy",
    "Which tag is the largest heading?",
    ["`<h6>`", "`<h1>`", "`<head>`", "`<header>`"],
    1,
    {
        0: "Reverses heading levels",
        2: "Confuses head with heading",
    },
)

T = "Web: CSS"
Q(
    T,
    "easy",
    "Which property changes text color?",
    ["font-color", "color", "text-color", "foreground"],
    1,
    {
        0: "Guesses property names",
        2: "Guesses property names",
    },
)

Q(
    T,
    "easy",
    "Which selector targets the element with id 'box'?",
    [".box", "#box", "box", "*box"],
    1,
    {
        0: "Confuses class and id selectors",
    },
)

T = "Web: JavaScript"
Q(
    T,
    "easy",
    "Which keyword declares a block-scoped variable?",
    ["var", "let", "int", "dim"],
    1,
    {
        0: "Confuses var and let scope",
        2: "Mixes syntax from other languages",
    },
)

Q(
    T,
    "medium",
    "What does `===` check?",
    ["Value only", "Value and type", "Type only", "Assignment"],
    1,
    {
        0: "Confuses == with ===",
        3: "Confuses = with ==",
    },
)

T = "AI: Types of Learning"
Q(
    T,
    "easy",
    "Which type of learning uses labeled data?",
    ["Supervised", "Unsupervised", "Reinforcement", "Self-organizing"],
    0,
    {
        1: "Confuses supervised with unsupervised learning",
        2: "Confuses supervised with reinforcement learning",
    },
)

Q(
    T,
    "easy",
    "Grouping customers into segments without labels is...",
    ["Classification", "Clustering", "Regression", "Reinforcement learning"],
    1,
    {
        0: "Confuses clustering with classification",
        2: "Confuses clustering with regression",
    },
)

Q(
    T,
    "easy",
    "Predicting a house price is which task?",
    ["Classification", "Clustering", "Regression", "Segmentation"],
    2,
    {
        0: "Confuses regression with classification",
    },
)

T = "AI: Model Evaluation"
Q(
    T,
    "easy",
    "Why split data into training and test sets?",
    [
        "To measure performance on unseen data",
        "To make training faster",
        "To remove outliers",
        "To raise accuracy automatically",
    ],
    0,
    {
        1: "Thinks splitting is for speed",
        3: "Believes splitting boosts accuracy",
    },
)

Q(
    T,
    "medium",
    "Which metric is better than accuracy for imbalanced classes?",
    ["F1 score", "Batch size", "Learning rate", "Epoch count"],
    0,
    {
        1: "Confuses hyperparameters with metrics",
        2: "Confuses hyperparameters with metrics",
        3: "Confuses hyperparameters with metrics",
    },
)

Q(
    T,
    "medium",
    "What does recall measure?",
    [
        "Share of actual positives that were found",
        "Share of predictions that were correct",
        "Share of negatives found",
        "Training speed",
    ],
    0,
    {
        1: "Confuses recall with precision",
        2: "Confuses recall with specificity",
    },
)

T = "AI: Overfitting"
Q(
    T,
    "medium",
    "99% training accuracy but 70% test accuracy suggests...",
    ["Underfitting", "Overfitting", "Good generalisation", "A faster model"],
    1,
    {
        0: "Confuses overfitting with underfitting",
        2: "Ignores the gap between train and test",
    },
)

Q(
    T,
    "medium",
    "Which helps reduce overfitting?",
    [
        "Adding regularisation",
        "Training much longer",
        "Using fewer training examples",
        "Removing the test set",
    ],
    0,
    {
        1: "Thinks more training always helps",
        2: "Thinks less data helps",
        3: "Hides the problem instead of fixing it",
    },
)

Q(
    T,
    "medium",
    "Underfitting means the model...",
    [
        "Is too simple to capture the pattern",
        "Memorises the training data",
        "Has too many parameters",
        "Is perfect on test data",
    ],
    0,
    {
        1: "Confuses underfitting with overfitting",
        2: "Confuses underfitting with overfitting",
    },
)


# ---------------- study resources ----------------

def _slug(topic):
    return re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")


def _search_query(topic):
    return topic.replace("&", "and").replace(":", "").replace(" ", "+")


RESOURCES = []

for topic in TOPIC_SUBJECT:
    search_term = _search_query(topic)

    resource_specs = [
        (
            "video",
            "beginner",
            25,
            "Intro video",
            f"https://www.youtube.com/results?search_query={search_term}+tutorial+for+beginners",
        ),
        (
            "notes",
            "beginner",
            20,
            "Beginner notes",
            f"https://www.google.com/search?q={search_term}+tutorial+notes",
        ),
        (
            "practice",
            "intermediate",
            40,
            "Practice problems",
            f"https://www.google.com/search?q={search_term}+practice+problems",
        ),
        (
            "practice",
            "advanced",
            50,
            "Challenge set",
            f"https://www.google.com/search?q={search_term}+interview+questions",
        ),
    ]

    for index, (resource_type, difficulty, minutes, label, url) in enumerate(
        resource_specs, start=1
    ):
        RESOURCES.append({
            "id": f"{_slug(topic)}-{index}",
            "title": f"{topic}: {label}",
            "topic": topic,
            "difficulty": difficulty,
            "type": resource_type,
            "minutes": minutes,
            "url": url,
        })


# ---------------- trusted notes for the RAG tutor ----------------

NOTES = {
    "Python: Variables & Types": (
        "A variable is a name that refers to a value. Python infers types: int for whole "
        "numbers, float for decimals (the / operator always returns a float), str for text. "
        "Names cannot start with a digit or be keywords like class."
    ),
    "Python: Conditionals": (
        "if checks a condition, elif adds more conditions, else is the fallback. Use == to "
        "compare and = to assign. Indentation decides which code belongs to each branch."
    ),
    "Python: Loops": (
        "A for loop repeats over a sequence. range(n) produces 0 to n-1, so it runs n times. "
        "A while loop repeats while its condition is true. break exits the loop and continue "
        "skips to the next iteration."
    ),
    "Java: Variables & Types": (
        "Java is statically typed, so you declare the type, for example int x = 5. Dividing "
        "two ints gives an int, so 7 / 2 is 3. Use double for decimals."
    ),
    "Java: Classes & Objects": (
        "A class is a blueprint and an object is an instance created with the new keyword. "
        "A constructor runs when an object is created and sets its initial state."
    ),
    "Java: Inheritance": (
        "A subclass inherits fields and methods from a parent class using extends. super() "
        "calls the parent constructor. A class can implement interfaces with implements."
    ),
    "C: Arrays": (
        "C arrays are zero-indexed: an array of size 5 has valid indexes 0 to 4. C does not "
        "check bounds, so reading a[5] is undefined behavior."
    ),
    "C: Pointers": (
        "A pointer stores a memory address. &x gives the address of x and *p dereferences a "
        "pointer to read or write the value at that address."
    ),
    "C: Functions": (
        "C passes arguments by value, so a function receives a copy. To change the caller's "
        "variable, pass a pointer. A void function returns no value."
    ),
    "SQL: SELECT & WHERE": (
        "SELECT chooses columns and FROM chooses the table. WHERE filters rows before any "
        "grouping. SELECT * returns every column."
    ),
    "SQL: JOINs": (
        "INNER JOIN keeps only rows that match in both tables. LEFT JOIN keeps every row from "
        "the left table and fills missing matches with NULL."
    ),
    "SQL: GROUP BY": (
        "GROUP BY collapses rows into groups so aggregate functions like COUNT, SUM and AVG "
        "work per group. WHERE filters rows before grouping and HAVING filters groups after "
        "grouping."
    ),
    "DSA: Arrays": (
        "Arrays give O(1) access by index, but inserting or deleting in the middle costs O(n) "
        "because elements must shift."
    ),
    "DSA: Linked Lists": (
        "A singly linked list stores data and a next pointer in each node. Inserting at the "
        "head is O(1) but reaching the k-th element takes O(n) because there is no random access."
    ),
    "DSA: Sorting & Complexity": (
        "Bubble, insertion and selection sort are O(n^2) in the worst case. Merge sort and "
        "heap sort are O(n log n). Big-O describes how running time grows with input size."
    ),
    "Web: HTML": (
        "HTML structures a page with tags. The a tag with href makes a link, h1 is the largest "
        "heading and h6 the smallest, p is a paragraph."
    ),
    "Web: CSS": (
        "CSS styles HTML. The color property sets text color and background-color sets the "
        "background. Select classes with .name and ids with #name."
    ),
    "AI: Types of Learning": (
        "Supervised learning trains on labeled data, for example classification (categories) "
        "and regression (numbers such as a house price). Unsupervised learning finds structure "
        "without labels, for example clustering. Reinforcement learning learns from rewards."
    ),
    "AI: Model Evaluation": (
        "Split data into training and test sets so you can measure performance on unseen data. "
        "Accuracy can mislead on imbalanced classes, so use precision, recall or F1 score. "
        "Recall is the share of actual positives the model found."
    ),
    "AI: Overfitting": (
        "Overfitting means a model memorises training data: high training accuracy but low test "
        "accuracy. Regularisation, more data and simpler models reduce it. Underfitting is the "
        "opposite: the model is too simple to capture the pattern."
    ),
    "Web: JavaScript": (
        "Use let and const for block-scoped variables, while var is function-scoped. === "
        "compares value and type, whereas == converts types first."
    ),
}


# ---------------- demo profiles ----------------

DEMO1 = {
    "Python: Variables & Types": [True, True],
    "Python: Conditionals": [False, True],
    "Python: Loops": [False, False],
    "SQL: SELECT & WHERE": [True, True],
    "SQL: JOINs": [False, False],
    "SQL: GROUP BY": [False, True],
    "DSA: Arrays": [True, True],
    "DSA: Linked Lists": [False, True],
}

DEMO_IMPROVED = {
    "Python: Conditionals": [True, True],
    "Python: Loops": [True, True],
    "SQL: JOINs": [True, False],
    "SQL: GROUP BY": [True, True],
    "DSA: Linked Lists": [True, True],
}

DEMO_STUCK = {
    "Python: Loops": [False, False],
    "SQL: JOINs": [True, False],
}


# ---------------- answer conversion ----------------

def make_answers(profile, strict=False):
    """
    Convert a demo profile into answer records.

    profile format:
        {
            topic: [True, False, ...]
        }

    If strict=True, the number of flags must exactly match the number of
    questions available for that topic.
    """
    answers = []

    for topic, flags in profile.items():
        topic_questions = [
            question
            for question in QUESTIONS
            if question["topic"] == topic
        ]