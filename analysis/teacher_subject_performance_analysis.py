import pandas as pd
from pathlib import Path


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"

OUTPUT_DIR = (
    DATA_DIR
    / "analysis"
    / "teacher"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. PERFORMANCE SETTINGS
# ============================================================

ASSIGNMENT_MAX_MARKS = 20
TEST_MAX_MARKS = 20

ATTENDANCE_WEIGHT = 0.30
ASSIGNMENT_WEIGHT = 0.30
TEST_WEIGHT = 0.40


# ============================================================
# 3. FILE HELPER
# ============================================================

def find_cleaned_file(folder, base_name):
    """
    Find cleaned dataset.

    Standard cleaning output:
        students_cleaned.csv

    Fallback:
        students.csv
    """

    possible_names = [
        f"{base_name}_cleaned.csv",
        f"{base_name}.csv"
    ]

    for name in possible_names:

        path = folder / name

        if path.exists():
            return path

    return None


def load_cleaned_csv(
    folder,
    base_name,
    required=True
):
    """
    Load cleaned CSV file.
    """

    path = find_cleaned_file(
        folder,
        base_name
    )

    if path is None:

        if required:

            raise FileNotFoundError(
                f"\nRequired cleaned file not found.\n"
                f"Folder: {folder}\n"
                f"Expected: {base_name}_cleaned.csv"
            )

        return pd.DataFrame()

    return pd.read_csv(path)


def load_raw_csv(
    base_name,
    required=True
):
    """
    Load master/raw CSV file.
    """

    path = RAW_DIR / base_name

    if not path.exists():

        if required:

            raise FileNotFoundError(
                f"\nRequired raw/master file not found:\n{path}"
            )

        return pd.DataFrame()

    return pd.read_csv(path)


# ============================================================
# 4. LOAD DATA
# ============================================================

print("\n======================================")
print(" LOADING TEACHER ANALYSIS DATA")
print("======================================\n")


# ------------------------------------------------------------
# Current cleaned academic data
# ------------------------------------------------------------

students = load_cleaned_csv(
    CLEANED_DIR,
    "students"
)

student_subject = load_cleaned_csv(
    CLEANED_DIR,
    "student_subject"
)

subjects = load_cleaned_csv(
    CLEANED_DIR,
    "subjects"
)

attendance = load_cleaned_csv(
    CLEANED_DIR,
    "attendance"
)

practical_attendance = load_cleaned_csv(
    CLEANED_DIR,
    "practical_attendance",
    required=False
)

assignments = load_cleaned_csv(
    CLEANED_DIR,
    "assignments"
)

tests = load_cleaned_csv(
    CLEANED_DIR,
    "tests"
)


# ------------------------------------------------------------
# Master files exported by auto_pipeline
# ------------------------------------------------------------

teacher_master = load_raw_csv(
    "teacher_master.csv"
)

teacher_subject_path = RAW_DIR / "current" / "teacher_subject.csv"
if not teacher_subject_path.exists():
    teacher_subject_path = RAW_DIR / "teacher_subject.csv"

teacher_subject = pd.read_csv(teacher_subject_path)

programs = load_raw_csv(
    "programs.csv"
)

semesters = load_raw_csv(
    "semesters.csv"
)


# ============================================================
# 5. BASIC VALIDATION
# ============================================================

required_student_columns = [
    "Student_ID",
    "Program_ID",
    "Semester_ID"
]

for column in required_student_columns:

    if column not in students.columns:

        raise ValueError(
            f"students data is missing column: {column}"
        )


required_subject_columns = [
    "Subject_ID",
    "Program_ID",
    "Semester_ID"
]

for column in required_subject_columns:

    if column not in subjects.columns:

        raise ValueError(
            f"subjects data is missing column: {column}"
        )


print("Students:", len(students))
print("Student-Subject records:", len(student_subject))
print("Subjects:", len(subjects))
print("Attendance records:", len(attendance))
print(
    "Practical Attendance records:",
    len(practical_attendance)
)
print("Assignment records:", len(assignments))
print("Test records:", len(tests))
print("Teacher master records:", len(teacher_master))
print(
    "Teacher-subject allocations:",
    len(teacher_subject)
)


# ============================================================
# 6. CURRENT STUDENTS
# ============================================================

# students_cleaned.csv represents current students.

current_student_ids = set(
    students["Student_ID"]
    .dropna()
    .astype(int)
)


# ------------------------------------------------------------
# Current Program + Semester combinations
# ------------------------------------------------------------

current_student_structure = (
    students[
        [
            "Student_ID",
            "Program_ID",
            "Semester_ID"
        ]
    ]
    .drop_duplicates()
    .copy()
)


current_semester_pairs = set(
    zip(
        current_student_structure["Program_ID"],
        current_student_structure["Semester_ID"]
    )
)


print(
    "\nCurrent students:",
    len(current_student_ids)
)

print(
    "Current Program/Semester combinations:",
    len(current_semester_pairs)
)


# ============================================================
# 7. CURRENT STUDENT-SUBJECT ENROLLMENT
# ============================================================

student_subject = student_subject[
    student_subject["Student_ID"]
    .isin(current_student_ids)
].copy()


# ------------------------------------------------------------
# Keep only student's actual semester
# ------------------------------------------------------------

student_subject = student_subject.merge(
    students[
        [
            "Student_ID",
            "Program_ID",
            "Semester_ID"
        ]
    ].drop_duplicates(),
    on="Student_ID",
    how="inner",
    suffixes=(
        "",
        "_Student"
    )
)


# ------------------------------------------------------------
# Validate enrollment semester
# ------------------------------------------------------------

student_subject = student_subject[
    (
        student_subject["Semester_ID"]
        ==
        student_subject["Semester_ID_Student"]
    )
].copy()


student_subject.drop(
    columns=["Semester_ID_Student"],
    inplace=True
)


# ------------------------------------------------------------
# Validate program through subject
# ------------------------------------------------------------

student_subject = student_subject.merge(
    subjects[
        [
            "Subject_ID",
            "Semester_ID",
            "Program_ID"
        ]
    ].drop_duplicates(),
    on=[
        "Subject_ID",
        "Semester_ID"
    ],
    how="inner",
    suffixes=(
        "",
        "_Subject"
    )
)


student_subject = student_subject[
    (
        student_subject["Program_ID"]
        ==
        student_subject["Program_ID_Subject"]
    )
].copy()


student_subject.drop(
    columns=["Program_ID_Subject"],
    inplace=True
)


print(
    "Valid current student-subject records:",
    len(student_subject)
)


# ============================================================
# 8. PROGRAM INFORMATION
# ============================================================

program_map = programs[
    [
        "Program_ID",
        "Program_Name"
    ]
].drop_duplicates()


# ============================================================
# 9. SEMESTER INFORMATION
# ============================================================

semester_columns = [
    "Semester_ID",
    "Semester_Name",
    "Program_ID"
]

if "Semester_Number" in semesters.columns:

    semester_columns.append(
        "Semester_Number"
    )


semester_map = (
    semesters[
        semester_columns
    ]
    .drop_duplicates()
    .copy()
)


# ------------------------------------------------------------
# Derive Semester_Number if not exported
# ------------------------------------------------------------

if "Semester_Number" not in semester_map.columns:

    semester_map["Semester_Number"] = (
        semester_map["Semester_Name"]
        .astype(str)
        .str.extract(
            r"(\d+)",
            expand=False
        )
    )

    semester_map["Semester_Number"] = (
        pd.to_numeric(
            semester_map["Semester_Number"],
            errors="coerce"
        )
    )


# ============================================================
# 10. PREPARE TEACHER ALLOCATION
# ============================================================

teacher_allocation = teacher_subject.copy()


# ------------------------------------------------------------
# Teacher information
# ------------------------------------------------------------

teacher_allocation = teacher_allocation.merge(
    teacher_master[
        [
            "Teacher_ID",
            "Teacher_Name"
        ]
    ].drop_duplicates(),
    on="Teacher_ID",
    how="left"
)


# ============================================================
# 11. DERIVE PROGRAM FROM SUBJECT
# ============================================================

# teacher_subject does not necessarily contain Program_ID.
#
# Program is derived from:
#
# Subject_ID + Semester_ID
#          ↓
# Subject master
#          ↓
# Program_ID
#

subject_program_map = subjects[
    ["Subject_ID", "Semester_ID", "Program_ID"]
].drop_duplicates()

if "Program_ID" not in teacher_allocation.columns:
    teacher_allocation = teacher_allocation.merge(
        subject_program_map,
        on=["Subject_ID", "Semester_ID"],
        how="left"
    )
else:
    teacher_allocation["Program_ID"] = pd.to_numeric(
        teacher_allocation["Program_ID"], errors="coerce"
    )

# Program name
teacher_allocation = teacher_allocation.merge(
    program_map,
    on="Program_ID",
    how="left"
)


# ------------------------------------------------------------
# Semester information
# ------------------------------------------------------------

teacher_allocation = teacher_allocation.merge(
    semester_map[
        [
            "Semester_ID",
            "Semester_Name",
            "Program_ID",
            "Semester_Number"
        ]
    ],
    on=[
        "Semester_ID",
        "Program_ID"
    ],
    how="left"
)


# ============================================================
# 12. KEEP ONLY CURRENT ALLOCATIONS
# ============================================================

teacher_allocation["Current_Key"] = list(
    zip(
        teacher_allocation["Program_ID"],
        teacher_allocation["Semester_ID"]
    )
)


teacher_allocation = teacher_allocation[
    teacher_allocation["Current_Key"]
    .isin(current_semester_pairs)
].copy()


teacher_allocation.drop(
    columns=["Current_Key"],
    inplace=True
)


print(
    "Current teacher allocations:",
    len(teacher_allocation)
)


# ============================================================
# 13. SUBJECT INFORMATION
# ============================================================

subject_info_columns = [
    "Subject_ID",
    "Subject_Name",
    "Subject_Code",
    "Subject_Type",
    "Program_ID",
    "Semester_ID"
]


subject_info = (
    subjects[
        subject_info_columns
    ]
    .drop_duplicates()
    .copy()
)


teacher_allocation = teacher_allocation.merge(
    subject_info,
    on=[
        "Subject_ID",
        "Program_ID",
        "Semester_ID"
    ],
    how="left"
)


print(
    "Teacher-subject mappings after subject match:",
    len(teacher_allocation)
)


# ============================================================
# 14. ATTENDANCE PREPARATION
# ============================================================

def prepare_attendance_dataframe(
    df
):
    """
    Standardize attendance dataframe.
    """

    if df.empty:

        return pd.DataFrame(
            columns=[
                "Student_ID",
                "Subject_ID",
                "Semester_ID",
                "Attendance_Status"
            ]
        )

    df = df.copy()

    if "Attendance_Status" not in df.columns:

        if "Status" in df.columns:

            df["Attendance_Status"] = (
                df["Status"]
            )

        else:

            raise ValueError(
                "Attendance_Status/Status column "
                "not found in attendance data."
            )

    required_columns = [
        "Student_ID",
        "Subject_ID",
        "Semester_ID",
        "Attendance_Status"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Attendance data missing columns: {missing}"
        )

    df["Attendance_Status"] = (
        df["Attendance_Status"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df = df[
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID",
            "Attendance_Status"
        ]
    ].copy()

    return df


# ------------------------------------------------------------
# Regular attendance
# ------------------------------------------------------------

attendance = prepare_attendance_dataframe(
    attendance
)


attendance = attendance[
    attendance["Student_ID"]
    .isin(current_student_ids)
].copy()


# ------------------------------------------------------------
# Validate current semester/program using student structure
# ------------------------------------------------------------

attendance = attendance.merge(
    students[
        [
            "Student_ID",
            "Program_ID",
            "Semester_ID"
        ]
    ].drop_duplicates(),
    on="Student_ID",
    how="inner",
    suffixes=(
        "",
        "_Student"
    )
)


attendance = attendance[
    attendance["Semester_ID"]
    ==
    attendance["Semester_ID_Student"]
].copy()


attendance.drop(
    columns=["Semester_ID_Student"],
    inplace=True
)


# ------------------------------------------------------------
# Practical attendance
# ------------------------------------------------------------

practical_attendance = (
    prepare_attendance_dataframe(
        practical_attendance
    )
)


if not practical_attendance.empty:

    practical_attendance = practical_attendance[
        practical_attendance["Student_ID"]
        .isin(current_student_ids)
    ].copy()

    practical_attendance = practical_attendance.merge(
        students[
            [
                "Student_ID",
                "Semester_ID"
            ]
        ].drop_duplicates(),
        on="Student_ID",
        how="inner",
        suffixes=(
            "",
            "_Student"
        )
    )

    practical_attendance = practical_attendance[
        practical_attendance["Semester_ID"]
        ==
        practical_attendance["Semester_ID_Student"]
    ].copy()

    practical_attendance.drop(
        columns=["Semester_ID_Student"],
        inplace=True
    )


# ------------------------------------------------------------
# Combine regular + practical attendance
# ------------------------------------------------------------

attendance_parts = [
    attendance
]

if not practical_attendance.empty:

    attendance_parts.append(
        practical_attendance
    )


attendance_all = pd.concat(
    attendance_parts,
    ignore_index=True
)


# ============================================================
# 15. ATTENDANCE PERFORMANCE
# ============================================================

attendance_all["Present"] = (
    attendance_all["Attendance_Status"]
    .eq("present")
    .astype(int)
)


attendance_summary = (
    attendance_all
    .groupby(
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ],
        as_index=False
    )
    .agg(
        Total_Attendance=(
            "Attendance_Status",
            "count"
        ),

        Present_Attendance=(
            "Present",
            "sum"
        )
    )
)


attendance_summary["Attendance_Percentage"] = (
    attendance_summary["Present_Attendance"]
    /
    attendance_summary["Total_Attendance"]
    * 100
)


print(
    "Attendance student-subject summaries:",
    len(attendance_summary)
)


# ============================================================
# 16. ASSIGNMENT PERFORMANCE
# ============================================================

assignments = assignments[
    assignments["Student_ID"]
    .isin(current_student_ids)
].copy()


# ------------------------------------------------------------
# Match student's current semester
# ------------------------------------------------------------

assignments = assignments.merge(
    students[
        [
            "Student_ID",
            "Program_ID",
            "Semester_ID"
        ]
    ].drop_duplicates(),
    on="Student_ID",
    how="inner",
    suffixes=(
        "",
        "_Student"
    )
)


assignments = assignments[
    assignments["Semester_ID"]
    ==
    assignments["Semester_ID_Student"]
].copy()


assignments.drop(
    columns=["Semester_ID_Student"],
    inplace=True
)


# ------------------------------------------------------------
# Marks
# ------------------------------------------------------------

assignments["Marks"] = pd.to_numeric(
    assignments["Marks"],
    errors="coerce"
)


assignments["Marks"] = (
    assignments["Marks"]
    .clip(
        lower=0,
        upper=ASSIGNMENT_MAX_MARKS
    )
)


assignments["Assignment_Percentage"] = (
    assignments["Marks"]
    /
    ASSIGNMENT_MAX_MARKS
    * 100
)


assignment_summary = (
    assignments
    .groupby(
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ],
        as_index=False
    )
    .agg(
        Assignment_Percentage=(
            "Assignment_Percentage",
            "mean"
        )
    )
)


