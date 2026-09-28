import pandas as pd
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CLEANED_DIR = BASE_DIR / "data" / "cleaned"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

SEM1_FOLDER = CLEANED_DIR / "historical_sem1"
SEM2_FOLDER = CLEANED_DIR / "historical_sem2"

ANALYSIS_SEM1 = ANALYSIS_DIR / "historical_sem1"
ANALYSIS_SEM2 = ANALYSIS_DIR / "historical_sem2"
ANALYSIS_DASHBOARD2 = ANALYSIS_DIR / "dashboard2"

ANALYSIS_SEM1.mkdir(parents=True, exist_ok=True)
ANALYSIS_SEM2.mkdir(parents=True, exist_ok=True)
ANALYSIS_DASHBOARD2.mkdir(parents=True, exist_ok=True)


# ============================================================
# ANALYSIS CONFIGURATION
# ============================================================

ASSIGNMENT_MAX_MARKS = 20
TEST_MAX_MARKS = 20

ATTENDANCE_WEIGHT = 0.30
ASSIGNMENT_WEIGHT = 0.30
TEST_WEIGHT = 0.40


# ============================================================
# FILE LOADER
# ============================================================

def read_cleaned_csv(folder, filename):

    file_path = folder / filename

    if not file_path.exists():

        raise FileNotFoundError(
            f"\nRequired file not found:\n{file_path}"
        )

    print(f"Reading: {file_path}")

    return pd.read_csv(file_path)


# ============================================================
# PERFORMANCE CATEGORY
# ============================================================

def get_performance_category(score):

    if score >= 85:
        return "Excellent"

    elif score >= 70:
        return "Good"

    elif score >= 50:
        return "Average"

    else:
        return "Needs Improvement"


# ============================================================
# SUBJECT-LEVEL PERFORMANCE
# ============================================================

