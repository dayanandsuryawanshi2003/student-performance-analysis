"""
STUDENT PERFORMANCE SYSTEM - AUTOMATIC DATA PIPELINE

Purpose
-------
After Flask saves a change in MySQL, this pipeline:

1. Exports CURRENT application data from MySQL to data/raw/.
2. Runs the existing cleaning script.
3. Runs the existing current performance analysis.
4. Runs the existing student report analysis.
5. Runs the existing teacher-subject analysis.
6. Runs the existing dashboard2 analysis.

Historical raw files are NOT overwritten. They remain available for the
student historical-performance/journey analysis.

Run manually from project root:
    python auto_pipeline.py

From Flask:
    from auto_pipeline import run_pipeline
    run_pipeline()
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

from db import get_db_connection


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
CURRENT_RAW_DIR = RAW_DIR / "current"
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

RAW_DIR.mkdir(parents=True, exist_ok=True)
CURRENT_RAW_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SCRIPT PATHS
# ============================================================

CLEANING_SCRIPT = BASE_DIR / "cleaning" / "data_cleaning.py"
PERFORMANCE_SCRIPT = BASE_DIR / "analysis" / "performance_analysis.py"
STUDENT_SCRIPT = BASE_DIR / "analysis" / "analyze_student_report_FINAL.py"
TEACHER_SCRIPT = BASE_DIR / "analysis" / "teacher_subject_performance_analysis.py"
DASHBOARD2_SCRIPT = BASE_DIR / "analysis" / "dashboard2_analysis.py"
HISTORICAL_SCRIPT = BASE_DIR / "analysis" / "historical_analysis.py"


# ============================================================
# EXPORT HELPERS
# ============================================================

def export_query(cursor, query: str, output_file: Path) -> int:
    """Run a SELECT query and save its result as a CSV."""

    cursor.execute(query)
    rows = cursor.fetchall()

    if rows:
        df = pd.DataFrame(rows)
    else:
        # Get column names even when a query returns zero rows.
        columns = [column[0] for column in cursor.description]
        df = pd.DataFrame(columns=columns)

    df.to_csv(output_file, index=False, encoding="utf-8")

    print(f"[OK] {output_file.relative_to(BASE_DIR)} -> {len(df)} rows")
    return len(df)


def build_teacher_master(cursor) -> None:
    """
    Keep the existing teacher descriptive master and add any newly-created
    teachers from MySQL so the teacher analysis does not lose coverage.

    Existing descriptive data from teacher_master_FINAL.csv is preserved.
    """

    master_final = RAW_DIR / "teacher_master_FINAL.csv"
    master_output = RAW_DIR / "teacher_master.csv"

    if master_final.exists():
        master = pd.read_csv(master_final)
    elif master_output.exists():
        master = pd.read_csv(master_output)
    else:
        master = pd.DataFrame(
            columns=[
                "Teacher_ID",
                "Teacher_Code",
                "Teacher_Name",
                "Department",
            ]
        )

    # Read current Teacher IDs and usernames from MySQL.
    cursor.execute(
        """
        SELECT Teacher_ID, Username
        FROM Teacher
        ORDER BY Teacher_ID
        """
    )
    teachers = pd.DataFrame(cursor.fetchall())

    if teachers.empty:
        master.to_csv(master_output, index=False, encoding="utf-8")
        return

    if "Teacher_ID" not in master.columns:
        master = pd.DataFrame(
            columns=[
                "Teacher_ID",
                "Teacher_Code",
                "Teacher_Name",
                "Department",
            ]
        )

    for column in [
        "Teacher_ID",
        "Teacher_Code",
        "Teacher_Name",
        "Department",
    ]:
        if column not in master.columns:
            master[column] = ""

    master = master[
        ["Teacher_ID", "Teacher_Code", "Teacher_Name", "Department"]
    ].copy()

    master["Teacher_ID"] = pd.to_numeric(
        master["Teacher_ID"], errors="coerce"
    ).astype("Int64")

    existing_ids = set(master["Teacher_ID"].dropna().astype(int))

    new_rows = []

    for _, teacher in teachers.iterrows():
        teacher_id = int(teacher["Teacher_ID"])

        if teacher_id not in existing_ids:
            username = str(teacher["Username"])
            new_rows.append(
                {
                    "Teacher_ID": teacher_id,
                    "Teacher_Code": f"T{teacher_id:03d}",
                    "Teacher_Name": username,
                    "Department": "",
                }
            )

    if new_rows:
        master = pd.concat(
            [master, pd.DataFrame(new_rows)],
            ignore_index=True,
        )

    master = master.sort_values("Teacher_ID")
    master.to_csv(master_output, index=False, encoding="utf-8")

    print(
        f"[OK] data/raw/teacher_master.csv -> {len(master)} teachers"
    )


# ============================================================
# MYSQL -> CURRENT RAW CSV
# ============================================================

def export_current_mysql_data() -> None:
    """Export current MySQL data using the exact generated-raw-data schema."""

    print("\n" + "=" * 70)
    print("STEP 1 - EXPORT CURRENT MYSQL DATA")
    print("=" * 70)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        export_query(
            cursor,
            "SELECT * FROM Student ORDER BY Student_ID",
            CURRENT_RAW_DIR / "students.csv",
        )

        export_query(
            cursor,
            "SELECT * FROM Program ORDER BY Program_ID",
            RAW_DIR / "programs.csv",
        )

        export_query(
            cursor,
            """
            SELECT
                sem.Semester_ID,
                sem.Semester_Name,
                sem.Program_ID,
                CAST(SUBSTRING_INDEX(sem.Semester_Name, ' ', -1) AS UNSIGNED) AS Semester_Number
            FROM Semester sem
            INNER JOIN (
                SELECT DISTINCT Program_ID, Semester_ID
                FROM Student
                WHERE Semester_ID IS NOT NULL
            ) current_sem
                ON sem.Program_ID = current_sem.Program_ID
                AND sem.Semester_ID = current_sem.Semester_ID
            ORDER BY sem.Program_ID, sem.Semester_ID
            """,
            RAW_DIR / "semesters.csv",
        )

        export_query(
            cursor,
            """
            SELECT
                sub.Subject_ID,
                sub.Subject_Name,
                sub.Subject_Code,
                sub.Subject_Type,
                sub.Program_ID,
                sub.Semester_ID
            FROM Subject sub
            INNER JOIN (
                SELECT DISTINCT Program_ID, Semester_ID
                FROM Student
                WHERE Semester_ID IS NOT NULL
            ) current_sem
                ON sub.Program_ID = current_sem.Program_ID
                AND sub.Semester_ID = current_sem.Semester_ID
            ORDER BY sub.Subject_ID
            """,
            CURRENT_RAW_DIR / "subjects.csv",
        )

        export_query(
            cursor,
            """
            SELECT ss.Student_ID, ss.Subject_ID, ss.Semester_ID
            FROM Student_Subject ss
            INNER JOIN Student s
                ON ss.Student_ID = s.Student_ID
                AND ss.Semester_ID = s.Semester_ID
            INNER JOIN Subject sub
                ON ss.Subject_ID = sub.Subject_ID
                AND ss.Semester_ID = sub.Semester_ID
                AND s.Program_ID = sub.Program_ID
            WHERE s.Semester_ID IS NOT NULL
            ORDER BY ss.Student_ID, ss.Subject_ID
            """,
            CURRENT_RAW_DIR / "student_subject.csv",
        )

        # Generated raw schema: Status is numeric (1=Present, 0=Absent).
        export_query(
            cursor,
            """
            SELECT
                Student_ID,
                Subject_ID,
                Attendance_Date,
                CASE WHEN Attendance_Status = 'Present' THEN 1 ELSE 0 END AS Status,
                1 AS Total_Classes,
                Semester_ID
            FROM Attendance
            WHERE Student_ID IN (SELECT Student_ID FROM Student)
            ORDER BY Attendance_ID
            """,
            CURRENT_RAW_DIR / "attendance.csv",
        )

        export_query(
            cursor,
            """
            SELECT
                pa.Student_ID,
                pa.Subject_ID,
                pa.Attendance_Date,
                pa.Status,
                1 AS Total_Classes,
                pa.Semester_ID
            FROM Practical_Attendance pa
            INNER JOIN Student s
                ON pa.Student_ID = s.Student_ID
                AND pa.Semester_ID = s.Semester_ID
            WHERE s.Semester_ID IS NOT NULL
            ORDER BY pa.Practical_Attendance_ID
            """,
            CURRENT_RAW_DIR / "practical_attendance.csv",
        )

        export_query(
            cursor,
            """
            SELECT
                a.Student_ID,
                a.Subject_ID,
                a.Assignment_No,
                a.Marks,
                20 AS Max_Marks,
                a.Semester_ID
            FROM Assignment a
            INNER JOIN Student s
                ON a.Student_ID = s.Student_ID
                AND a.Semester_ID = s.Semester_ID
            WHERE s.Semester_ID IS NOT NULL
            ORDER BY a.Assignment_ID
            """,
            CURRENT_RAW_DIR / "assignments.csv",
        )

        export_query(
            cursor,
            """
            SELECT
                t.Student_ID,
                t.Subject_ID,
                t.Test_No,
                t.Marks,
                20 AS Max_Marks,
                t.Semester_ID
            FROM Test t
            INNER JOIN Student s
                ON t.Student_ID = s.Student_ID
                AND t.Semester_ID = s.Semester_ID
            WHERE s.Semester_ID IS NOT NULL
            ORDER BY t.Test_ID
            """,
            CURRENT_RAW_DIR / "tests.csv",
        )

        export_query(
            cursor,
            """
            SELECT Student_ID, Subject_ID, Marks, 20 AS Max_Marks, Semester_ID
            FROM Semester_Result
            WHERE Student_ID IN (SELECT Student_ID FROM Student)
            ORDER BY Result_ID
            """,
            CURRENT_RAW_DIR / "semester_results.csv",
        )

        export_query(
            cursor,
            """
            SELECT
                ts.Teacher_ID,
                ts.Subject_ID,
                ts.Semester_ID,
                sub.Program_ID AS Program_ID
            FROM Teacher_Subject ts
            INNER JOIN Subject sub
                ON ts.Subject_ID = sub.Subject_ID
                AND ts.Semester_ID = sub.Semester_ID
            INNER JOIN (
                SELECT DISTINCT Program_ID, Semester_ID
                FROM Student
                WHERE Semester_ID IS NOT NULL
            ) current_sem
                ON sub.Program_ID = current_sem.Program_ID
                AND ts.Semester_ID = current_sem.Semester_ID
            ORDER BY ts.Teacher_ID, ts.Subject_ID, ts.Semester_ID
            """,
            CURRENT_RAW_DIR / "teacher_subject.csv",
        )

        build_teacher_master(cursor)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# RUN EXISTING SCRIPT
# ============================================================

def run_script(script_path: Path, label: str) -> None:
    """Run one existing project script and stop if it fails."""

    if not script_path.exists():
        raise FileNotFoundError(
            f"Required script not found for {label}: {script_path}"
        )

    print("\n" + "=" * 70)
    print(f"STEP - {label}")
    print("=" * 70)
    print(f"Running: {script_path.relative_to(BASE_DIR)}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=BASE_DIR,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{label} failed with exit code {result.returncode}."
        )

    print(f"[OK] {label} completed")


# ============================================================
# PUBLIC PIPELINE FUNCTION
# ============================================================

def run_pipeline() -> bool:
    """
    Run the complete automatic pipeline.

    Returns True only when every step succeeds.
    """

    print("\n" + "#" * 70)
    print(" STUDENT PERFORMANCE SYSTEM - AUTOMATIC PIPELINE")
    print("#" * 70)

    export_current_mysql_data()

    run_script(
        CLEANING_SCRIPT,
        "CURRENT DATA CLEANING",
    )

    run_script(
        PERFORMANCE_SCRIPT,
        "CURRENT PERFORMANCE ANALYSIS",
    )

    # This script also uses the existing historical Sem-1/Sem-2 raw files.
    # Those files are intentionally preserved by this pipeline.
    run_script(
        STUDENT_SCRIPT,
        "STUDENT REPORT ANALYSIS",
    )

    run_script(
        TEACHER_SCRIPT,
        "TEACHER-SUBJECT PERFORMANCE ANALYSIS",
    )

    # Historical analysis creates only historical outputs.
    # Dashboard 2 is intentionally the final analysis step so its CSV files
    # cannot be overwritten by another analysis script.
    run_script(
        HISTORICAL_SCRIPT,
        "HISTORICAL ANALYSIS",
    )

    run_script(
        DASHBOARD2_SCRIPT,
        "DASHBOARD 2 ANALYSIS",
    )

    print("\n" + "#" * 70)
    print(" AUTOMATIC PIPELINE COMPLETED SUCCESSFULLY")
    print("#" * 70)
    print("\nUpdated outputs are ready for Power BI refresh.")

    return True


# ============================================================
# FLASK-SAFE WRAPPER
# ============================================================

def run_pipeline_safe() -> bool:
    """
    Run the pipeline without breaking the Flask request if analysis fails.

    The database transaction has already been committed before Flask calls
    this function. Therefore a pipeline failure does not undo the database
    change; it is printed clearly so it can be fixed/re-run.
    """

    try:
        return run_pipeline()
    except Exception as exc:
        print("\n" + "!" * 70)
        print(" AUTOMATIC PIPELINE FAILED")
        print("!" * 70)
        print(f"ERROR: {exc}")
        print("Database changes were already committed.")
        print("Run: python auto_pipeline.py to retry the analysis pipeline.")
        print("!" * 70)
        return False


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        print("\nPIPELINE FAILED:")
        print(exc)
        sys.exit(1)