print(
    "Assignment student-subject summaries:",
    len(assignment_summary)
)


# ============================================================
# 17. TEST PERFORMANCE
# ============================================================

tests = tests[
    tests["Student_ID"]
    .isin(current_student_ids)
].copy()


# ------------------------------------------------------------
# Match student's current semester
# ------------------------------------------------------------

tests = tests.merge(
    students[
        [
            "Student_ID",
            "Program_ID",
            "Semester_ID"
        ]
    ].drop_duplicates(),
    on="Student_ID",
    how="inner",
    suffixes=(
        "",
        "_Student"
    )
)


tests = tests[
    tests["Semester_ID"]
    ==
    tests["Semester_ID_Student"]
].copy()


tests.drop(
    columns=["Semester_ID_Student"],
    inplace=True
)


# ------------------------------------------------------------
# Marks
# ------------------------------------------------------------

tests["Marks"] = pd.to_numeric(
    tests["Marks"],
    errors="coerce"
)


tests["Marks"] = (
    tests["Marks"]
    .clip(
        lower=0,
        upper=TEST_MAX_MARKS
    )
)


tests["Test_Percentage"] = (
    tests["Marks"]
    /
    TEST_MAX_MARKS
    * 100
)


test_summary = (
    tests
    .groupby(
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ],
        as_index=False
    )
    .agg(
        Test_Percentage=(
            "Test_Percentage",
            "mean"
        )
    )
)