def calculate_subject_performance(
    attendance_df,
    assignment_df,
    test_df,
    subjects_df,
    students_df
):

    # --------------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------------

    attendance_df = attendance_df.copy()

    attendance_df["Attendance_Status"] = (
        attendance_df["Attendance_Status"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    attendance_grouped = (
        attendance_df
        .groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ],
            as_index=False
        )
        .agg(
            Total_Classes=(
                "Attendance_Status",
                "count"
            ),
            Present_Classes=(
                "Attendance_Status",
                lambda x: (x == "Present").sum()
            )
        )
    )

    attendance_grouped["Attendance_Percentage"] = (
        attendance_grouped["Present_Classes"]
        / attendance_grouped["Total_Classes"].replace(0, pd.NA)
        * 100
    ).fillna(0)


    # --------------------------------------------------------
    # ASSIGNMENTS
    # --------------------------------------------------------

    assignment_df = assignment_df.copy()

    assignment_df["Marks"] = pd.to_numeric(
        assignment_df["Marks"],
        errors="coerce"
    ).fillna(0)

    assignment_df["Marks"] = assignment_df["Marks"].clip(
        lower=0,
        upper=ASSIGNMENT_MAX_MARKS
    )

    assignment_grouped = (
        assignment_df
        .groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ],
            as_index=False
        )
        .agg(
            Assignment_Obtained=(
                "Marks",
                "sum"
            ),
            Assignment_Count=(
                "Marks",
                "count"
            )
        )
    )

    assignment_grouped["Assignment_Max"] = (
        assignment_grouped["Assignment_Count"]
        * ASSIGNMENT_MAX_MARKS
    )

    assignment_grouped["Assignment_Percentage"] = (
        assignment_grouped["Assignment_Obtained"]
        / assignment_grouped["Assignment_Max"].replace(0, pd.NA)
        * 100
    ).fillna(0)


    # --------------------------------------------------------
    # TESTS
    # --------------------------------------------------------

    test_df = test_df.copy()

    test_df["Marks"] = pd.to_numeric(
        test_df["Marks"],
        errors="coerce"
    ).fillna(0)

    test_df["Marks"] = test_df["Marks"].clip(
        lower=0,
        upper=TEST_MAX_MARKS
    )

    test_grouped = (
        test_df
        .groupby(
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID"
            ],
            as_index=False
        )
        .agg(
            Test_Obtained=(
                "Marks",
                "sum"
            ),
            Test_Count=(
                "Marks",
                "count"
            )
        )
    )

    test_grouped["Test_Max"] = (
        test_grouped["Test_Count"]
        * TEST_MAX_MARKS
    )

    test_grouped["Test_Percentage"] = (
        test_grouped["Test_Obtained"]
        / test_grouped["Test_Max"].replace(0, pd.NA)
        * 100
    ).fillna(0)


    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    performance = pd.merge(
        attendance_grouped,
        assignment_grouped,
        on=[
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ],
        how="outer"
    )

    performance = pd.merge(
        performance,
        test_grouped,
        on=[
            "Student_ID",
            "Subject_ID",
            "Semester_ID"
        ],
        how="outer"
    )


    # --------------------------------------------------------
    # MISSING VALUES
    # --------------------------------------------------------

    performance["Attendance_Percentage"] = (
        performance["Attendance_Percentage"]
        .fillna(0)
    )

    performance["Assignment_Percentage"] = (
        performance["Assignment_Percentage"]
        .fillna(0)
    )

    performance["Test_Percentage"] = (
        performance["Test_Percentage"]
        .fillna(0)
    )


    # --------------------------------------------------------
    # OVERALL PERFORMANCE
    # --------------------------------------------------------

    performance["Overall_Performance_Score"] = (
        performance["Attendance_Percentage"]
        * ATTENDANCE_WEIGHT
        +
        performance["Assignment_Percentage"]
        * ASSIGNMENT_WEIGHT
        +
        performance["Test_Percentage"]
        * TEST_WEIGHT
    ).round(2)


    # --------------------------------------------------------
    # ADD SUBJECT INFORMATION
    # --------------------------------------------------------

    subject_columns = [
        "Subject_ID",
        "Program_ID",
        "Semester_ID",
        "Subject_Code",
        "Subject_Name",
        "Subject_Type"
    ]

    available_subject_columns = [
        column
        for column in subject_columns
        if column in subjects_df.columns
    ]

    subject_master = (
        subjects_df[
            available_subject_columns
        ]
        .drop_duplicates(
            subset=["Subject_ID"]
        )
    )

    performance = performance.merge(
        subject_master,
        on="Subject_ID",
        how="left",
        suffixes=("", "_Subject")
    )


    # --------------------------------------------------------
    # ADD STUDENT INFORMATION
    # --------------------------------------------------------

    student_columns = [
        "Student_ID",
        "Roll_No",
        "Name",
        "Department_ID",
        "Program_ID"
    ]

    available_student_columns = [
        column
        for column in student_columns
        if column in students_df.columns
    ]

    student_master = (
        students_df[
            available_student_columns
        ]
        .drop_duplicates(
            subset=["Student_ID"]
        )
    )

    performance = performance.merge(
        student_master,
        on="Student_ID",
        how="left",
        suffixes=("", "_Student")
    )


    # --------------------------------------------------------
    # PROGRAM NAME
    #
    # Prefer Program_Name already present in subject/student
    # data. No hard-coded Program_ID mapping.
    # --------------------------------------------------------

    if "Program_Name" not in performance.columns:

        if "Program_Name" in subjects_df.columns:

            program_master = (
                subjects_df[
                    ["Program_ID", "Program_Name"]
                ]
                .drop_duplicates(
                    subset=["Program_ID"]
                )
            )

            performance = performance.merge(
                program_master,
                on="Program_ID",
                how="left"
            )

        else:

            performance["Program_Name"] = (
                performance["Program_ID"]
                .astype("string")
            )


    # --------------------------------------------------------
    # SEMESTER NUMBER
    #
    # If Semester_Number is already available, use it.
    # Otherwise derive it from Semester_Name only.
    # --------------------------------------------------------

    if "Semester_Number" not in performance.columns:

        if "Semester_Name" in performance.columns:

            performance["Semester_Number"] = (
                performance["Semester_Name"]
                .astype("string")
                .str.extract(r"(\d+)", expand=False)
            )

            performance["Semester_Number"] = pd.to_numeric(
                performance["Semester_Number"],
                errors="coerce"
            )

        else:

            performance["Semester_Number"] = pd.NA


    # --------------------------------------------------------
    # SEMESTER NAME
    # --------------------------------------------------------

    if "Semester_Name" not in performance.columns:

        performance["Semester_Name"] = (
            "Semester "
            + performance["Semester_Number"]
            .astype("Int64")
            .astype("string")
        )


    # --------------------------------------------------------
    # PERFORMANCE CATEGORY
    # --------------------------------------------------------

    performance["Performance_Category"] = (
        performance["Overall_Performance_Score"]
        .apply(get_performance_category)
    )


    # --------------------------------------------------------
    # ROUND
    # --------------------------------------------------------

    numeric_columns = [
        "Attendance_Percentage",
        "Assignment_Percentage",
        "Test_Percentage",
        "Overall_Performance_Score"
    ]

    for column in numeric_columns:

        if column in performance.columns:

            performance[column] = (
                performance[column]
                .round(2)
            )


    return performance


