import pandas as pd
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"
POWERBI_DIR = ANALYSIS_DIR / "powerbi"

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
POWERBI_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD CLEANED DATA
# ============================================================

students = pd.read_csv(
    CLEANED_DIR / "students_cleaned.csv"
)

attendance = pd.read_csv(
    CLEANED_DIR / "attendance_cleaned.csv"
)

assignments = pd.read_csv(
    CLEANED_DIR / "assignments_cleaned.csv"
)

tests = pd.read_csv(
    CLEANED_DIR / "tests_cleaned.csv"
)


# ============================================================
# LOAD MASTER DATA
# ============================================================

programs = pd.read_csv(
    RAW_DIR / "programs.csv"
)

semesters = pd.read_csv(
    RAW_DIR / "semesters.csv"
)


# ============================================================
# MASTER STUDENT INFORMATION
# ============================================================

student_info_columns = [
    "Student_ID",
    "Roll_No",
    "Name",
    "Department_ID",
    "Program_ID",
    "Semester_ID"
]

student_info = students[
    [
        column
        for column in student_info_columns
        if column in students.columns
    ]
].drop_duplicates(
    subset=["Student_ID"]
)


# ============================================================
# ADD PROGRAM NAME
# ============================================================

student_info = student_info.merge(
    programs[
        [
            "Program_ID",
            "Program_Name"
        ]
    ].drop_duplicates(
        subset=["Program_ID"]
    ),
    on="Program_ID",
    how="left"
)


# ============================================================
# ADD SEMESTER NAME
# ============================================================

student_info = student_info.merge(
    semesters[
        [
            "Semester_ID",
            "Semester_Name"
        ]
    ].drop_duplicates(
        subset=["Semester_ID"]
    ),
    on="Semester_ID",
    how="left"
)


# ============================================================
# ATTENDANCE ANALYSIS
# ============================================================