print(
    "Test student-subject summaries:",
    len(test_summary)
)


# ============================================================
# 18. BUILD STUDENT-SUBJECT PERFORMANCE
# ============================================================

student_performance = student_subject.copy()


student_performance = student_performance.merge(
    attendance_summary[
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID",
            "Attendance_Percentage"
        ]
    ],
    on=[
        "Student_ID",
        "Subject_ID",
        "Semester_ID"
    ],
    how="left"
)


student_performance = student_performance.merge(
    assignment_summary[
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID",
            "Assignment_Percentage"
        ]
    ],
    on=[
        "Student_ID",
        "Subject_ID",
        "Semester_ID"
    ],
    how="left"
)


student_performance = student_performance.merge(
    test_summary[
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID",
            "Test_Percentage"
        ]
    ],
    on=[
        "Student_ID",
        "Subject_ID",
        "Semester_ID"
    ],
    how="left"
)


# ------------------------------------------------------------
# Missing assessment values
# ------------------------------------------------------------

performance_columns = [
    "Attendance_Percentage",
    "Assignment_Percentage",
    "Test_Percentage"
]


student_performance[
    performance_columns
] = student_performance[
    performance_columns
].fillna(0)


# ============================================================
# 19. OVERALL PERFORMANCE
# ============================================================