# ============================================================
# STUDENT-LEVEL PERFORMANCE
# ============================================================

def calculate_student_performance(subject_performance):

    grouping_columns = [
        "Student_ID",
        "Program_ID",
        "Program_Name",
        "Semester_ID",
        "Semester_Number"
    ]

    grouping_columns = [
        column
        for column in grouping_columns
        if column in subject_performance.columns
    ]

    student_performance = (
        subject_performance
        .groupby(
            grouping_columns,
            as_index=False
        )
        .agg(
            Attendance_Percentage=(
                "Attendance_Percentage",
                "mean"
            ),
            Assignment_Percentage=(
                "Assignment_Percentage",
                "mean"
            ),
            Test_Percentage=(
                "Test_Percentage",
                "mean"
            ),
            Overall_Performance_Score=(
                "Overall_Performance_Score",
                "mean"
            )
        )
    )

    student_performance["Performance_Category"] = (
        student_performance[
            "Overall_Performance_Score"
        ]
        .apply(get_performance_category)
    )

    numeric_columns = [
        "Attendance_Percentage",
        "Assignment_Percentage",
        "Test_Percentage",
        "Overall_Performance_Score"
    ]

    for column in numeric_columns:

        student_performance[column] = (
            student_performance[column]
            .round(2)
        )


    # --------------------------------------------------------
    # RANK WITHIN PROGRAM + SEMESTER
    # --------------------------------------------------------

    rank_group = [
        column
        for column in [
            "Program_ID",
            "Semester_ID"
        ]
        if column in student_performance.columns
    ]

    if rank_group:

        student_performance["Rank"] = (
            student_performance
            .groupby(rank_group)[
                "Overall_Performance_Score"
            ]
            .rank(
                method="dense",
                ascending=False
            )
            .astype(int)
        )

    else:

        student_performance["Rank"] = (
            student_performance[
                "Overall_Performance_Score"
            ]
            .rank(
                method="dense",
                ascending=False
            )
            .astype(int)
        )


    student_performance = (
        student_performance
        .sort_values(
            [
                column
                for column in [
                    "Program_ID",
                    "Semester_Number",
                    "Rank"
                ]
                if column in student_performance.columns
            ]
        )
        .reset_index(drop=True)
    )

    return student_performance


# ============================================================
# PROGRAM + SEMESTER SUMMARY
# ============================================================

