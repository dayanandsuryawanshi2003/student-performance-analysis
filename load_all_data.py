"""
STUDENT PERFORMANCE SYSTEM - MASTER DATA LOADER

Run from the project folder:
    python load_all_data_updated.py

Expected raw-data structure:
    data/raw/
        admin.csv
        departments.csv
        programs.csv
        semesters.csv
        subject_master.csv
        teacher_master_FINAL.csv
        teachers_FINAL.csv

        current/
            students.csv
            subjects.csv
            student_subject.csv
            attendance.csv
            practical_attendance.csv
            assignments.csv
            tests.csv
            semester_results.csv
            teacher_subject.csv

        historical_sem1/
            students.csv
            subjects.csv
            student_subject.csv
            attendance.csv
            practical_attendance.csv
            assignments.csv
            tests.csv
            semester_results.csv

        historical_sem2/
            students.csv
            subjects.csv
            student_subject.csv
            attendance.csv
            practical_attendance.csv
            assignments.csv
            tests.csv
            semester_results.csv

Important:
    - Root-level duplicate data files are NOT used.
    - Current students are loaded only from current/students.csv.
    - Historical students.csv files are intentionally NOT inserted into Student,
      because Student stores the student's current semester.
    - Historical subject/activity/result records ARE loaded.
    - Existing project data is cleared before the fresh load.
    - The database should be backed up before running this script.
"""

import csv
import sys
from pathlib import Path

try:
    import mysql.connector
except ImportError:
    print("ERROR: mysql-connector-python is not installed.")
    print("Run: pip install mysql-connector-python")
    sys.exit(1)

try:
    from werkzeug.security import generate_password_hash
except ImportError:
    print("ERROR: Werkzeug is not installed.")
    print("Run: pip install werkzeug")
    sys.exit(1)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "student_performance_app",
    "password": "StudentApp@123",
    "database": "student_performance_db",
}

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "raw"

CURRENT_DIR = DATA_DIR / "current"
HIST_SEM1_DIR = DATA_DIR / "historical_sem1"
HIST_SEM2_DIR = DATA_DIR / "historical_sem2"


# ============================================================
# FILE HELPERS
# ============================================================
def read_csv(folder, filename, required=True):
    path = folder / filename

    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing CSV: {path}")
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def val(row, key):
    value = row.get(key)
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def integer(value):
    if value is None:
        return None
    value = str(value).strip()
    return int(value) if value else None


def num(value):
    if value is None:
        return None
    value = str(value).strip()
    return float(value) if value else None


def require_structure():
    required_dirs = [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]
    for folder in required_dirs:
        if not folder.exists():
            raise FileNotFoundError(f"Required data folder not found: {folder}")

    required_root = [
        "departments.csv",
        "programs.csv",
        "semesters.csv",
        "admin.csv",
        "teachers_FINAL.csv",
    ]

    for filename in required_root:
        if not (DATA_DIR / filename).exists():
            raise FileNotFoundError(f"Missing root master file: {DATA_DIR / filename}")

    current_required = [
        "students.csv",
        "subjects.csv",
        "student_subject.csv",
        "attendance.csv",
        "assignments.csv",
        "tests.csv",
        "semester_results.csv",
        "teacher_subject.csv",
    ]

    historical_required = [
        "subjects.csv",
        "student_subject.csv",
        "attendance.csv",
        "assignments.csv",
        "tests.csv",
        "semester_results.csv",
    ]

    for filename in current_required:
        if not (CURRENT_DIR / filename).exists():
            raise FileNotFoundError(f"Missing current CSV: {CURRENT_DIR / filename}")

    for folder in [HIST_SEM1_DIR, HIST_SEM2_DIR]:
        for filename in historical_required:
            if not (folder / filename).exists():
                raise FileNotFoundError(f"Missing historical CSV: {folder / filename}")

    print(f"[OK] Raw data root: {DATA_DIR}")
    print("[OK] Using ONLY current/, historical_sem1/ and historical_sem2/ data folders.")


# ============================================================
# DATABASE HELPERS
# ============================================================
def table_exists(cursor, table):
    cursor.execute("SHOW TABLES")
    return table.lower() in {row[0].lower() for row in cursor.fetchall()}


def table_columns(cursor, table):
    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
    return {row[0] for row in cursor.fetchall()}