student_performance[
    "Overall_Performance"
] = (
    student_performance[
        "Attendance_Percentage"
    ]
    * ATTENDANCE_WEIGHT
    +
    student_performance[
        "Assignment_Percentage"
    ]
    * ASSIGNMENT_WEIGHT
    +
    student_performance[
        "Test_Percentage"
    ]
    * TEST_WEIGHT
)


# ============================================================
# 20. MAP TEACHER TO STUDENT PERFORMANCE
# ============================================================

teacher_student_performance = (
    teacher_allocation.merge(
        student_performance,
        on=[
            "Subject_ID",
            "Semester_ID"
        ],
        how="inner"
    )
)


# Resolve merge suffixes defensively. The generated teacher_subject.csv
# already contains Program_ID, while student_performance does not.
if "Program_ID" not in teacher_student_performance.columns:
    for candidate in ["Program_ID_x", "Program_ID_y"]:
        if candidate in teacher_student_performance.columns:
            teacher_student_performance["Program_ID"] = teacher_student_performance[candidate]
            break

if "Program_Name" not in teacher_student_performance.columns:
    for candidate in ["Program_Name_x", "Program_Name_y"]:
        if candidate in teacher_student_performance.columns:
            teacher_student_performance["Program_Name"] = teacher_student_performance[candidate]
            break