def create_program_semester_summary(
    student_sem1,
    student_sem2
):

    combined = pd.concat(
        [
            student_sem1,
            student_sem2
        ],
        ignore_index=True
    )

    summary = (
        combined
        .groupby(
            [
                "Program_ID",
                "Program_Name",
                "Semester_Number"
            ],
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
    )

    numeric_columns = [
        "Average_Attendance",
        "Average_Assignment_Performance",
        "Average_Test_Performance",
        "Average_Overall_Performance"
    ]

    summary[numeric_columns] = (
        summary[numeric_columns].round(2)
    )

    summary["Semester_Name"] = (
        "Semester "
        + summary["Semester_Number"]
        .astype("Int64")
        .astype("string")
    )

    summary = (
        summary
        .sort_values(
            [
                "Program_ID",
                "Semester_Number"
            ]
        )
        .reset_index(drop=True)
    )

    return summary


# ============================================================
# PERFORMANCE CATEGORY SUMMARY
# ============================================================

def create_category_summary(
    student_sem1,
    student_sem2
):

    combined = pd.concat(
        [
            student_sem1,
            student_sem2
        ],
        ignore_index=True
    )

    category_summary = (
        combined
        .groupby(
            [
                "Program_Name",
                "Semester_Number",
                "Performance_Category"
            ],
            as_index=False
        )
        .agg(
            Student_Count=(
                "Student_ID",
                "nunique"
            )
        )
    )

    category_summary["Semester_Name"] = (
        "Semester "
        + category_summary["Semester_Number"]
        .astype("Int64")
        .astype("string")
    )

    return category_summary


# ============================================================
# ANALYZE ONE HISTORICAL SEMESTER
# ============================================================

def analyze_semester(
    folder,
    output_folder,
    semester_label
):

    print("\n")
    print("=" * 70)
    print(semester_label)
    print("=" * 70)

    students_df = read_cleaned_csv(
        folder,
        "students_cleaned.csv"
    )

    subjects_df = read_cleaned_csv(
        folder,
        "subjects_cleaned.csv"
    )

    attendance_df = read_cleaned_csv(
        folder,
        "attendance_cleaned.csv"
    )

    assignments_df = read_cleaned_csv(
        folder,
        "assignments_cleaned.csv"
    )

    tests_df = read_cleaned_csv(
        folder,
        "tests_cleaned.csv"
    )

    subject_performance = calculate_subject_performance(
        attendance_df,
        assignments_df,
        tests_df,
        subjects_df,
        students_df
    )

    student_performance = calculate_student_performance(
        subject_performance
    )

    subject_output = (
        output_folder
        / f"{folder.name}_subject_performance.csv"
    )

    student_output = (
        output_folder
        / f"{folder.name}_student_performance.csv"
    )

    subject_performance.to_csv(
        subject_output,
        index=False
    )

    student_performance.to_csv(
        student_output,
        index=False
    )

    print(f"\nCreated: {subject_output}")
    print(f"Created: {student_output}")

    return (
        subject_performance,
        student_performance
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("HISTORICAL DATA ANALYSIS")
    print("=" * 70)


    # ========================================================
    # HISTORICAL SEMESTER 1
    # ========================================================

    (
        sem1_subject_performance,
        sem1_student_performance
    ) = analyze_semester(
        SEM1_FOLDER,
        ANALYSIS_SEM1,
        "HISTORICAL SEMESTER 1"
    )


    # ========================================================
    # HISTORICAL SEMESTER 2
    # ========================================================

    (
        sem2_subject_performance,
        sem2_student_performance
    ) = analyze_semester(
        SEM2_FOLDER,
        ANALYSIS_SEM2,
        "HISTORICAL SEMESTER 2"
    )


    # ========================================================
    # DASHBOARD 2 OUTPUTS
    # ========================================================
    # Dashboard 2 is generated exclusively by dashboard2_analysis.py.
    # This script intentionally does NOT write any dashboard2_* file.
    # This prevents historical analysis from overwriting the Power BI
    # dashboard2_student_performance.csv schema.

    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print("\n")
    print("=" * 70)
    print("HISTORICAL ANALYSIS COMPLETED SUCCESSFULLY")
    print("=" * 70)

    print("\nGenerated files:")

    print("\nHistorical Semester 1:")
    print(" - historical_sem1_subject_performance.csv")
    print(" - historical_sem1_student_performance.csv")

    print("\nHistorical Semester 2:")
    print(" - historical_sem2_subject_performance.csv")
    print(" - historical_sem2_student_performance.csv")

    print("\nDashboard 2:")
    print(" - Generated separately by dashboard2_analysis.py")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()