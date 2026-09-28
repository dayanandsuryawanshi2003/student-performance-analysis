"""
FINAL STUDENT DASHBOARD ANALYSIS
================================

Creates Power BI-ready data for the Student Dashboard.

Raw structure:

data/raw/
    programs.csv
    semesters.csv

    current/
        students.csv
        student_subject.csv
        subjects.csv
        attendance.csv
        assignments.csv
        tests.csv

    historical_sem1/
        students.csv
        student_subject.csv
        subjects.csv
        attendance.csv
        assignments.csv
        tests.csv
        semester_results.csv

    historical_sem2/
        students.csv
        student_subject.csv
        subjects.csv
        attendance.csv
        assignments.csv
        tests.csv
        semester_results.csv

Performance formula:

Attendance   = 30%
Assignment   = 30%
Test         = 40%

Categories:

> 80              Excellent
> 70 to 80        Good
> 50 to 70        Average
> 40 to 50        Below Average
<= 40             Needs Improvement
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "analysis"
    / "student"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. FILE READER
# ============================================================

def read_raw(filename):
    """
    Reads files from the actual raw-data structure.
    """

    file_map = {

        # ----------------------------------------------------
        # CURRENT
        # ----------------------------------------------------

        "students.csv":
            "current/students.csv",

        "student_subject.csv":
            "current/student_subject.csv",

        "subjects.csv":
            "current/subjects.csv",

        "attendance.csv":
            "current/attendance.csv",

        "assignments.csv":
            "current/assignments.csv",

        "tests.csv":
            "current/tests.csv",


        # ----------------------------------------------------
        # HISTORICAL SEMESTER 1
        # ----------------------------------------------------

        "historical_sem1_student_subject.csv":
            "historical_sem1/student_subject.csv",

        "historical_sem1_subjects.csv":
            "historical_sem1/subjects.csv",

        "historical_sem1_attendance.csv":
            "historical_sem1/attendance.csv",

        "historical_sem1_assignments.csv":
            "historical_sem1/assignments.csv",

        "historical_sem1_tests.csv":
            "historical_sem1/tests.csv",


        # ----------------------------------------------------
        # HISTORICAL SEMESTER 2
        # ----------------------------------------------------

        "semester_sem2_additions.csv":
            "historical_sem2/semester_results.csv",

        "student_subject_sem2_additions.csv":
            "historical_sem2/student_subject.csv",

        "subjects_sem2_additions.csv":
            "historical_sem2/subjects.csv",

        "attendance_with_historical_sem2.csv":
            "historical_sem2/attendance.csv",

        "assignments_with_historical_sem2.csv":
            "historical_sem2/assignments.csv",

        "tests_with_historical_sem2.csv":
            "historical_sem2/tests.csv",


        # ----------------------------------------------------
        # MASTER FILES
        # ----------------------------------------------------

        "semesters.csv":
            "semesters.csv",

        "programs.csv":
            "programs.csv",
    }

    relative_path = file_map.get(
        filename,
        filename
    )

    path = RAW_DIR / relative_path

    if not path.exists():

        raise FileNotFoundError(
            f"\nRequired file not found:\n"
            f"{path}\n\n"
            f"Please check the raw-data structure inside:\n"
            f"{RAW_DIR}\n"
        )

    df = pd.read_csv(path)

    # --------------------------------------------------------
    # Attendance column normalization
    # Actual CSV uses Status.
    # Analysis uses Attendance_Status.
    # --------------------------------------------------------

    if (
        "Status" in df.columns
        and "Attendance_Status" not in df.columns
    ):
        df = df.rename(
            columns={
                "Status": "Attendance_Status"
            }
        )

    # --------------------------------------------------------
    # Normalize attendance status
    # Current raw attendance stores Status as numeric:
    # 1 = Present, 0 = Absent. Historical files may also use
    # the same numeric representation. Convert both numeric and
    # text values to the common Attendance_Status format used by
    # attendance_stats().
    # --------------------------------------------------------
    if "Attendance_Status" in df.columns:
        status_numeric = pd.to_numeric(
            df["Attendance_Status"],
            errors="coerce"
        )

        numeric_status = status_numeric.map({
            1: "Present",
            0: "Absent"
        })

        text_status = (
            df["Attendance_Status"]
            .astype("string")
            .str.strip()
            .str.title()
            .replace({
                "1": "Present",
                "0": "Absent"
            })
        )

        df["Attendance_Status"] = numeric_status.fillna(text_status)

    return df


# ============================================================
# 3. START
# ============================================================

print("\n==============================================")
print(" FINAL STUDENT DASHBOARD ANALYSIS")
print("==============================================\n")


# ============================================================
# 4. LOAD CURRENT DATA
# ============================================================

print("Loading current data...")


students = read_raw(
    "students.csv"
)

student_subject_current = read_raw(
    "student_subject.csv"
)

subjects_current = read_raw(
    "subjects.csv"
)

attendance_current = read_raw(
    "attendance.csv"
)

assignments_current = read_raw(
    "assignments.csv"
)

tests_current = read_raw(
    "tests.csv"
)

semesters_current = read_raw(
    "semesters.csv"
)

programs = read_raw(
    "programs.csv"
)


# ============================================================
# 5. LOAD HISTORICAL SEMESTER 1
# ============================================================

print(
    "Loading historical Semester 1 data..."
)


student_subject_sem1 = read_raw(
    "historical_sem1_student_subject.csv"
)

subjects_sem1 = read_raw(
    "historical_sem1_subjects.csv"
)

attendance_sem1 = read_raw(
    "historical_sem1_attendance.csv"
)

assignments_sem1 = read_raw(
    "historical_sem1_assignments.csv"
)

tests_sem1 = read_raw(
    "historical_sem1_tests.csv"
)


# ============================================================
# 6. LOAD HISTORICAL SEMESTER 2
# ============================================================

print(
    "Loading historical Semester 2 data..."
)


semester_sem2 = read_raw(
    "semester_sem2_additions.csv"
)

student_subject_sem2 = read_raw(
    "student_subject_sem2_additions.csv"
)

subjects_sem2 = read_raw(
    "subjects_sem2_additions.csv"
)

attendance_sem2_all = read_raw(
    "attendance_with_historical_sem2.csv"
)

assignments_sem2_all = read_raw(
    "assignments_with_historical_sem2.csv"
)

tests_sem2_all = read_raw(
    "tests_with_historical_sem2.csv"
)


# ============================================================
# 7. STANDARDIZE ID COLUMNS
# ============================================================

def make_int(df, columns):

    for col in columns:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).astype("Int64")

    return df


all_loaded_data = [

    students,

    student_subject_current,
    subjects_current,
    attendance_current,
    assignments_current,
    tests_current,

    semesters_current,
    programs,

    student_subject_sem1,
    subjects_sem1,
    attendance_sem1,
    assignments_sem1,
    tests_sem1,

    semester_sem2,
    student_subject_sem2,
    subjects_sem2,
    attendance_sem2_all,
    assignments_sem2_all,
    tests_sem2_all
]


for df in all_loaded_data:

    make_int(
        df,
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID",
            "Program_ID",
            "Assignment_ID",
            "Assignment_No",
            "Test_ID",
            "Test_No",
            "Attendance_ID",
            "Semester_Number"
        ]
    )


# ============================================================
# 8. CURRENT STUDENT MASTER
# ============================================================

current_student_info = students[
    [
        "Student_ID",
        "Roll_No",
        "Name",
        "Gender",
        "Department_ID",
        "Semester_ID",
        "Program_ID"
    ]
].copy()


current_student_info = (
    current_student_info
    .drop_duplicates(
        subset=["Student_ID"]
    )
)


# ============================================================
# 9. PROGRAM MASTER
# ============================================================

program_info = programs[
    [
        "Program_ID",
        "Program_Name"
    ]
].drop_duplicates(
    subset=["Program_ID"]
)


# ============================================================
# 10. SEMESTER MASTER
# ============================================================

current_semester_info = semesters_current[
    [
        "Semester_ID",
        "Semester_Name",
        "Program_ID",
        "Semester_Number"
    ]
].drop_duplicates(
    subset=["Semester_ID"]
)


# ============================================================
# 11. IDENTIFY CURRENT SEM 1 AND SEM 3
# ============================================================

current_sem1_students = (
    current_student_info[
        current_student_info["Semester_ID"].isin(
            current_semester_info.loc[
                current_semester_info[
                    "Semester_Number"
                ].eq(1),
                "Semester_ID"
            ]
        )
    ]
    .copy()
)


current_sem3_students = (
    current_student_info[
        current_student_info["Semester_ID"].isin(
            current_semester_info.loc[
                current_semester_info[
                    "Semester_Number"
                ].eq(3),
                "Semester_ID"
            ]
        )
    ]
    .copy()
)


all_current_students = (
    pd.concat(
        [
            current_sem1_students,
            current_sem3_students
        ],
        ignore_index=True
    )
    .drop_duplicates(
        "Student_ID"
    )
)


all_current_student_ids = set(
    all_current_students[
        "Student_ID"
    ]
    .dropna()
    .astype(int)
)


current_sem3_student_ids = set(
    current_sem3_students[
        "Student_ID"
    ]
    .dropna()
    .astype(int)
)


print(
    f"Current students analysed: "
    f"{len(all_current_student_ids)}"
)

print(
    f"Current Semester 1 students: "
    f"{len(current_sem1_students)}"
)

print(
    f"Current Semester 3 students: "
    f"{len(current_sem3_students)}"
)


print(
    "\nCurrent students by Program and Semester:"
)


current_check = (
    all_current_students

    .merge(
        program_info,
        on="Program_ID",
        how="left"
    )

    .merge(
        current_semester_info[
            [
                "Semester_ID",
                "Semester_Name",
                "Semester_Number"
            ]
        ],
        on="Semester_ID",
        how="left"
    )
)


print(
    current_check
    .groupby(
        [
            "Program_Name",
            "Semester_Number"
        ]
    )
    .size()
    .to_string()
)


# ============================================================
# 12. PERFORMANCE FUNCTIONS
# ============================================================

def attendance_stats(df):

    if df.empty:

        return {
            "Average_Attendance": np.nan,
            "Attendance_Total_Classes": 0,
            "Attendance_Present": 0
        }


    status = (
        df["Attendance_Status"]
        .astype(str)
        .str.strip()
        .str.lower()
    )


    total = len(df)

    present = status.eq(
        "present"
    ).sum()


    percentage = (
        present / total * 100
        if total > 0
        else np.nan
    )


    return {
        "Average_Attendance":
            percentage,

        "Attendance_Total_Classes":
            total,

        "Attendance_Present":
            present
    }


def performance_category(score):

    if pd.isna(score):
        return "Not Available"

    if score > 80:
        return "Excellent"

    if score > 70:
        return "Good"

    if score > 50:
        return "Average"

    if score > 40:
        return "Below Average"

    return "Needs Improvement"


def weakest_factor(
    attendance,
    assignment,
    test
):

    values = {

        "Attendance":
            attendance,

        "Assignment":
            assignment,

        "Test":
            test
    }


    if any(
        pd.isna(v)
        for v in values.values()
    ):

        return "Not Available"


    return min(
        values,
        key=values.get
    )


def attention_status(score):

    if pd.isna(score):
        return "Not Available"

    if score >= 70:
        return "On Track"

    return "Needs Attention"


# ============================================================
# 13. SUBJECT PERFORMANCE BUILDER
# ============================================================

def build_subject_performance(
    student_ids,
    enrollment,
    subject_master,
    attendance,
    assignments,
    tests,
    semester_number,
    semester_id_filter=None
):

    student_ids = set(
        int(x)
        for x in student_ids
    )


    # --------------------------------------------------------
    # Enrollment
    # --------------------------------------------------------

    e = enrollment[
        enrollment["Student_ID"].isin(
            student_ids
        )
    ].copy()


    if semester_id_filter is not None:

        e = e[
            e["Semester_ID"].isin(
                set(
                    int(x)
                    for x in semester_id_filter
                )
            )
        ].copy()


    if e.empty:
        return pd.DataFrame()


    e = e[
        [
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ]
    ].drop_duplicates()


    # --------------------------------------------------------
    # Subject master
    # --------------------------------------------------------

    s = subject_master[
        [
            "Subject_ID",
            "Program_ID",
            "Semester_ID",
            "Subject_Code",
            "Subject_Name",
            "Subject_Type"
        ]
    ].drop_duplicates(
        subset=[
            "Subject_ID",
            "Semester_ID"
        ]
    )


    result = e.merge(
        s,
        on=[
            "Subject_ID",
            "Semester_ID"
        ],
        how="left"
    )


    # --------------------------------------------------------
    # Student information
    # --------------------------------------------------------

    result = result.merge(
        current_student_info,
        on="Student_ID",
        how="left",
        suffixes=(
            "",
            "_student"
        )
    )


    if "Program_ID_student" in result.columns:

        result["Program_ID"] = (
            result[
                "Program_ID_student"
            ]
            .fillna(
                result["Program_ID"]
            )
        )


        result.drop(
            columns=[
                "Program_ID_student"
            ],
            inplace=True
        )


    result = result.merge(
        program_info,
        on="Program_ID",
        how="left"
    )


    result["Semester_Number"] = (
        semester_number
    )


    result["Semester_Name"] = (
        "Semester "
        + str(semester_number)
    )


    # ========================================================
    # ATTENDANCE
    # ========================================================

    a = attendance[
        attendance["Student_ID"].isin(
            student_ids
        )
    ].copy()


    if semester_id_filter is not None:

        a = a[
            a["Semester_ID"].isin(
                set(
                    int(x)
                    for x in semester_id_filter
                )
            )
        ].copy()


    attendance_rows = []


    if not a.empty:

        for keys, group in a.groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ]
        ):

            stats = attendance_stats(
                group
            )


            attendance_rows.append(
                {
                    "Student_ID":
                        int(keys[0]),

                    "Subject_ID":
                        int(keys[1]),

                    "Semester_ID":
                        int(keys[2]),

                    **stats
                }
            )


    attendance_summary = pd.DataFrame(
        attendance_rows
    )


    if not attendance_summary.empty:

        result = result.merge(
            attendance_summary,
            on=[
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ],
            how="left"
        )


    # ========================================================
    # ASSIGNMENTS
    # ========================================================

    ass = assignments[
        assignments["Student_ID"].isin(
            student_ids
        )
    ].copy()


    if semester_id_filter is not None:

        ass = ass[
            ass["Semester_ID"].isin(
                set(
                    int(x)
                    for x in semester_id_filter
                )
            )
        ].copy()


    if not ass.empty:

        assignment_summary = (
            ass
            .groupby(
                [
                    "Student_ID",
                    "Subject_ID",
                    "Semester_ID"
                ],
                as_index=False
            )
            .agg(
                Average_Assignment_Marks=(
                    "Marks",
                    "mean"
                ),

                Assignment_Count=(
                    "Assignment_No",
                    "count"
                )
            )
        )


        assignment_summary[
            "Average_Assignment"
        ] = (

            pd.to_numeric(
                assignment_summary[
                    "Average_Assignment_Marks"
                ],
                errors="coerce"
            )

            / 20
            * 100
        )


        result = result.merge(
            assignment_summary,
            on=[
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ],
            how="left"
        )


    # ========================================================
    # TESTS
    # ========================================================

    t = tests[
        tests["Student_ID"].isin(
            student_ids
        )
    ].copy()


    if semester_id_filter is not None:

        t = t[
            t["Semester_ID"].isin(
                set(
                    int(x)
                    for x in semester_id_filter
                )
            )
        ].copy()


    if not t.empty:

        test_summary = (
            t
            .groupby(
                [
                    "Student_ID",
                    "Subject_ID",
                    "Semester_ID"
                ],
                as_index=False
            )
            .agg(
                Average_Test_Marks=(
                    "Marks",
                    "mean"
                ),

                Test_Count=(
                    "Test_No",
                    "count"
                )
            )
        )


        test_summary[
            "Average_Test"
        ] = (

            pd.to_numeric(
                test_summary[
                    "Average_Test_Marks"
                ],
                errors="coerce"
            )

            / 20
            * 100
        )


        result = result.merge(
            test_summary,
            on=[
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ],
            how="left"
        )


    # ========================================================
    # MISSING METRICS
    # ========================================================

    required_metric_columns = [

        "Average_Attendance",

        "Attendance_Total_Classes",

        "Attendance_Present",

        "Average_Assignment",

        "Average_Assignment_Marks",

        "Assignment_Count",

        "Average_Test",

        "Average_Test_Marks",

        "Test_Count"
    ]


    for col in required_metric_columns:

        if col not in result.columns:

            result[col] = np.nan


    # ========================================================
    # OVERALL PERFORMANCE
    # ========================================================

    result["Average_Overall"] = (

        result[
            "Average_Attendance"
        ] * 0.30

        +

        result[
            "Average_Assignment"
        ] * 0.30

        +

        result[
            "Average_Test"
        ] * 0.40
    )


    result["Performance_Category"] = (
        result[
            "Average_Overall"
        ]
        .apply(
            performance_category
        )
    )


    result["Weakest_Factor"] = (
        result.apply(
            lambda r:
            weakest_factor(
                r["Average_Attendance"],
                r["Average_Assignment"],
                r["Average_Test"]
            ),
            axis=1
        )
    )


    result["Attention_Status"] = (
        result[
            "Average_Overall"
        ]
        .apply(
            attention_status
        )
    )


    # ========================================================
    # ROUND NUMBERS
    # ========================================================

    numeric_columns = [

        "Average_Attendance",

        "Average_Assignment",

        "Average_Assignment_Marks",

        "Average_Test",

        "Average_Test_Marks",

        "Average_Overall"
    ]


    for col in numeric_columns:

        result[col] = pd.to_numeric(
            result[col],
            errors="coerce"
        ).round(2)


    return result


# ============================================================
# 14. CURRENT SEMESTER 1
# ============================================================

print(
    "\nAnalysing current Semester 1..."
)


current_sem1_ids = set(
    current_sem1_students[
        "Student_ID"
    ]
    .astype(int)
)


current_sem1_semester_ids = set(
    current_sem1_students[
        "Semester_ID"
    ]
    .astype(int)
)


current_sem1_performance = (
    build_subject_performance(

        current_sem1_ids,

        student_subject_current,

        subjects_current,

        attendance_current,

        assignments_current,

        tests_current,

        semester_number=1,

        semester_id_filter=
            current_sem1_semester_ids
    )
)


# ============================================================
# 15. HISTORICAL SEMESTER 1
# ============================================================

print(
    "Analysing historical Semester 1 "
    "for current Semester 3 students..."
)


historical_sem1_performance = (
    build_subject_performance(

        current_sem3_student_ids,

        student_subject_sem1,

        subjects_sem1,

        attendance_sem1,

        assignments_sem1,

        tests_sem1,

        semester_number=1
    )
)


# ============================================================
# 16. HISTORICAL SEMESTER 2
# ============================================================

print(
    "Analysing historical Semester 2..."
)


historical_sem2_enrollment = (
    student_subject_sem2[
        student_subject_sem2[
            "Student_ID"
        ].isin(
            current_sem3_student_ids
        )
    ]
    .copy()
)


historical_sem2_ids = set(
    historical_sem2_enrollment[
        "Student_ID"
    ]
    .astype(int)
)


historical_sem2_semester_ids = set(
    historical_sem2_enrollment[
        "Semester_ID"
    ]
    .astype(int)
)


attendance_sem2 = (
    attendance_sem2_all[
        attendance_sem2_all[
            "Student_ID"
        ].isin(
            historical_sem2_ids
        )
        &
        attendance_sem2_all[
            "Semester_ID"
        ].isin(
            historical_sem2_semester_ids
        )
    ]
    .copy()
)


assignments_sem2 = (
    assignments_sem2_all[
        assignments_sem2_all[
            "Student_ID"
        ].isin(
            historical_sem2_ids
        )
        &
        assignments_sem2_all[
            "Semester_ID"
        ].isin(
            historical_sem2_semester_ids
        )
    ]
    .copy()
)


tests_sem2 = (
    tests_sem2_all[
        tests_sem2_all[
            "Student_ID"
        ].isin(
            historical_sem2_ids
        )
        &
        tests_sem2_all[
            "Semester_ID"
        ].isin(
            historical_sem2_semester_ids
        )
    ]
    .copy()
)


historical_sem2_performance = (
    build_subject_performance(

        current_sem3_student_ids,

        historical_sem2_enrollment,

        subjects_sem2,

        attendance_sem2,

        assignments_sem2,

        tests_sem2,

        semester_number=2,

        semester_id_filter=
            historical_sem2_semester_ids
    )
)


# ============================================================
# 17. CURRENT SEMESTER 3
# ============================================================

print(
    "Analysing current Semester 3..."
)


current_sem3_semester_ids = set(
    current_sem3_students[
        "Semester_ID"
    ]
    .astype(int)
)


current_sem3_performance = (
    build_subject_performance(

        current_sem3_student_ids,

        student_subject_current,

        subjects_current,

        attendance_current,

        assignments_current,

        tests_current,

        semester_number=3,

        semester_id_filter=
            current_sem3_semester_ids
    )
)


# ============================================================
# 18. COMBINE ALL SUBJECT DATA
# ============================================================

print(
    "Combining Student Dashboard data..."
)


all_subject_performance = pd.concat(
    [
        current_sem1_performance,

        historical_sem1_performance,

        historical_sem2_performance,

        current_sem3_performance
    ],
    ignore_index=True
)


all_subject_performance = (
    all_subject_performance

    .drop_duplicates(
        subset=[
            "Student_ID",
            "Semester_Number",
            "Subject_ID"
        ]
    )

    .copy()
)


all_subject_performance = (
    all_subject_performance

    .sort_values(
        [
            "Student_ID",
            "Semester_Number",
            "Subject_Name"
        ],
        na_position="last"
    )

    .reset_index(
        drop=True
    )
)


# ============================================================
# 19. STUDENT SEMESTER PERFORMANCE
# ============================================================

print(
    "Creating student-semester performance..."
)


group_columns = [

    "Student_ID",

    "Roll_No",

    "Name",

    "Gender",

    "Program_ID",

    "Program_Name",

    "Semester_Number",

    "Semester_Name"
]


student_semester_performance = (
    all_subject_performance

    .groupby(
        group_columns,
        as_index=False
    )

    .agg(

        Average_Attendance=(
            "Average_Attendance",
            "mean"
        ),

        Average_Assignment=(
            "Average_Assignment",
            "mean"
        ),

        Average_Test=(
            "Average_Test",
            "mean"
        ),

        Average_Overall=(
            "Average_Overall",
            "mean"
        ),

        Subjects_Count=(
            "Subject_ID",
            "nunique"
        )
    )
)


student_semester_performance[
    "Performance_Category"
] = (
    student_semester_performance[
        "Average_Overall"
    ]
    .apply(
        performance_category
    )
)


student_semester_performance[
    "Weakest_Factor"
] = (
    student_semester_performance.apply(

        lambda r:
        weakest_factor(

            r["Average_Attendance"],

            r["Average_Assignment"],

            r["Average_Test"]
        ),

        axis=1
    )
)


student_semester_performance[
    "Attention_Status"
] = (
    student_semester_performance[
        "Average_Overall"
    ]
    .apply(
        attention_status
    )
)


for col in [

    "Average_Attendance",

    "Average_Assignment",

    "Average_Test",

    "Average_Overall"

]:

    student_semester_performance[col] = (
        pd.to_numeric(
            student_semester_performance[col],
            errors="coerce"
        )
        .round(2)
    )


student_semester_performance = (
    student_semester_performance

    .sort_values(
        [
            "Student_ID",
            "Semester_Number"
        ]
    )

    .reset_index(
        drop=True
    )
)


# ============================================================
# 20. PERFORMANCE JOURNEY
# ============================================================

print(
    "Creating performance journey..."
)


student_journey = (
    student_semester_performance[
        [
            "Student_ID",
            "Roll_No",
            "Name",
            "Program_ID",
            "Program_Name",
            "Semester_Number",
            "Semester_Name",
            "Average_Attendance",
            "Average_Assignment",
            "Average_Test",
            "Average_Overall",
            "Performance_Category"
        ]
    ]
    .copy()
)


student_journey[
    "Previous_Overall"
] = (
    student_journey
    .groupby(
        "Student_ID"
    )[
        "Average_Overall"
    ]
    .shift(1)
)


student_journey[
    "Overall_Change"
] = (
    student_journey[
        "Average_Overall"
    ]

    -

    student_journey[
        "Previous_Overall"
    ]
).round(2)


student_journey[
    "Progress_Status"
] = np.select(

    [

        student_journey[
            "Overall_Change"
        ].isna(),

        student_journey[
            "Overall_Change"
        ] >= 5,

        student_journey[
            "Overall_Change"
        ] <= -5
    ],

    [

        "Starting Point",

        "Improved",

        "Declined"
    ],

    default="Stable"
)


# ============================================================
# 21. CURRENT STUDENT PROFILE
# ============================================================

print(
    "Creating current student profile..."
)


current_semester_per_student = pd.concat(

    [

        current_sem1_students[
            ["Student_ID"]
        ]
        .assign(
            Current_Semester_Number=1
        ),

        current_sem3_students[
            ["Student_ID"]
        ]
        .assign(
            Current_Semester_Number=3
        )
    ],

    ignore_index=True
)


current_profile = (
    all_subject_performance

    .merge(
        current_semester_per_student,
        on="Student_ID",
        how="inner"
    )
)


current_profile = (
    current_profile[
        current_profile[
            "Semester_Number"
        ]
        .eq(
            current_profile[
                "Current_Semester_Number"
            ]
        )
    ]
    .copy()
)


current_profile = (
    current_profile

    .groupby(

        [

            "Student_ID",

            "Roll_No",

            "Name",

            "Gender",

            "Program_ID",

            "Program_Name",

            "Current_Semester_Number"
        ],

        as_index=False
    )

    .agg(

        Average_Attendance=(
            "Average_Attendance",
            "mean"
        ),

        Average_Assignment=(
            "Average_Assignment",
            "mean"
        ),

        Average_Test=(
            "Average_Test",
            "mean"
        ),

        Average_Overall=(
            "Average_Overall",
            "mean"
        ),

        Subjects_Count=(
            "Subject_ID",
            "nunique"
        )
    )
)


current_profile[
    "Current_Semester"
] = (
    "Semester "
    +
    current_profile[
        "Current_Semester_Number"
    ].astype(str)
)


current_profile[
    "Performance_Category"
] = (
    current_profile[
        "Average_Overall"
    ]
    .apply(
        performance_category
    )
)


current_profile[
    "Current_Weakest_Factor"
] = (
    current_profile.apply(

        lambda r:
        weakest_factor(

            r["Average_Attendance"],

            r["Average_Assignment"],

            r["Average_Test"]
        ),

        axis=1
    )
)


current_profile[
    "Current_Status"
] = (
    current_profile[
        "Average_Overall"
    ]
    .apply(
        attention_status
    )
)


# ============================================================
# 22. JOURNEY PIVOT
# ============================================================

journey_pivot = (

    student_semester_performance

    .pivot_table(

        index="Student_ID",

        columns="Semester_Number",

        values="Average_Overall",

        aggfunc="mean"
    )

    .rename(

        columns={

            1: "Sem1_Overall",

            2: "Sem2_Overall",

            3: "Sem3_Overall"
        }
    )

    .reset_index()
)


current_profile = (
    current_profile

    .merge(
        journey_pivot,
        on="Student_ID",
        how="left"
    )
)


current_profile[
    "Sem1_to_Sem2_Change"
] = (

    current_profile[
        "Sem2_Overall"
    ]

    -

    current_profile[
        "Sem1_Overall"
    ]

).round(2)


current_profile[
    "Sem2_to_Sem3_Change"
] = (

    current_profile[
        "Sem3_Overall"
    ]

    -

    current_profile[
        "Sem2_Overall"
    ]

).round(2)


current_profile[
    "Sem1_to_Sem3_Change"
] = (

    current_profile[
        "Sem3_Overall"
    ]

    -

    current_profile[
        "Sem1_Overall"
    ]

).round(2)


# ============================================================
# 23. STRONGEST + WEAKEST SUBJECT
# ============================================================

print(
    "Finding strongest and weakest current subjects..."
)


current_subjects = (

    current_profile[
        [
            "Student_ID",
            "Current_Semester_Number"
        ]
    ]

    .merge(

        all_subject_performance,

        left_on=[
            "Student_ID",
            "Current_Semester_Number"
        ],

        right_on=[
            "Student_ID",
            "Semester_Number"
        ],

        how="inner"
    )
)


# ------------------------------------------------------------
# WEAKEST SUBJECT
# ------------------------------------------------------------

# IMPORTANT:
# Some students may have all-NA performance scores.
# Remove those rows before idxmin().

valid_weak = (
    current_subjects
    .dropna(
        subset=[
            "Average_Overall"
        ]
    )
    .copy()
)


weak_idx = (

    valid_weak

    .groupby(
        "Student_ID"
    )[
        "Average_Overall"
    ]

    .idxmin()
)


weakest = (

    valid_weak.loc[

        weak_idx,

        [
            "Student_ID",
            "Subject_Name",
            "Average_Overall",
            "Weakest_Factor"
        ]
    ]

    .rename(

        columns={

            "Subject_Name":
                "Weakest_Subject",

            "Average_Overall":
                "Weakest_Subject_Overall",

            "Weakest_Factor":
                "Weakest_Subject_Factor"
        }
    )
)


# ------------------------------------------------------------
# STRONGEST SUBJECT
# ------------------------------------------------------------

valid_strong = (
    current_subjects
    .dropna(
        subset=[
            "Average_Overall"
        ]
    )
    .copy()
)


strong_idx = (

    valid_strong

    .groupby(
        "Student_ID"
    )[
        "Average_Overall"
    ]

    .idxmax()
)


strongest = (

    valid_strong.loc[

        strong_idx,

        [
            "Student_ID",
            "Subject_Name",
            "Average_Overall"
        ]
    ]

    .rename(

        columns={

            "Subject_Name":
                "Strongest_Subject",

            "Average_Overall":
                "Strongest_Subject_Overall"
        }
    )
)


current_profile = (
    current_profile

    .merge(
        weakest,
        on="Student_ID",
        how="left"
    )

    .merge(
        strongest,
        on="Student_ID",
        how="left"
    )
)


# ============================================================
# 24. ROUND PROFILE METRICS
# ============================================================

profile_numeric_columns = [

    "Average_Attendance",

    "Average_Assignment",

    "Average_Test",

    "Average_Overall",

    "Sem1_Overall",

    "Sem2_Overall",

    "Sem3_Overall",

    "Sem1_to_Sem2_Change",

    "Sem2_to_Sem3_Change",

    "Sem1_to_Sem3_Change",

    "Weakest_Subject_Overall",

    "Strongest_Subject_Overall"
]


for col in profile_numeric_columns:

    if col in current_profile.columns:

        current_profile[col] = (
            pd.to_numeric(
                current_profile[col],
                errors="coerce"
            )
            .round(2)
        )


# ============================================================
# 25. REVISION & ATTENTION
# ============================================================

print(
    "Creating revision and attention data..."
)


revision_attention = current_subjects[
    [

        "Student_ID",

        "Roll_No",

        "Name",

        "Program_ID",

        "Program_Name",

        "Current_Semester_Number",

        "Subject_ID",

        "Subject_Name",

        "Subject_Code",

        "Subject_Type",

        "Average_Attendance",

        "Average_Assignment",

        "Average_Test",

        "Average_Overall",

        "Performance_Category",

        "Weakest_Factor",

        "Attention_Status"
    ]
].copy()


revision_attention[
    "Revision_Priority"
] = np.select(

    [

        revision_attention[
            "Average_Overall"
        ] < 50,

        revision_attention[
            "Average_Overall"
        ] < 70,

        revision_attention[
            "Average_Overall"
        ] < 80
    ],

    [

        "High",

        "Medium",

        "Low"
    ],

    default="On Track"
)


revision_attention = (
    revision_attention

    .rename(

        columns={

            "Current_Semester_Number":
                "Semester_Number"
        }
    )
)


revision_attention = (

    revision_attention

    .sort_values(

        [
            "Student_ID",
            "Average_Overall"
        ],

        ascending=[
            True,
            True
        ]
    )

    .reset_index(
        drop=True
    )
)


# ============================================================
# 26. DASHBOARD MASTER
# ============================================================

print(
    "Creating dashboard master..."
)


student_dashboard_master = (
    current_profile.copy()
)


student_dashboard_master[
    "Student_Key"
] = (

    student_dashboard_master[
        "Student_ID"
    ].astype(str)

    + " - "

    +

    student_dashboard_master[
        "Name"
    ].astype(str)
)


student_dashboard_master = (
    student_dashboard_master[

        [

            "Student_ID",

            "Student_Key",

            "Roll_No",

            "Name",

            "Gender",

            "Program_ID",

            "Program_Name",

            "Current_Semester_Number",

            "Current_Semester",

            "Average_Attendance",

            "Average_Assignment",

            "Average_Test",

            "Average_Overall",

            "Performance_Category",

            "Current_Status",

            "Current_Weakest_Factor",

            "Strongest_Subject",

            "Strongest_Subject_Overall",

            "Weakest_Subject",

            "Weakest_Subject_Overall",

            "Weakest_Subject_Factor",

            "Sem1_Overall",

            "Sem2_Overall",

            "Sem3_Overall",

            "Sem1_to_Sem2_Change",

            "Sem2_to_Sem3_Change",

            "Sem1_to_Sem3_Change",

            "Subjects_Count"
        ]
    ]
)


# ============================================================
# 27. SAVE POWER BI FILES
# ============================================================

print(
    "\nSaving Power BI-ready CSV files..."
)


all_subject_performance.to_csv(

    OUTPUT_DIR
    / "student_subject_performance.csv",

    index=False
)


student_semester_performance.to_csv(

    OUTPUT_DIR
    / "student_semester_performance.csv",

    index=False
)


student_journey.to_csv(

    OUTPUT_DIR
    / "student_performance_journey.csv",

    index=False
)


current_profile.to_csv(

    OUTPUT_DIR
    / "student_current_profile.csv",

    index=False
)


revision_attention.to_csv(

    OUTPUT_DIR
    / "student_revision_attention.csv",

    index=False
)


student_dashboard_master.to_csv(

    OUTPUT_DIR
    / "student_dashboard_master.csv",

    index=False
)


# ============================================================
# 28. FINAL VALIDATION
# ============================================================

print(
    "\n=============================================="
)

print(
    " ANALYSIS COMPLETED SUCCESSFULLY"
)

print(
    "=============================================="
)


print(
    f"\nAll current students: "
    f"{len(all_current_student_ids)}"
)


print(
    f"Student-subject rows: "
    f"{len(all_subject_performance)}"
)


print(
    f"Student-semester rows: "
    f"{len(student_semester_performance)}"
)


print(
    f"Journey rows: "
    f"{len(student_journey)}"
)


print(
    f"Current profiles: "
    f"{len(current_profile)}"
)


print(
    f"Revision/attention rows: "
    f"{len(revision_attention)}"
)


print(
    "\nCurrent Student Report coverage:"
)


print(

    current_profile[

        [
            "Program_Name",
            "Current_Semester_Number"
        ]

    ]

    .groupby(

        [
            "Program_Name",
            "Current_Semester_Number"
        ]

    )

    .size()

    .to_string()
)


print(
    "\nCreated files:"
)


for file in sorted(
    OUTPUT_DIR.glob(
        "student_*.csv"
    )
):

    print(
        f"  - {file.name}"
    )


print(
    "\nThese files are ready "
    "to import into Power BI."
)


print(
    "\nIMPORTANT: Raw data and "
    "Admin/Teacher reports "
    "were not modified."
)