if "Semester_Name" not in teacher_student_performance.columns:
    for candidate in ["Semester_Name_x", "Semester_Name_y"]:
        if candidate in teacher_student_performance.columns:
            teacher_student_performance["Semester_Name"] = teacher_student_performance[candidate]
            break

if "Semester_Number" not in teacher_student_performance.columns:
    for candidate in ["Semester_Number_x", "Semester_Number_y"]:
        if candidate in teacher_student_performance.columns:
            teacher_student_performance["Semester_Number"] = teacher_student_performance[candidate]
            break

print(
    "\nTeacher allocation + student performance "
    "matched rows:",
    len(teacher_student_performance)
)


# ============================================================
# 21. FINAL SUBJECT-LEVEL AGGREGATION
# ============================================================

group_columns = [
    "Teacher_ID",
    "Teacher_Name",
    "Program_ID",
    "Program_Name",
    "Semester_ID",
    "Semester_Name",
    "Semester_Number",
    "Subject_ID",
    "Subject_Name",
    "Subject_Code",
    "Subject_Type"
]


final_data = (
    teacher_student_performance
    .groupby(
        group_columns,
        as_index=False
    )
    .agg(
        Total_Students=(
            "Student_ID",
            "nunique"
        ),

        Average_Attendance=(
            "Attendance_Percentage",
            "mean"
        ),

        Average_Assignment=(
            "Assignment_Percentage",
            "mean"
        ),

        Average_Test=(
            "Test_Percentage",
            "mean"
        ),

        Average_Overall=(
            "Overall_Performance",
            "mean"
        )
    )
)