def insert_ignore(cursor, table, columns, rows):
    if not rows:
        return 0

    cols = ", ".join(f"`{c}`" for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT IGNORE INTO `{table}` ({cols}) VALUES ({placeholders})"
    cursor.executemany(sql, rows)
    return len(rows)


def count_rows(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
    return cursor.fetchone()[0]


# ============================================================
# FULL DATA RESET
# ============================================================
def clear_project_data(cursor):
    """
    Clear all project tables so old dummy data cannot mix with the
    newly generated dataset.

    This does NOT drop tables or change the database schema.
    """
    clear_order = [
        "Performance_Analysis",
        "Recommendation",
        "Semester_Result",
        "Practical_Attendance",
        "Attendance",
        "Assignment",
        "Test",
        "Student_Subject",
        "Teacher_Subject",
        "Student",
        "Subject",
        "Teacher",
        "Admin",
        "Career_Domain",
        "Semester",
        "Program",
        "Department",
    ]

    print()
    print("=" * 70)
    print("CLEARING OLD PROJECT DATA")
    print("=" * 70)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    for table in clear_order:
        if table_exists(cursor, table):
            cursor.execute(f"DELETE FROM `{table}`")
            print(f"[CLEARED] {table}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("[OK] Old project data cleared. Tables/schema were not dropped.")


# ============================================================
# MAIN
# ============================================================
def main():
    require_structure()

    conn = None
    cursor = None

    try:
        print()
        print("=" * 70)
        print("STUDENT PERFORMANCE SYSTEM - FRESH DATA LOADER")
        print("=" * 70)

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[OK] MySQL connected")
        print(f"[OK] Database: {DB_CONFIG['database']}")

        required_tables = [
            "Department",
            "Program",
            "Semester",
            "Student",
            "Subject",
            "Student_Subject",
            "Teacher",
            "Teacher_Subject",
            "Attendance",
            "Practical_Attendance",
            "Assignment",
            "Test",
            "Semester_Result",
            "Admin",
        ]

        missing = [t for t in required_tables if not table_exists(cursor, t)]
        if missing:
            raise RuntimeError(
                "Required table(s) missing: " + ", ".join(missing)
            )

        # --------------------------------------------------------
        # 1. CLEAR OLD DATA
        # --------------------------------------------------------
        clear_project_data(cursor)

        # --------------------------------------------------------
        # 2. DEPARTMENT
        # --------------------------------------------------------
        rows = read_csv(DATA_DIR, "departments.csv")
        data = [
            (integer(r["Department_ID"]), val(r, "Department_Name"))
            for r in rows
        ]
        insert_ignore(cursor, "Department",
                      ["Department_ID", "Department_Name"], data)
        print(f"[OK] Department: {len(data)}")

        # --------------------------------------------------------
        # 3. PROGRAM
        # --------------------------------------------------------
        rows = read_csv(DATA_DIR, "programs.csv")
        data = [
            (
                integer(r["Program_ID"]),
                val(r, "Program_Name"),
                integer(r["Department_ID"]),
            )
            for r in rows
        ]
        insert_ignore(
            cursor,
            "Program",
            ["Program_ID", "Program_Name", "Department_ID"],
            data,
        )
        print(f"[OK] Program: {len(data)}")

        # --------------------------------------------------------
        # 4. SEMESTER
        #    Current + historical semester IDs are merged.
        # --------------------------------------------------------
        semester_map = {}

        semester_sources = [
            (DATA_DIR, "semesters.csv"),
            (CURRENT_DIR, "subjects.csv"),
            (HIST_SEM1_DIR, "subjects.csv"),
            (HIST_SEM2_DIR, "subjects.csv"),
        ]

        for folder, filename in semester_sources:
            rows = read_csv(folder, filename)
            if filename == "semesters.csv":
                for r in rows:
                    sid = integer(r["Semester_ID"])
                    value = (
                        sid,
                        val(r, "Semester_Name"),
                        integer(r["Program_ID"]),
                    )
                    old = semester_map.get(sid)
                    if old and old != value:
                        raise RuntimeError(
                            f"Conflicting Semester_ID definition: {sid}"
                        )
                    semester_map[sid] = value
            else:
                for r in rows:
                    sid = integer(r["Semester_ID"])
                    value = (
                        sid,
                        f"Semester {sid}",
                        integer(r["Program_ID"]),
                    )
                    semester_map.setdefault(sid, value)

        data = list(semester_map.values())
        insert_ignore(
            cursor,
            "Semester",
            ["Semester_ID", "Semester_Name", "Program_ID"],
            data,
        )
        print(f"[OK] Semester: {len(data)}")

        # --------------------------------------------------------
        # 5. CURRENT STUDENTS ONLY
        # --------------------------------------------------------
        rows = read_csv(CURRENT_DIR, "students.csv")
        data = []

        for r in rows:
            raw_password = val(r, "Password")
            password_hash = (
                generate_password_hash(raw_password)
                if raw_password else None
            )

            data.append((
                integer(r["Student_ID"]),
                val(r, "Roll_No"),
                val(r, "Name"),
                val(r, "Gender"),
                integer(r["Department_ID"]),
                integer(r["Semester_ID"]),
                integer(r["Program_ID"]),
                password_hash,
            ))

        insert_ignore(
            cursor,
            "Student",
            [
                "Student_ID",
                "Roll_No",
                "Name",
                "Gender",
                "Department_ID",
                "Semester_ID",
                "Program_ID",
                "Password",
            ],
            data,
        )
        print(f"[OK] Student (current only): {len(data)}")

        # --------------------------------------------------------
        # 6. SUBJECTS
        #    Current + historical subject records.
        # --------------------------------------------------------
        subject_map = {}

        for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
            rows = read_csv(folder, "subjects.csv")

            for r in rows:
                sid = integer(r["Subject_ID"])
                value = (
                    sid,
                    val(r, "Subject_Code"),
                    val(r, "Subject_Name"),
                    val(r, "Subject_Type"),
                    integer(r["Program_ID"]),
                    integer(r["Semester_ID"]),
                )

                old = subject_map.get(sid)
                if old and old != value:
                    raise RuntimeError(
                        f"Conflicting Subject_ID definition: {sid}"
                    )

                subject_map[sid] = value

        data = list(subject_map.values())

        insert_ignore(
            cursor,
            "Subject",
            [
                "Subject_ID",
                "Subject_Code",
                "Subject_Name",
                "Subject_Type",
                "Program_ID",
                "Semester_ID",
            ],
            data,
        )
        print(f"[OK] Subject: {len(data)}")

        # --------------------------------------------------------
        # 7. TEACHER
        # --------------------------------------------------------
        rows = read_csv(DATA_DIR, "teachers_FINAL.csv")
        data = []

        for r in rows:
            raw_password = val(r, "Password")
            password_hash = (
                generate_password_hash(raw_password)
                if raw_password else None
            )

            data.append((
                integer(r["Teacher_ID"]),
                val(r, "Username"),
                password_hash,
            ))

        insert_ignore(
            cursor,
            "Teacher",
            ["Teacher_ID", "Username", "Password"],
            data,
        )
        print(f"[OK] Teacher: {len(data)}")

        # --------------------------------------------------------
        # 8. TEACHER_SUBJECT
        #    Current allocation only.
        # --------------------------------------------------------
        ts_columns = table_columns(cursor, "Teacher_Subject")

        if not {"Teacher_ID", "Subject_ID", "Semester_ID"}.issubset(ts_columns):
            raise RuntimeError(
                "Teacher_Subject must contain Teacher_ID, Subject_ID and Semester_ID."
            )

        rows = read_csv(CURRENT_DIR, "teacher_subject.csv")
        data = []

        for r in rows:
            base = [
                integer(r["Teacher_ID"]),
                integer(r["Subject_ID"]),
                integer(r["Semester_ID"]),
            ]

            if "Program_ID" in ts_columns:
                base.append(integer(r["Program_ID"]))

            data.append(tuple(base))

        ts_insert_cols = ["Teacher_ID", "Subject_ID", "Semester_ID"]
        if "Program_ID" in ts_columns:
            ts_insert_cols.append("Program_ID")

        insert_ignore(cursor, "Teacher_Subject", ts_insert_cols, data)
        print(f"[OK] Teacher_Subject: {len(data)}")

        # --------------------------------------------------------
        # 9. STUDENT_SUBJECT
        #    Current + historical Sem1 + historical Sem2.
        # --------------------------------------------------------
        ss_map = {}

        for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
            rows = read_csv(folder, "student_subject.csv")

            for r in rows:
                key = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                )

                value = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                )

                old = ss_map.get(key)
                if old and old != value:
                    raise RuntimeError(
                        f"Conflicting Student_Subject mapping: {key}"
                    )

                ss_map[key] = value

        data = list(ss_map.values())

        insert_ignore(
            cursor,
            "Student_Subject",
            ["Student_ID", "Subject_ID", "Semester_ID"],
            data,
        )
        print(f"[OK] Student_Subject: {len(data)}")

        # --------------------------------------------------------
        # 10. ATTENDANCE
        # --------------------------------------------------------
        attendance_map = {}

        for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
            rows = read_csv(folder, "attendance.csv")

            for r in rows:
                key = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                    val(r, "Attendance_Date"),
                )

                attendance_map[key] = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                    val(r, "Attendance_Date"),
                    val(r, "Attendance_Status") if r.get("Attendance_Status") is not None else val(r, "Status"),
                )

        data = list(attendance_map.values())

        insert_ignore(
            cursor,
            "Attendance",
            [
                "Student_ID",
                "Subject_ID",
                "Semester_ID",
                "Attendance_Date",
                "Attendance_Status",
            ],
            data,
        )
        print(f"[OK] Attendance: {len(data)}")

        # --------------------------------------------------------
        # 11. PRACTICAL ATTENDANCE
        # --------------------------------------------------------
        practical_columns = table_columns(cursor, "Practical_Attendance")

        if practical_columns:
            practical_map = {}

            for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
                rows = read_csv(
                    folder,
                    "practical_attendance.csv",
                    required=False,
                )

                for r in rows:
                    key = (
                        integer(r["Student_ID"]),
                        integer(r["Subject_ID"]),
                        integer(r["Semester_ID"]),
                        val(r, "Attendance_Date"),
                    )

                    practical_map[key] = (
                        integer(r["Student_ID"]),
                        integer(r["Subject_ID"]),
                        integer(r["Semester_ID"]),
                        val(r, "Attendance_Date"),
                        val(r, "Status"),
                    )

            data = list(practical_map.values())

            insert_ignore(
                cursor,
                "Practical_Attendance",
                [
                    "Student_ID",
                    "Subject_ID",
                    "Semester_ID",
                    "Attendance_Date",
                    "Status",
                ],
                data,
            )
            print(f"[OK] Practical_Attendance: {len(data)}")

        # --------------------------------------------------------
        # 12. ASSIGNMENTS
        # --------------------------------------------------------
        assignment_map = {}

        for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
            rows = read_csv(folder, "assignments.csv")

            for r in rows:
                key = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                    integer(r["Assignment_No"]),
                )

                assignment_map[key] = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    num(r["Marks"]),
                    integer(r["Semester_ID"]),
                    integer(r["Assignment_No"]),
                )

        data = list(assignment_map.values())

        insert_ignore(
            cursor,
            "Assignment",
            [
                "Student_ID",
                "Subject_ID",
                "Marks",
                "Semester_ID",
                "Assignment_No",
            ],
            data,
        )
        print(f"[OK] Assignment: {len(data)}")

        # --------------------------------------------------------
        # 13. TESTS
        # --------------------------------------------------------
        test_map = {}

        for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
            rows = read_csv(folder, "tests.csv")

            for r in rows:
                key = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                    integer(r["Test_No"]),
                )

                test_map[key] = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Test_No"]),
                    num(r["Marks"]),
                    integer(r["Semester_ID"]),
                )

        data = list(test_map.values())

        insert_ignore(
            cursor,
            "Test",
            [
                "Student_ID",
                "Subject_ID",
                "Test_No",
                "Marks",
                "Semester_ID",
            ],
            data,
        )
        print(f"[OK] Test: {len(data)}")

        # --------------------------------------------------------
        # 14. SEMESTER RESULTS
        # --------------------------------------------------------
        result_map = {}

        for folder in [CURRENT_DIR, HIST_SEM1_DIR, HIST_SEM2_DIR]:
            rows = read_csv(folder, "semester_results.csv")

            for r in rows:
                key = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                )

                result_map[key] = (
                    integer(r["Student_ID"]),
                    integer(r["Subject_ID"]),
                    integer(r["Semester_ID"]),
                    num(r["Marks"]),
                )

        data = list(result_map.values())

        insert_ignore(
            cursor,
            "Semester_Result",
            ["Student_ID", "Subject_ID", "Semester_ID", "Marks"],
            data,
        )
        print(f"[OK] Semester_Result: {len(data)}")

        # --------------------------------------------------------
        # 15. ADMIN
        # --------------------------------------------------------
        rows = read_csv(DATA_DIR, "admin.csv")
        data = []

        for r in rows:
            raw_password = val(r, "Password")
            password_hash = (
                generate_password_hash(raw_password)
                if raw_password else None
            )

            data.append((
                integer(r["Admin_ID"]),
                val(r, "Username"),
                password_hash,
            ))

        insert_ignore(
            cursor,
            "Admin",
            ["Admin_ID", "Username", "Password"],
            data,
        )
        print(f"[OK] Admin: {len(data)}")

        # --------------------------------------------------------
        # COMMIT
        # --------------------------------------------------------
        conn.commit()

        print()
        print("=" * 70)
        print("DATA LOADING COMPLETED SUCCESSFULLY")
        print("=" * 70)

        report_tables = [
            "Department",
            "Program",
            "Semester",
            "Student",
            "Subject",
            "Teacher",
            "Teacher_Subject",
            "Student_Subject",
            "Attendance",
            "Practical_Attendance",
            "Assignment",
            "Test",
            "Semester_Result",
            "Admin",
        ]

        for table in report_tables:
            if table_exists(cursor, table):
                print(f"{table:25} : {count_rows(cursor, table)}")

        print()
        print("Old dummy project data was replaced.")
        print("Root-level duplicate CSV data was not used.")
        print("Current + Historical Sem1 + Historical Sem2 data were loaded.")
        print()
        print("NEXT STEP: run auto_pipeline.py")

    except Exception as exc:
        if conn:
            conn.rollback()

        print()
        print("=" * 70)
        print("DATA LOADING FAILED - TRANSACTION ROLLED BACK")
        print("=" * 70)
        print(f"ERROR: {exc}")
        print()

        sys.exit(1)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