def attendance_analysis():

    print("\n" + "=" * 60)
    print("ATTENDANCE ANALYSIS")
    print("=" * 60)

    attendance_summary = (
        attendance.groupby(
            [
                "Student_ID",
                "Semester_ID"
            ]
        )
        .agg(
            Total_Classes=(
                "Attendance_Status",
                "count"
            ),

            Present=(
                "Attendance_Status",
                lambda x: (
                    x == "Present"
                ).sum()
            )
        )
        .reset_index()
    )

    attendance_summary["Absent"] = (
        attendance_summary["Total_Classes"]
        - attendance_summary["Present"]
    )

    attendance_summary["Attendance_Percentage"] = (
        attendance_summary["Present"]
        / attendance_summary["Total_Classes"]
        * 100
    ).round(2)

    attendance_summary["Certificate_Eligible"] = (
        attendance_summary["Attendance_Percentage"]
        >= 75
    ).map({
        True: "Yes",
        False: "No"
    })

    attendance_summary = attendance_summary.merge(
        student_info,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    preferred_columns = [
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Present",
        "Absent",
        "Total_Classes",
        "Attendance_Percentage",
        "Certificate_Eligible"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in attendance_summary.columns
    ]

    attendance_summary = attendance_summary[
        final_columns
    ]

    attendance_summary.to_csv(
        ANALYSIS_DIR /
        "student_attendance_analysis.csv",
        index=False
    )

    print(
        "student_attendance_analysis.csv created."
    )


# ============================================================
# ASSIGNMENT ANALYSIS
# ============================================================

def assignment_analysis():

    print("\n" + "=" * 60)
    print("ASSIGNMENT ANALYSIS")
    print("=" * 60)

    assignment_summary = (
        assignments.groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ]
        )
        .agg(
            Obtained_Marks=(
                "Marks",
                "sum"
            ),

            Assignment_Count=(
                "Marks",
                "count"
            )
        )
        .reset_index()
    )

    assignment_summary["Maximum_Marks"] = (
        assignment_summary["Assignment_Count"]
        * 20
    )

    assignment_summary["Assignment_Percentage"] = (
        assignment_summary["Obtained_Marks"]
        / assignment_summary["Maximum_Marks"]
        * 100
    ).round(2)

    assignment_summary = assignment_summary.merge(
        student_info,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    preferred_columns = [
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Subject_ID",
        "Obtained_Marks",
        "Maximum_Marks",
        "Assignment_Percentage"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in assignment_summary.columns
    ]

    assignment_summary = assignment_summary[
        final_columns
    ]

    assignment_summary.to_csv(
        ANALYSIS_DIR /
        "assignment_analysis.csv",
        index=False
    )

    print(
        "assignment_analysis.csv created."
    )


# ============================================================
# TEST ANALYSIS
# ============================================================

def test_analysis():

    print("\n" + "=" * 60)
    print("TEST ANALYSIS")
    print("=" * 60)

    test_summary = (
        tests.groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ]
        )
        .agg(
            Obtained_Marks=(
                "Marks",
                "sum"
            ),

            Test_Count=(
                "Marks",
                "count"
            )
        )
        .reset_index()
    )

    test_summary["Maximum_Marks"] = (
        test_summary["Test_Count"]
        * 20
    )

    test_summary["Test_Percentage"] = (
        test_summary["Obtained_Marks"]
        / test_summary["Maximum_Marks"]
        * 100
    ).round(2)

    test_summary = test_summary.merge(
        student_info,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    preferred_columns = [
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Subject_ID",
        "Obtained_Marks",
        "Maximum_Marks",
        "Test_Percentage"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in test_summary.columns
    ]

    test_summary = test_summary[
        final_columns
    ]

    test_summary.to_csv(
        ANALYSIS_DIR /
        "test_analysis.csv",
        index=False
    )

    print(
        "test_analysis.csv created."
    )


# ============================================================
# OVERALL PERFORMANCE ANALYSIS
# ============================================================

def overall_performance_analysis():

    print("\n" + "=" * 60)
    print("OVERALL PERFORMANCE ANALYSIS")
    print("=" * 60)

    attendance_df = pd.read_csv(
        ANALYSIS_DIR /
        "student_attendance_analysis.csv"
    )

    assignment_df = pd.read_csv(
        ANALYSIS_DIR /
        "assignment_analysis.csv"
    )

    test_df = pd.read_csv(
        ANALYSIS_DIR /
        "test_analysis.csv"
    )

    # --------------------------------------------------------
    # STUDENT LEVEL ASSIGNMENT PERFORMANCE
    # --------------------------------------------------------

    assignment_student = (
        assignment_df.groupby(
            [
                "Student_ID",
                "Semester_ID"
            ]
        )["Assignment_Percentage"]
        .mean()
        .reset_index()
    )

    # --------------------------------------------------------
    # STUDENT LEVEL TEST PERFORMANCE
    # --------------------------------------------------------

    test_student = (
        test_df.groupby(
            [
                "Student_ID",
                "Semester_ID"
            ]
        )["Test_Percentage"]
        .mean()
        .reset_index()
    )

    # --------------------------------------------------------
    # START WITH ALL CURRENT STUDENTS
    # --------------------------------------------------------
    # Attendance may not yet exist for every current student.
    # Start from the current student list so that a missing attendance
    # record does not remove that student from the Power BI dataset.

    current_students = students[
        [
            "Student_ID",
            "Semester_ID"
        ]
    ].drop_duplicates()

    attendance_student = attendance_df[
        [
            "Student_ID",
            "Semester_ID",
            "Attendance_Percentage",
            "Certificate_Eligible"
        ]
    ].drop_duplicates(
        subset=["Student_ID", "Semester_ID"]
    )

    overall = current_students.merge(
        attendance_student,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    overall = overall.merge(
        assignment_student,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    overall = overall.merge(
        test_student,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    overall["Attendance_Percentage"] = (
        overall["Attendance_Percentage"]
        .fillna(0)
    )

    overall["Assignment_Percentage"] = (
        overall["Assignment_Percentage"]
        .fillna(0)
    )

    overall["Test_Percentage"] = (
        overall["Test_Percentage"]
        .fillna(0)
    )

    overall["Certificate_Eligible"] = (
        overall["Certificate_Eligible"]
        .fillna("No")
    )

    # Add the current student's display/master information.
    overall = overall.merge(
        student_info,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    # --------------------------------------------------------
    # WEIGHTED PERFORMANCE
    # --------------------------------------------------------

    overall["Attendance_Weight"] = (
        overall["Attendance_Percentage"]
        * 0.30
    )

    overall["Assignment_Weight"] = (
        overall["Assignment_Percentage"]
        * 0.30
    )

    overall["Test_Weight"] = (
        overall["Test_Percentage"]
        * 0.40
    )

    overall["Overall_Performance_Score"] = (
        overall["Attendance_Weight"]
        + overall["Assignment_Weight"]
        + overall["Test_Weight"]
    ).round(2)

    # --------------------------------------------------------
    # PERFORMANCE CATEGORY
    # --------------------------------------------------------

    def performance_category(score):

        if score > 80:
            return "Excellent"

        elif score > 70:
            return "Good"

        elif score > 50:
            return "Average"

        elif score > 40:
            return "Below Average"

        else:
            return "Needs Improvement"

    overall["Performance_Category"] = (
        overall["Overall_Performance_Score"]
        .apply(performance_category)
    )

    # --------------------------------------------------------
    # PASS / FAIL
    # --------------------------------------------------------

    overall["Performance_Status"] = (
        overall["Overall_Performance_Score"]
        .apply(
            lambda score:
            "Pass"
            if score >= 40
            else "Fail"
        )
    )

    # --------------------------------------------------------
    # FINAL COLUMNS
    # --------------------------------------------------------

    preferred_columns = [
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Attendance_Percentage",
        "Assignment_Percentage",
        "Test_Percentage",
        "Attendance_Weight",
        "Assignment_Weight",
        "Test_Weight",
        "Overall_Performance_Score",
        "Performance_Category",
        "Performance_Status",
        "Certificate_Eligible"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in overall.columns
    ]

    # --------------------------------------------------------
    # FINAL CURRENT-STUDENT DATASET
    # --------------------------------------------------------

    overall = overall[
        final_columns
    ]

    overall.to_csv(
        ANALYSIS_DIR /
        "overall_performance_analysis.csv",
        index=False
    )

    print(
        "overall_performance_analysis.csv created."
    )


# ============================================================
# STUDENT RANKING
# ============================================================

def student_ranking_analysis():

    print("\n" + "=" * 60)
    print("STUDENT RANKING")
    print("=" * 60)

    df = pd.read_csv(
        ANALYSIS_DIR /
        "overall_performance_analysis.csv"
    )

    df = df.sort_values(
        by="Overall_Performance_Score",
        ascending=False
    ).reset_index(
        drop=True
    )

    df["Rank"] = range(
        1,
        len(df) + 1
    )

    preferred_columns = [
        "Rank",
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Attendance_Percentage",
        "Assignment_Percentage",
        "Test_Percentage",
        "Overall_Performance_Score",
        "Performance_Category",
        "Performance_Status",
        "Certificate_Eligible"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in df.columns
    ]

    df = df[
        final_columns
    ]

    df.to_csv(
        ANALYSIS_DIR /
        "student_performance_ranking.csv",
        index=False
    )

    print(
        "student_performance_ranking.csv created."
    )


# ============================================================
# PROGRAM PERFORMANCE SUMMARY
# ============================================================

def program_performance_summary():

    print("\n" + "=" * 60)
    print("PROGRAM PERFORMANCE SUMMARY")
    print("=" * 60)

    df = pd.read_csv(
        ANALYSIS_DIR /
        "overall_performance_analysis.csv"
    )

    program_summary = (
        df.groupby(
            [
                "Program_ID",
                "Program_Name"
            ]
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

            Average_Assignment_Performance=(
                "Assignment_Percentage",
                "mean"
            ),

            Average_Test_Performance=(
                "Test_Percentage",
                "mean"
            ),

            Average_Overall_Performance=(
                "Overall_Performance_Score",
                "mean"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # SEMESTER INFORMATION
    # --------------------------------------------------------

    semester_info = (
        df.groupby(
            "Program_ID"
        )["Semester_Name"]
        .apply(
            lambda x:
            ", ".join(
                sorted(
                    x.dropna()
                    .astype(str)
                    .unique()
                )
            )
        )
        .reset_index()
    )

    program_summary = program_summary.merge(
        semester_info,
        on="Program_ID",
        how="left"
    )

    # --------------------------------------------------------
    # ROUND VALUES
    # --------------------------------------------------------

    percentage_columns = [
        "Average_Attendance",
        "Average_Assignment_Performance",
        "Average_Test_Performance",
        "Average_Overall_Performance"
    ]

    program_summary[
        percentage_columns
    ] = program_summary[
        percentage_columns
    ].round(2)

    program_summary.to_csv(
        ANALYSIS_DIR /
        "program_performance_summary.csv",
        index=False
    )

    print(
        "program_performance_summary.csv created."
    )


# ============================================================
# SEMESTER PERFORMANCE SUMMARY
# ============================================================

def semester_performance_summary():

    print("\n" + "=" * 60)
    print("SEMESTER PERFORMANCE SUMMARY")
    print("=" * 60)

    df = pd.read_csv(
        ANALYSIS_DIR /
        "overall_performance_analysis.csv"
    )

    semester_summary = (
        df.groupby(
            [
                "Semester_ID",
                "Semester_Name"
            ]
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

            Average_Assignment_Performance=(
                "Assignment_Percentage",
                "mean"
            ),

            Average_Test_Performance=(
                "Test_Percentage",
                "mean"
            ),

            Average_Overall_Performance=(
                "Overall_Performance_Score",
                "mean"
            )
        )
        .reset_index()
    )

    percentage_columns = [
        "Average_Attendance",
        "Average_Assignment_Performance",
        "Average_Test_Performance",
        "Average_Overall_Performance"
    ]

    semester_summary[
        percentage_columns
    ] = semester_summary[
        percentage_columns
    ].round(2)

    semester_summary.to_csv(
        ANALYSIS_DIR /
        "semester_performance_summary.csv",
        index=False
    )

    print(
        "semester_performance_summary.csv created."
    )


# ============================================================
# POWER BI - STUDENT DATA
# ============================================================

def create_powerbi_student_data():

    print("\n" + "=" * 60)
    print("POWER BI STUDENT DATA")
    print("=" * 60)

    df = pd.read_csv(
        ANALYSIS_DIR /
        "student_performance_ranking.csv"
    )

    columns = [
        "Rank",
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Attendance_Percentage",
        "Assignment_Percentage",
        "Test_Percentage",
        "Overall_Performance_Score",
        "Performance_Category",
        "Performance_Status",
        "Certificate_Eligible"
    ]

    df = df[
        [
            column
            for column in columns
            if column in df.columns
        ]
    ]

    df.to_csv(
        POWERBI_DIR /
        "powerbi_student_performance.csv",
        index=False
    )

    print(
        "powerbi_student_performance.csv created."
    )


# ============================================================
# POWER BI - PROGRAM DATA
# ============================================================

def create_powerbi_program_data():

    print("\n" + "=" * 60)
    print("POWER BI PROGRAM DATA")
    print("=" * 60)

    df = pd.read_csv(
        ANALYSIS_DIR /
        "program_performance_summary.csv"
    )

    df.to_csv(
        POWERBI_DIR /
        "powerbi_program_performance.csv",
        index=False
    )

    print(
        "powerbi_program_performance.csv created."
    )


# ============================================================
# POWER BI - SEMESTER DATA
# ============================================================

def create_powerbi_semester_data():

    print("\n" + "=" * 60)
    print("POWER BI SEMESTER DATA")
    print("=" * 60)

    df = pd.read_csv(
        ANALYSIS_DIR /
        "semester_performance_summary.csv"
    )

    df.to_csv(
        POWERBI_DIR /
        "powerbi_semester_performance.csv",
        index=False
    )

    print(
        "powerbi_semester_performance.csv created."
    )


# ============================================================
# POWER BI - SUBJECT DATA
# ============================================================

def create_powerbi_subject_data():

    print("\n" + "=" * 60)
    print("POWER BI SUBJECT DATA")
    print("=" * 60)

    assignment_df = pd.read_csv(
        ANALYSIS_DIR /
        "assignment_analysis.csv"
    )

    test_df = pd.read_csv(
        ANALYSIS_DIR /
        "test_analysis.csv"
    )

    # --------------------------------------------------------
    # ASSIGNMENT SUBJECT SUMMARY
    # --------------------------------------------------------

    assignment_subject = (
        assignment_df.groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ]
        )["Assignment_Percentage"]
        .mean()
        .reset_index()
    )

    # --------------------------------------------------------
    # TEST SUBJECT SUMMARY
    # --------------------------------------------------------

    test_subject = (
        test_df.groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ]
        )["Test_Percentage"]
        .mean()
        .reset_index()
    )

    subject_df = assignment_subject.merge(
        test_subject,
        on=[
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ],
        how="outer"
    )

    subject_df[
        "Assignment_Percentage"
    ] = subject_df[
        "Assignment_Percentage"
    ].fillna(0)

    subject_df[
        "Test_Percentage"
    ] = subject_df[
        "Test_Percentage"
    ].fillna(0)

    subject_df["Assessment_Performance"] = (
        (
            subject_df["Assignment_Percentage"]
            * 0.30
        )
        +
        (
            subject_df["Test_Percentage"]
            * 0.70
        )
    ).round(2)

    # --------------------------------------------------------
    # ADD STUDENT INFORMATION
    # --------------------------------------------------------

    subject_df = subject_df.merge(
        student_info,
        on=[
            "Student_ID",
            "Semester_ID"
        ],
        how="left"
    )

    # --------------------------------------------------------
    # SUBJECT NAME
    # --------------------------------------------------------

    subjects_file = RAW_DIR / "subjects.csv"

    if subjects_file.exists():

        subjects = pd.read_csv(
            subjects_file
        )

        subject_columns = [
            column
            for column in [
                "Subject_ID",
                "Subject_Name",
                "Subject_Type"
            ]
            if column in subjects.columns
        ]

        subject_df = subject_df.merge(
            subjects[subject_columns].drop_duplicates(
                subset=["Subject_ID"]
            ),
            on="Subject_ID",
            how="left"
        )

    preferred_columns = [
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Name",
        "Subject_ID",
        "Subject_Name",
        "Subject_Type",
        "Assignment_Percentage",
        "Test_Percentage",
        "Assessment_Performance"
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in subject_df.columns
    ]

    subject_df = subject_df[
        final_columns
    ]

    subject_df.to_csv(
        POWERBI_DIR /
        "powerbi_subject_performance.csv",
        index=False
    )

    print(
        "powerbi_subject_performance.csv created."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    attendance_analysis()

    assignment_analysis()

    test_analysis()

    overall_performance_analysis()

    student_ranking_analysis()

    program_performance_summary()

    semester_performance_summary()

    create_powerbi_student_data()

    create_powerbi_program_data()

    create_powerbi_semester_data()

    create_powerbi_subject_data()

    print("\n" + "=" * 60)
    print("ALL ANALYSIS COMPLETED SUCCESSFULLY")
    print("=" * 60)

    print("\nPower BI files:")
    print(
        POWERBI_DIR /
        "powerbi_student_performance.csv"
    )

    print(
        POWERBI_DIR /
        "powerbi_program_performance.csv"
    )

    print(
        POWERBI_DIR /
        "powerbi_semester_performance.csv"
    )

    print(
        POWERBI_DIR /
        "powerbi_subject_performance.csv"
    )