# ============================================================
# 22. PERFORMANCE CATEGORY
# ============================================================

def performance_category(score):

    if pd.isna(score):
        return "No Data"

    if score >= 80:
        return "Excellent"

    elif score >= 70:
        return "Good"

    elif score >= 50:
        return "Average"

    else:
        return "Poor"


final_data[
    "Performance_Category"
] = (
    final_data[
        "Average_Overall"
    ]
    .apply(performance_category)
)


# ============================================================
# 23. ROUND VALUES
# ============================================================

percentage_columns = [
    "Average_Attendance",
    "Average_Assignment",
    "Average_Test",
    "Average_Overall"
]


final_data[
    percentage_columns
] = (
    final_data[
        percentage_columns
    ]
    .round(2)
)


# ============================================================
# 24. SORT
# ============================================================

final_data = (
    final_data
    .sort_values(
        by=[
            "Teacher_ID",
            "Program_ID",
            "Semester_Number",
            "Subject_ID"
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# 25. FINAL COLUMNS
# ============================================================

final_columns = [
    "Teacher_ID",
    "Teacher_Name",
    "Program_ID",
    "Program_Name",
    "Semester_ID",
    "Semester_Name",
    "Semester_Number",
    "Subject_ID",
    "Subject_Name",
    "Subject_Code",
    "Subject_Type",
    "Total_Students",
    "Average_Attendance",
    "Average_Assignment",
    "Average_Test",
    "Average_Overall",
    "Performance_Category"
]


final_data = final_data[
    [
        column
        for column in final_columns
        if column in final_data.columns
    ]
]


# ============================================================
# 26. SAVE OUTPUT
# ============================================================

output_file = (
    OUTPUT_DIR
    /
    "teacher_subject_performance.csv"
)


final_data.to_csv(
    output_file,
    index=False
)


# ============================================================
# 27. DIAGNOSTICS
# ============================================================

print("\n======================================")
print(" TEACHER ANALYSIS COMPLETED")
print("======================================\n")


print(
    "Final rows:",
    len(final_data)
)


if not final_data.empty:

    print(
        "Teachers in final report:",
        final_data[
            "Teacher_ID"
        ].nunique()
    )

    print(
        "Subjects in final report:",
        final_data[
            "Subject_ID"
        ].nunique()
    )

    print(
        "Programs in final report:",
        final_data[
            "Program_ID"
        ].nunique()
    )

    print(
        "Semester IDs in final report:",
        sorted(
            final_data[
                "Semester_ID"
            ]
            .dropna()
            .unique()
            .tolist()
        )
    )

    print(
        "\nSemester summary:"
    )

    print(
        final_data[
            [
                "Program_ID",
                "Program_Name",
                "Semester_ID",
                "Semester_Name",
                "Semester_Number"
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "Program_ID",
                "Semester_Number"
            ]
        )
        .to_string(
            index=False
        )
    )

    print(
        "\nPerformance categories:"
    )

    print(
        final_data[
            "Performance_Category"
        ]
        .value_counts()
    )

else:

    print(
        "\nWARNING: Final teacher analysis is empty."
    )


print(
    "\nOutput:"
)

print(output_file)