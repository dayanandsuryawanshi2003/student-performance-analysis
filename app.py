from flask import Flask, render_template, request, session, redirect, url_for
from db import get_db_connection
import pandas as pd
import os
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from auto_pipeline import run_pipeline_safe


app = Flask(__name__)

app.secret_key = "SPS_flask_2026_6077@"

BASE_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"


# ============================================================
# PROJECT ACADEMIC RULES
# ============================================================

ASSIGNMENTS_PER_SUBJECT = 2
TESTS_PER_SUBJECT = 2

ASSIGNMENT_MAX_MARKS = 20
TEST_MAX_MARKS = 20

ATTENDANCE_WEIGHT = 0.30
ASSIGNMENT_WEIGHT = 0.30
TEST_WEIGHT = 0.40


# ============================================================
# PERFORMANCE CALCULATION HELPERS
# ============================================================

def calculate_percentage(obtained, maximum):
    if maximum <= 0:
        return 0.0

    return (float(obtained or 0) / float(maximum)) * 100


def calculate_performance(
    attendance_percentage,
    assignment_percentage,
    test_percentage
):
    return (
        (attendance_percentage * ATTENDANCE_WEIGHT)
        + (assignment_percentage * ASSIGNMENT_WEIGHT)
        + (test_percentage * TEST_WEIGHT)
    )


def get_grade(score):
    score = float(score or 0)

    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"


def get_performance_level(score):
    score = float(score or 0)

    if score >= 80:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Needs Improvement"


def calculate_subject_performance(
    cursor,
    student_id,
    subject_id,
    semester_id
):
    """
    Central performance calculation used by:
    - Student performance
    - Admin performance
    - Report
    """

    # --------------------------------------------------------
    # Attendance
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_classes,
            SUM(
                CASE
                    WHEN Attendance_Status = 'Present'
                    THEN 1
                    ELSE 0
                END
            ) AS present_classes
        FROM Attendance
        WHERE Student_ID = %s
          AND Subject_ID = %s
          AND Semester_ID = %s
        """,
        (
            student_id,
            subject_id,
            semester_id
        )
    )

    attendance = cursor.fetchone()

    total_classes = attendance["total_classes"] or 0
    present_classes = attendance["present_classes"] or 0

    attendance_percentage = calculate_percentage(
        present_classes,
        total_classes
    )

    # --------------------------------------------------------
    # Assignments
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(Marks), 0) AS obtained_marks,
            COUNT(*) AS assignment_count
        FROM Assignment
        WHERE Student_ID = %s
          AND Subject_ID = %s
          AND Semester_ID = %s
        """,
        (
            student_id,
            subject_id,
            semester_id
        )
    )

    assignment = cursor.fetchone()

    assignment_obtained = assignment["obtained_marks"] or 0
    assignment_count = assignment["assignment_count"] or 0

    assignment_max = (
        assignment_count * ASSIGNMENT_MAX_MARKS
    )

    assignment_percentage = calculate_percentage(
        assignment_obtained,
        assignment_max
    )

    # --------------------------------------------------------
    # Tests
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(Marks), 0) AS obtained_marks,
            COUNT(*) AS test_count
        FROM Test
        WHERE Student_ID = %s
          AND Subject_ID = %s
          AND Semester_ID = %s
        """,
        (
            student_id,
            subject_id,
            semester_id
        )
    )

    test = cursor.fetchone()

    test_obtained = test["obtained_marks"] or 0
    test_count = test["test_count"] or 0

    test_max = (
        test_count * TEST_MAX_MARKS
    )

    test_percentage = calculate_percentage(
        test_obtained,
        test_max
    )

    # --------------------------------------------------------
    # Final performance
    # --------------------------------------------------------

    performance_percentage = calculate_performance(
        attendance_percentage,
        assignment_percentage,
        test_percentage
    )

    return {
        "Attendance_Percentage": round(
            attendance_percentage,
            2
        ),
        "Assignment_Percentage": round(
            assignment_percentage,
            2
        ),
        "Test_Percentage": round(
            test_percentage,
            2
        ),
        "Performance_Percentage": round(
            performance_percentage,
            2
        ),
        "Grade": get_grade(
            performance_percentage
        ),
        "Performance_Level": get_performance_level(
            performance_percentage
        )
    }


def calculate_student_overall(subject_results):
    """
    Calculates overall student performance from
    subject-wise performance.
    """

    if not subject_results:
        return {
            "Overall_Percentage": 0,
            "Overall_Grade": "N/A",
            "Strong_Subject": "N/A",
            "Weak_Subject": "N/A",
            "Performance_Level": "Needs Improvement"
        }

    overall_percentage = (
        sum(
            item["Performance_Percentage"]
            for item in subject_results
        )
        / len(subject_results)
    )

    strongest_subject = max(
        subject_results,
        key=lambda x: x["Performance_Percentage"]
    )

    weakest_subject = min(
        subject_results,
        key=lambda x: x["Performance_Percentage"]
    )

    return {
        "Overall_Percentage": round(
            overall_percentage,
            2
        ),
        "Overall_Grade": get_grade(
            overall_percentage
        ),
        "Strong_Subject": strongest_subject[
            "Subject_Name"
        ],
        "Weak_Subject": weakest_subject[
            "Subject_Name"
        ],
        "Performance_Level": get_performance_level(
            overall_percentage
        )
    }


def get_student_subject_results(
    cursor,
    student_id,
    semester_id
):
    """
    Returns all subject-wise performance for
    one student in one semester.
    """

    cursor.execute(
        """
        SELECT
            sub.Subject_ID,
            sub.Subject_Name,
            sub.Subject_Type
        FROM Student_Subject ss
        JOIN Subject sub
            ON ss.Subject_ID = sub.Subject_ID
        WHERE ss.Student_ID = %s
          AND ss.Semester_ID = %s
        ORDER BY sub.Subject_Name
        """,
        (
            student_id,
            semester_id
        )
    )

    subjects = cursor.fetchall()

    subject_results = []

    for subject in subjects:

        performance = calculate_subject_performance(
            cursor,
            student_id,
            subject["Subject_ID"],
            semester_id
        )

        subject_results.append(
            {
                "Subject_Name":
                    subject["Subject_Name"],

                "Subject_Type":
                    subject["Subject_Type"],

                "Attendance_Percentage":
                    performance[
                        "Attendance_Percentage"
                    ],

                "Assignment_Percentage":
                    performance[
                        "Assignment_Percentage"
                    ],

                "Test_Percentage":
                    performance[
                        "Test_Percentage"
                    ],

                "Performance_Percentage":
                    performance[
                        "Performance_Percentage"
                    ],

                "Grade":
                    performance["Grade"],

                "Performance_Level":
                    performance[
                        "Performance_Level"
                    ]
            }
        )

    return subject_results


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM Department"
    )

    departments = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "home.html",
        departments=departments
    )


# ============================================================
# TEACHER LOGIN
# ============================================================

@app.route(
    "/teacher-login",
    methods=["GET", "POST"]
)
def teacher_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM Teacher
            WHERE Username = %s
            """,
            (username,)
        )

        teacher = cursor.fetchone()

        cursor.close()
        connection.close()

        if teacher and check_password_hash(
            teacher["Password"],
            password
        ):

            session["teacher_id"] = (
                teacher["Teacher_ID"]
            )

            session["teacher_username"] = (
                teacher["Username"]
            )

            return redirect(
                url_for("teacher_dashboard")
            )

        return "Invalid username or password"

    return render_template(
        "teacher_login.html"
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin-login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM Admin
            WHERE Username = %s
            """,
            (username,)
        )

        admin = cursor.fetchone()

        cursor.close()
        connection.close()

        if admin and check_password_hash(
            admin["Password"],
            password
        ):

            session["admin_id"] = (
                admin["Admin_ID"]
            )

            session["admin_username"] = (
                admin["Username"]
            )

            return redirect(
                url_for("admin_dashboard")
            )

        return "Invalid username or password"

    return render_template(
        "admin_login.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    return render_template(
        "admin_dashboard.html",
        username=session["admin_username"]
    )


# ============================================================
# STUDENT LOGIN
# ============================================================

@app.route(
    "/student-login",
    methods=["GET", "POST"]
)
def student_login():

    if request.method == "POST":

        roll_no = request.form["roll_no"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM Student
            WHERE Roll_No = %s
            """,
            (roll_no,)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        if student and check_password_hash(
            student["Password"],
            password
        ):

            session["student_id"] = (
                student["Student_ID"]
            )

            session["student_roll_no"] = (
                student["Roll_No"]
            )

            return redirect(
                url_for("student_dashboard")
            )

        return "Invalid roll number or password"

    return render_template(
        "student_login.html"
    )


# ============================================================
# TEACHER DASHBOARD
# ============================================================

@app.route("/teacher-dashboard")
def teacher_dashboard():

    if "teacher_id" not in session:
        return redirect(
            url_for("teacher_login")
        )

    return render_template(
        "teacher_dashboard.html",
        username=session["teacher_username"]
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Name,
            s.Roll_No,
            d.Department_Name,
            p.Program_Name,
            sem.Semester_Name
        FROM Student s
        LEFT JOIN Department d
            ON s.Department_ID =
               d.Department_ID
        LEFT JOIN Program p
            ON s.Program_ID =
               p.Program_ID
        LEFT JOIN Semester sem
            ON s.Semester_ID =
               sem.Semester_ID
           AND s.Program_ID =
               sem.Program_ID
        WHERE s.Student_ID = %s
        """,
        (session["student_id"],)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "student_dashboard.html",
        student=student
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/teacher-logout")
def teacher_logout():

    session.pop("teacher_id", None)
    session.pop("teacher_username", None)

    return redirect(
        url_for("home")
    )


@app.route("/student-logout")
def student_logout():

    session.pop("student_id", None)
    session.pop("student_roll_no", None)

    return redirect(
        url_for("home")
    )


@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect(
        url_for("home")
    )


# ============================================================
# STUDENTS
# ============================================================

@app.route(
    "/students",
    methods=["GET", "POST"]
)
def students():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        roll_no = request.form["roll_no"]
        name = request.form["name"]
        gender = request.form["gender"]
        department_id = request.form[
            "department_id"
        ]
        program_id = request.form[
            "program_id"
        ]
        semester_id = request.form[
            "semester_id"
        ]
        password = request.form["password"]

        password_hash = (
            generate_password_hash(password)
        )

        cursor.execute(
            """
            INSERT INTO Student
            (
                Roll_No,
                Name,
                Gender,
                Department_ID,
                Program_ID,
                Semester_ID,
                Password
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                roll_no,
                name,
                gender,
                department_id,
                program_id,
                semester_id,
                password_hash
            )
        )

        student_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT Subject_ID
            FROM Subject
            WHERE Program_ID = %s
              AND Semester_ID = %s
            """,
            (
                program_id,
                semester_id
            )
        )

        subjects = cursor.fetchall()

        for subject in subjects:

            cursor.execute(
                """
                INSERT INTO Student_Subject
                (
                    Student_ID,
                    Subject_ID,
                    Semester_ID
                )
                VALUES (%s,%s,%s)
                """,
                (
                    student_id,
                    subject["Subject_ID"],
                    semester_id
                )
            )

        connection.commit()

        cursor.close()
        connection.close()

        run_pipeline_safe()

        return redirect(
            url_for("students")
        )

    cursor.execute(
        """
        SELECT
            Department_ID,
            Department_Name
        FROM Department
        ORDER BY Department_Name
        """
    )

    departments = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            Program_ID,
            Program_Name
        FROM Program
        ORDER BY Program_Name
        """
    )

    programs = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name,
            s.Gender,
            d.Department_Name,
            p.Program_Name,
            sem.Semester_Name
        FROM Student s
        LEFT JOIN Department d
            ON s.Department_ID =
               d.Department_ID
        LEFT JOIN Program p
            ON s.Program_ID =
               p.Program_ID
        LEFT JOIN Semester sem
            ON s.Semester_ID =
               sem.Semester_ID
           AND s.Program_ID =
               sem.Program_ID
        ORDER BY s.Student_ID
        """
    )

    students_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "students.html",
        students=students_data,
        departments=departments,
        programs=programs
    )


# ============================================================
# PROGRAM → SEMESTERS
# ============================================================

@app.route(
    "/get_semesters/<int:program_id>"
)
def get_semesters(program_id):

    if "admin_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name
        FROM Semester
        WHERE Program_ID = %s
        ORDER BY Semester_ID
        """,
        (program_id,)
    )

    semesters = cursor.fetchall()

    cursor.close()
    connection.close()

    return semesters


@app.route(
    "/get_subject_semesters/<int:program_id>"
)
def get_subject_semesters(program_id):

    if "admin_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name
        FROM Semester
        WHERE Program_ID = %s
        ORDER BY Semester_ID
        """,
        (program_id,)
    )

    semesters = cursor.fetchall()

    cursor.close()
    connection.close()

    return semesters


# ============================================================
# SUBJECTS
# ============================================================

@app.route(
    "/subjects",
    methods=["GET", "POST"]
)
def subjects():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        subject_name = request.form[
            "subject_name"
        ]

        subject_type = request.form[
            "subject_type"
        ]

        program_id = request.form[
            "program_id"
        ]

        semester_id = request.form[
            "semester_id"
        ]

        cursor.execute(
            """
            INSERT INTO Subject
            (
                Subject_Name,
                Subject_Type,
                Program_ID,
                Semester_ID
            )
            VALUES (%s,%s,%s,%s)
            """,
            (
                subject_name,
                subject_type,
                program_id,
                semester_id
            )
        )

        subject_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT Student_ID
            FROM Student
            WHERE Program_ID = %s
              AND Semester_ID = %s
            """,
            (
                program_id,
                semester_id
            )
        )

        matching_students = cursor.fetchall()

        for student in matching_students:

            cursor.execute(
                """
                SELECT 1
                FROM Student_Subject
                WHERE Student_ID = %s
                  AND Subject_ID = %s
                """,
                (
                    student["Student_ID"],
                    subject_id
                )
            )

            already_exists = cursor.fetchone()

            if not already_exists:

                cursor.execute(
                    """
                    INSERT INTO Student_Subject
                    (
                        Student_ID,
                        Subject_ID,
                        Semester_ID
                    )
                    VALUES (%s,%s,%s)
                    """,
                    (
                        student["Student_ID"],
                        subject_id,
                        semester_id
                    )
                )

        connection.commit()

        cursor.close()
        connection.close()

        run_pipeline_safe()

        return redirect(
            url_for("subjects")
        )

    cursor.execute(
        """
        SELECT
            Program_ID,
            Program_Name
        FROM Program
        ORDER BY Program_ID
        """
    )

    programs = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name,
            Program_ID
        FROM Semester
        ORDER BY Program_ID,
                 Semester_ID
        """
    )

    semesters = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            s.Subject_ID,
            s.Subject_Name,
            s.Subject_Type,
            p.Program_Name,
            sem.Semester_Name
        FROM Subject s
        LEFT JOIN Program p
            ON s.Program_ID =
               p.Program_ID
        LEFT JOIN Semester sem
            ON s.Semester_ID =
               sem.Semester_ID
           AND s.Program_ID =
               sem.Program_ID
        ORDER BY s.Subject_ID
        """
    )

    subjects_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "subjects.html",
        programs=programs,
        semesters=semesters,
        subjects=subjects_data
    )


# ============================================================
# ATTENDANCE
# ============================================================

@app.route(
    "/attendance",
    methods=["GET", "POST"]
)
def attendance():

    if "teacher_id" not in session:
        return redirect(
            url_for("teacher_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        program_id = request.form[
            "program_id"
        ]

        semester_id = request.form[
            "semester_id"
        ]

        subject_id = request.form[
            "subject_id"
        ]

        attendance_date = request.form[
            "attendance_date"
        ]

        cursor.execute(
            """
            SELECT Student_ID
            FROM Student
            WHERE Program_ID = %s
              AND Semester_ID = %s
            """,
            (
                program_id,
                semester_id
            )
        )

        students_data = cursor.fetchall()

        for student in students_data:

            student_id = student[
                "Student_ID"
            ]

            status = request.form.get(
                f"status_{student_id}"
            )

            if status:

                cursor.execute(
                    """
                    INSERT INTO Attendance
                    (
                        Student_ID,
                        Subject_ID,
                        Semester_ID,
                        Attendance_Date,
                        Attendance_Status
                    )
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        student_id,
                        subject_id,
                        semester_id,
                        attendance_date,
                        status
                    )
                )

        connection.commit()

        cursor.close()
        connection.close()

        run_pipeline_safe()

        return redirect(
            url_for("attendance")
        )

    cursor.execute(
        """
        SELECT
            Program_ID,
            Program_Name
        FROM Program
        ORDER BY Program_Name
        """
    )

    programs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "attendance.html",
        programs=programs
    )


@app.route(
    "/get_attendance_semesters/<int:program_id>"
)
def get_attendance_semesters(program_id):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name
        FROM Semester
        WHERE Program_ID = %s
        ORDER BY Semester_ID
        """,
        (program_id,)
    )

    semesters = cursor.fetchall()

    cursor.close()
    connection.close()

    return semesters


@app.route(
    "/get_attendance_subjects/"
    "<int:program_id>/<int:semester_id>"
)
def get_attendance_subjects(
    program_id,
    semester_id
):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Subject_ID,
            Subject_Name
        FROM Subject
        WHERE Program_ID = %s
          AND Semester_ID = %s
        ORDER BY Subject_Name
        """,
        (
            program_id,
            semester_id
        )
    )

    subjects_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return subjects_data


@app.route(
    "/get_attendance_students/"
    "<int:program_id>/<int:semester_id>/<int:subject_id>"
)
def get_attendance_students(
    program_id,
    semester_id,
    subject_id
):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name
        FROM Student s
        JOIN Student_Subject ss
            ON s.Student_ID =
               ss.Student_ID
        WHERE s.Program_ID = %s
          AND s.Semester_ID = %s
          AND ss.Subject_ID = %s
        ORDER BY s.Roll_No
        """,
        (
            program_id,
            semester_id,
            subject_id
        )
    )

    students_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return students_data


# ============================================================
# ATTENDANCE REPORT
# ============================================================

@app.route("/attendance-report")
def attendance_report():

    if (
        "teacher_id" not in session
        and "admin_id" not in session
    ):
        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name,
            sub.Subject_ID,
            sub.Subject_Name,
            sub.Subject_Type,

            COUNT(*) AS Total_Classes,

            SUM(
                CASE
                    WHEN a.Attendance_Status =
                         'Present'
                    THEN 1
                    ELSE 0
                END
            ) AS Present,

            SUM(
                CASE
                    WHEN a.Attendance_Status =
                         'Absent'
                    THEN 1
                    ELSE 0
                END
            ) AS Absent,

            ROUND(
                SUM(
                    CASE
                        WHEN a.Attendance_Status =
                             'Present'
                        THEN 1
                        ELSE 0
                    END
                ) * 100.0 / COUNT(*),
                2
            ) AS Attendance_Percentage

        FROM Attendance a

        JOIN Student s
            ON a.Student_ID =
               s.Student_ID

        JOIN Subject sub
            ON a.Subject_ID =
               sub.Subject_ID

        GROUP BY
            s.Student_ID,
            s.Roll_No,
            s.Name,
            sub.Subject_ID,
            sub.Subject_Name,
            sub.Subject_Type

        ORDER BY
            s.Roll_No,
            sub.Subject_Name
        """
    )

    attendance_data = cursor.fetchall()

    cursor.close()
    connection.close()

    if "admin_id" in session:
        dashboard_url = url_for(
            "admin_dashboard"
        )
    else:
        dashboard_url = url_for(
            "teacher_dashboard"
        )

    return render_template(
        "attendance_report.html",
        attendance_data=attendance_data,
        dashboard_url=dashboard_url
    )


# ============================================================
# ASSIGNMENTS
# ============================================================

@app.route(
    "/assignments",
    methods=["GET", "POST"]
)
def assignments():

    if "teacher_id" not in session:
        return redirect(
            url_for("teacher_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        program_id = request.form[
            "program_id"
        ]

        semester_id = request.form[
            "semester_id"
        ]

        subject_id = request.form[
            "subject_id"
        ]

        student_ids = request.form.getlist(
            "student_id[]"
        )

        assignment_1_marks = (
            request.form.getlist(
                "assignment_1[]"
            )
        )

        assignment_2_marks = (
            request.form.getlist(
                "assignment_2[]"
            )
        )

        for i in range(len(student_ids)):

            student_id = student_ids[i]

            if (
                i < len(assignment_1_marks)
                and assignment_1_marks[i].strip()
                != ""
            ):

                cursor.execute(
                    """
                    INSERT INTO Assignment
                    (
                        Student_ID,
                        Subject_ID,
                        Marks,
                        Semester_ID,
                        Assignment_No
                    )
                    VALUES (%s,%s,%s,%s,1)
                    """,
                    (
                        student_id,
                        subject_id,
                        assignment_1_marks[i],
                        semester_id
                    )
                )

            if (
                i < len(assignment_2_marks)
                and assignment_2_marks[i].strip()
                != ""
            ):

                cursor.execute(
                    """
                    INSERT INTO Assignment
                    (
                        Student_ID,
                        Subject_ID,
                        Marks,
                        Semester_ID,
                        Assignment_No
                    )
                    VALUES (%s,%s,%s,%s,2)
                    """,
                    (
                        student_id,
                        subject_id,
                        assignment_2_marks[i],
                        semester_id
                    )
                )

        connection.commit()

        cursor.close()
        connection.close()

        run_pipeline_safe()

        return redirect(
            url_for("assignments")
        )

    cursor.execute(
        """
        SELECT
            Program_ID,
            Program_Name
        FROM Program
        ORDER BY Program_Name
        """
    )

    programs = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            a.Assignment_ID,
            a.Student_ID,
            a.Subject_ID,
            a.Semester_ID,
            a.Assignment_No,
            a.Marks,
            s.Roll_No,
            s.Name,
            sub.Subject_Name
        FROM Assignment a
        JOIN Student s
            ON a.Student_ID =
               s.Student_ID
        JOIN Subject sub
            ON a.Subject_ID =
               sub.Subject_ID
        ORDER BY
            s.Roll_No,
            sub.Subject_Name,
            a.Assignment_No
        """
    )

    assignment_records = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "assignments.html",
        programs=programs,
        assignment_records=assignment_records
    )


@app.route(
    "/get_assignment_semesters/<int:program_id>"
)
def get_assignment_semesters(program_id):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name
        FROM Semester
        WHERE Program_ID = %s
        ORDER BY Semester_ID
        """,
        (program_id,)
    )

    semesters = cursor.fetchall()

    cursor.close()
    connection.close()

    return semesters


@app.route(
    "/get_assignment_subjects/"
    "<int:program_id>/<int:semester_id>"
)
def get_assignment_subjects(
    program_id,
    semester_id
):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Subject_ID,
            Subject_Name,
            Subject_Type
        FROM Subject
        WHERE Program_ID = %s
          AND Semester_ID = %s
        ORDER BY Subject_Name
        """,
        (
            program_id,
            semester_id
        )
    )

    subjects_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return subjects_data


@app.route(
    "/get_assignment_students/"
    "<int:subject_id>/<int:semester_id>"
)
def get_assignment_students(
    subject_id,
    semester_id
):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name
        FROM Student_Subject ss
        JOIN Student s
            ON ss.Student_ID =
               s.Student_ID
        WHERE ss.Subject_ID = %s
          AND ss.Semester_ID = %s
        ORDER BY s.Roll_No
        """,
        (
            subject_id,
            semester_id
        )
    )

    students_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return students_data


# ============================================================
# TESTS
# ============================================================

@app.route(
    "/tests",
    methods=["GET", "POST"]
)
def tests():

    if "teacher_id" not in session:
        return redirect(
            url_for("teacher_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        program_id = request.form[
            "program_id"
        ]

        semester_id = request.form[
            "semester_id"
        ]

        subject_id = request.form[
            "subject_id"
        ]

        student_ids = request.form.getlist(
            "student_id[]"
        )

        test_1_marks = (
            request.form.getlist(
                "test_1[]"
            )
        )

        test_2_marks = (
            request.form.getlist(
                "test_2[]"
            )
        )

        for i in range(len(student_ids)):

            student_id = student_ids[i]

            if (
                i < len(test_1_marks)
                and test_1_marks[i].strip()
                != ""
            ):

                cursor.execute(
                    """
                    INSERT INTO Test
                    (
                        Student_ID,
                        Subject_ID,
                        Marks,
                        Semester_ID,
                        Test_No
                    )
                    VALUES (%s,%s,%s,%s,1)
                    """,
                    (
                        student_id,
                        subject_id,
                        test_1_marks[i],
                        semester_id
                    )
                )

            if (
                i < len(test_2_marks)
                and test_2_marks[i].strip()
                != ""
            ):

                cursor.execute(
                    """
                    INSERT INTO Test
                    (
                        Student_ID,
                        Subject_ID,
                        Marks,
                        Semester_ID,
                        Test_No
                    )
                    VALUES (%s,%s,%s,%s,2)
                    """,
                    (
                        student_id,
                        subject_id,
                        test_2_marks[i],
                        semester_id
                    )
                )

        connection.commit()

        cursor.close()
        connection.close()

        run_pipeline_safe()

        return redirect(
            url_for("tests")
        )

    cursor.execute(
        """
        SELECT
            Program_ID,
            Program_Name
        FROM Program
        ORDER BY Program_Name
        """
    )

    programs = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            t.Test_ID,
            t.Student_ID,
            t.Subject_ID,
            t.Semester_ID,
            t.Test_No,
            t.Marks,
            s.Roll_No,
            s.Name,
            sub.Subject_Name
        FROM Test t
        JOIN Student s
            ON t.Student_ID =
               s.Student_ID
        JOIN Subject sub
            ON t.Subject_ID =
               sub.Subject_ID
        ORDER BY
            s.Roll_No,
            sub.Subject_Name,
            t.Test_No
        """
    )

    test_records = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "tests.html",
        programs=programs,
        test_records=test_records
    )


@app.route(
    "/get_test_semesters/<int:program_id>"
)
def get_test_semesters(program_id):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name
        FROM Semester
        WHERE Program_ID = %s
        ORDER BY Semester_ID
        """,
        (program_id,)
    )

    semesters = cursor.fetchall()

    cursor.close()
    connection.close()

    return semesters


@app.route(
    "/get_test_subjects/"
    "<int:program_id>/<int:semester_id>"
)
def get_test_subjects(
    program_id,
    semester_id
):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Subject_ID,
            Subject_Name,
            Subject_Type
        FROM Subject
        WHERE Program_ID = %s
          AND Semester_ID = %s
        ORDER BY Subject_Name
        """,
        (
            program_id,
            semester_id
        )
    )

    subjects_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return subjects_data


@app.route(
    "/get_test_students/"
    "<int:subject_id>/<int:semester_id>"
)
def get_test_students(
    subject_id,
    semester_id
):

    if "teacher_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name
        FROM Student_Subject ss
        JOIN Student s
            ON ss.Student_ID =
               s.Student_ID
        WHERE ss.Subject_ID = %s
          AND ss.Semester_ID = %s
        ORDER BY s.Roll_No
        """,
        (
            subject_id,
            semester_id
        )
    )

    students_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return students_data


# ============================================================
# SEMESTER RESULT
# ============================================================

@app.route("/semester-result")
def semester_result():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    student_id = session["student_id"]

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            sr.Semester_Result_ID,
            sr.Student_ID,
            sr.Semester_ID,
            sr.Total_Marks,
            sr.Percentage,
            sr.Grade,
            sr.Result_Status
        FROM Semester_Result sr
        WHERE sr.Student_ID = %s
        ORDER BY sr.Semester_ID
        """,
        (student_id,)
    )

    semester_results = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            Student_ID,
            Roll_No,
            Name
        FROM Student
        WHERE Student_ID = %s
        """,
        (student_id,)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    summary = None

    if semester_results:

        percentages = [
            float(result["Percentage"])
            for result in semester_results
            if result["Percentage"] is not None
        ]

        if percentages:

            average_percentage = (
                sum(percentages)
                / len(percentages)
            )

            highest_percentage = max(
                percentages
            )

            lowest_percentage = min(
                percentages
            )

        else:

            average_percentage = 0
            highest_percentage = 0
            lowest_percentage = 0

        passed_semesters = sum(
            1
            for result in semester_results
            if str(
                result["Result_Status"]
            ).lower() == "pass"
        )

        failed_semesters = sum(
            1
            for result in semester_results
            if str(
                result["Result_Status"]
            ).lower() == "fail"
        )

        summary = {
            "Total_Semesters":
                len(semester_results),

            "Average_Percentage":
                round(
                    average_percentage,
                    2
                ),

            "Highest_Percentage":
                round(
                    highest_percentage,
                    2
                ),

            "Lowest_Percentage":
                round(
                    lowest_percentage,
                    2
                ),

            "Passed_Semesters":
                passed_semesters,

            "Failed_Semesters":
                failed_semesters
        }

    return render_template(
        "semester_results.html",
        student=student,
        semester_results=semester_results,
        summary=summary
    )


# ============================================================
# RESULT AJAX ROUTES
# ============================================================

@app.route(
    "/get_result_semesters/<int:program_id>"
)
def get_result_semesters(program_id):

    if "admin_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Semester_ID,
            Semester_Name
        FROM Semester
        WHERE Program_ID = %s
        ORDER BY Semester_ID
        """,
        (program_id,)
    )

    semesters = cursor.fetchall()

    cursor.close()
    connection.close()

    return semesters


@app.route(
    "/get_result_subjects/"
    "<int:program_id>/<int:semester_id>"
)
def get_result_subjects(
    program_id,
    semester_id
):

    if "admin_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Subject_ID,
            Subject_Name,
            Subject_Type
        FROM Subject
        WHERE Program_ID = %s
          AND Semester_ID = %s
        ORDER BY Subject_Name
        """,
        (
            program_id,
            semester_id
        )
    )

    subjects_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return subjects_data


@app.route(
    "/get_result_students/"
    "<int:subject_id>/<int:semester_id>"
)
def get_result_students(
    subject_id,
    semester_id
):

    if "admin_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name
        FROM Student_Subject ss
        JOIN Student s
            ON ss.Student_ID =
               s.Student_ID
        WHERE ss.Subject_ID = %s
          AND ss.Semester_ID = %s
        ORDER BY s.Roll_No
        """,
        (
            subject_id,
            semester_id
        )
    )

    students_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return students_data


@app.route(
    "/get_subjects_by_program/<int:program_id>"
)
def get_subjects_by_program(program_id):

    if "admin_id" not in session:
        return {
            "error": "Unauthorized"
        }, 401

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Subject_ID,
            Subject_Name,
            Subject_Type,
            Semester_ID
        FROM Subject
        WHERE Program_ID = %s
        ORDER BY
            Semester_ID,
            Subject_Name
        """,
        (program_id,)
    )

    subjects_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return subjects_data


# ============================================================
# TEACHERS
# ============================================================

@app.route(
    "/teachers",
    methods=["GET", "POST"]
)
def teachers():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        password_hash = (
            generate_password_hash(password)
        )

        cursor.execute(
            """
            INSERT INTO Teacher
            (
                Username,
                Password
            )
            VALUES (%s,%s)
            """,
            (
                username,
                password_hash
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        run_pipeline_safe()

        return redirect(
            url_for("teachers")
        )

    cursor.execute(
        """
        SELECT
            Teacher_ID,
            Username
        FROM Teacher
        ORDER BY Teacher_ID
        """
    )

    teachers_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "teachers.html",
        teachers=teachers_list
    )


# ============================================================
# STUDENT ATTENDANCE
# ============================================================

@app.route("/student-attendance")
def student_attendance():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            sub.Subject_Name,
            sub.Subject_Type,

            COUNT(a.Attendance_ID)
                AS Total_Classes,

            SUM(
                CASE
                    WHEN a.Attendance_Status =
                         'Present'
                    THEN 1
                    ELSE 0
                END
            ) AS Present,

            SUM(
                CASE
                    WHEN a.Attendance_Status =
                         'Absent'
                    THEN 1
                    ELSE 0
                END
            ) AS Absent,

            ROUND(
                SUM(
                    CASE
                        WHEN a.Attendance_Status =
                             'Present'
                        THEN 1
                        ELSE 0
                    END
                ) * 100.0
                / COUNT(a.Attendance_ID),
                2
            ) AS Attendance_Percentage

        FROM Attendance a

        JOIN Subject sub
            ON a.Subject_ID =
               sub.Subject_ID

        WHERE a.Student_ID = %s

        GROUP BY
            sub.Subject_ID,
            sub.Subject_Name,
            sub.Subject_Type

        ORDER BY sub.Subject_Name
        """,
        (session["student_id"],)
    )

    attendance_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_attendance.html",
        attendance_data=attendance_data
    )


# ============================================================
# STUDENT ASSIGNMENTS
# ============================================================

@app.route("/student-assignments")
def student_assignments():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            sub.Subject_Name,
            sub.Subject_Type,
            a.Assignment_No,
            a.Marks
        FROM Assignment a
        JOIN Subject sub
            ON a.Subject_ID =
               sub.Subject_ID
        WHERE a.Student_ID = %s
        ORDER BY
            sub.Subject_Name,
            a.Assignment_No
        """,
        (session["student_id"],)
    )

    assignment_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_assignments.html",
        assignment_data=assignment_data
    )


# ============================================================
# STUDENT TESTS
# ============================================================

@app.route("/student-tests")
def student_tests():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            sub.Subject_Name,
            sub.Subject_Type,
            t.Test_No,
            t.Marks
        FROM Test t
        JOIN Subject sub
            ON t.Subject_ID =
               sub.Subject_ID
        WHERE t.Student_ID = %s
        ORDER BY
            sub.Subject_Name,
            t.Test_No
        """,
        (session["student_id"],)
    )

    test_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_tests.html",
        test_data=test_data
    )


# ============================================================
# PANDAS PERFORMANCE ANALYSIS
# ============================================================

@app.route("/performance_analysis")
def performance_analysis():

    if (
        not session.get("admin_id")
        and not session.get("teacher_id")
    ):
        return redirect(
            url_for("home")
        )

    subject_file = (
        ANALYSIS_DIR
        / "subject_performance_analysis.csv"
    )

    overall_file = (
        ANALYSIS_DIR
        / "overall_performance_analysis.csv"
    )

    if (
        not subject_file.exists()
        or not overall_file.exists()
    ):
        return render_template(
            "performance_analysis.html",
            performance_data=[]
        )

    subject_df = pd.read_csv(
        subject_file
    )

    overall_df = pd.read_csv(
        overall_file
    )

    performance_data = []

    for _, student in overall_df.iterrows():

        student_id = student["Student_ID"]

        student_subjects = subject_df[
            subject_df["Student_ID"]
            == student_id
        ]

        subjects = []

        for _, subject in student_subjects.iterrows():

            score = float(
                subject.get(
                    "Subject_Performance_Score",
                    0
                )
            )

            subjects.append(
                {
                    "Subject_Name":
                        subject.get(
                            "Subject_Name",
                            "Unknown"
                        ),

                    "Attendance_Percentage":
                        subject.get(
                            "Attendance_Percentage",
                            0
                        ),

                    "Assignment_Percentage":
                        subject.get(
                            "Assignment_Percentage",
                            0
                        ),

                    "Test_Percentage":
                        subject.get(
                            "Test_Percentage",
                            0
                        ),

                    "Performance_Percentage":
                        score,

                    "Grade":
                        get_grade(score),

                    "Performance_Level":
                        get_performance_level(
                            score
                        )
                }
            )

        strong_subject = "N/A"
        weak_subject = "N/A"

        if not student_subjects.empty:

            strong_row = student_subjects.loc[
                student_subjects[
                    "Subject_Performance_Score"
                ].idxmax()
            ]

            weak_row = student_subjects.loc[
                student_subjects[
                    "Subject_Performance_Score"
                ].idxmin()
            ]

            strong_subject = strong_row.get(
                "Subject_Name",
                "N/A"
            )

            weak_subject = weak_row.get(
                "Subject_Name",
                "N/A"
            )

        overall_score = float(
            student.get(
                "Overall_Performance_Score",
                0
            )
        )

        semester_name = student.get(
            "Semester_Name",
            student.get(
                "Semester_ID",
                ""
            )
        )

        performance_data.append(
            {
                "Name":
                    student.get(
                        "Name",
                        ""
                    ),

                "Roll_No":
                    student.get(
                        "Roll_No",
                        ""
                    ),

                "Semester_Name":
                    semester_name,

                "Overall_Percentage":
                    round(
                        overall_score,
                        2
                    ),

                "Grade":
                    get_grade(
                        overall_score
                    ),

                "Strong_Subject":
                    strong_subject,

                "Weak_Subject":
                    weak_subject,

                "Performance_Level":
                    get_performance_level(
                        overall_score
                    ),

                "Subjects":
                    subjects
            }
        )

    return render_template(
        "performance_analysis.html",
        performance_data=performance_data
    )


# ============================================================
# STUDENT PERFORMANCE
# ============================================================

@app.route("/student-performance")
def student_performance():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    student_id = session["student_id"]

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name,
            d.Department_Name,
            p.Program_Name,
            sem.Semester_ID,
            sem.Semester_Name
        FROM Student s
        LEFT JOIN Department d
            ON s.Department_ID =
               d.Department_ID
        LEFT JOIN Program p
            ON s.Program_ID =
               p.Program_ID
        LEFT JOIN Semester sem
            ON s.Semester_ID =
               sem.Semester_ID
           AND s.Program_ID =
               sem.Program_ID
        WHERE s.Student_ID = %s
        """,
        (student_id,)
    )

    student = cursor.fetchone()

    if not student:

        cursor.close()
        connection.close()

        return "Student not found"

    semester_id = student["Semester_ID"]

    subject_results = (
        get_student_subject_results(
            cursor,
            student_id,
            semester_id
        )
    )

    overall = calculate_student_overall(
        subject_results
    )

    cursor.close()
    connection.close()

    return render_template(
        "student_performance.html",
        student=student,
        subject_results=subject_results,
        overall_percentage=
            overall["Overall_Percentage"],
        overall_grade=
            overall["Overall_Grade"],
        strong_subject=
            overall["Strong_Subject"],
        weak_subject=
            overall["Weak_Subject"]
    )


# ============================================================
# POWER BI
# ============================================================

@app.route("/open_admin_powerbi")
def open_admin_powerbi():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    pbix_path = (
        r"C:\new project\PowerBI\Admin_Reports.pbix"
    )

    os.startfile(pbix_path)

    return redirect(
        url_for("admin_dashboard")
    )


@app.route("/open_teacher_powerbi")
def open_teacher_powerbi():

    if "teacher_id" not in session:
        return redirect(
            url_for("teacher_login")
        )

    pbix_path = (
        r"C:\new project\PowerBI\Teacher_Reports.pbix"
    )

    os.startfile(pbix_path)

    return redirect(
        url_for("teacher_dashboard")
    )


@app.route("/open_student_powerbi")
def open_student_powerbi():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    pbix_path = (
        r"C:\new project\PowerBI\Student_Reports.pbix"
    )

    os.startfile(pbix_path)

    return redirect(
        url_for("student_dashboard")
    )


# ============================================================
# ADMIN PERFORMANCE ANALYSIS
# ============================================================

@app.route("/admin_performance_analysis")
def admin_performance_analysis():

    if "admin_id" not in session:
        return redirect(
            url_for("admin_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            s.Student_ID,
            s.Roll_No,
            s.Name,
            d.Department_Name,
            p.Program_Name,
            sem.Semester_Name,
            s.Semester_ID
        FROM Student s
        LEFT JOIN Department d
            ON s.Department_ID =
               d.Department_ID
        LEFT JOIN Program p
            ON s.Program_ID =
               p.Program_ID
        LEFT JOIN Semester sem
            ON s.Semester_ID =
               sem.Semester_ID
           AND s.Program_ID =
               sem.Program_ID
        ORDER BY s.Roll_No
        """
    )

    students_data = cursor.fetchall()

    performance_data = []

    for student in students_data:

        subject_results = (
            get_student_subject_results(
                cursor,
                student["Student_ID"],
                student["Semester_ID"]
            )
        )

        overall = calculate_student_overall(
            subject_results
        )

        performance_data.append(
            {
                "Roll_No":
                    student["Roll_No"],

                "Name":
                    student["Name"],

                "Department_Name":
                    student["Department_Name"],

                "Program_Name":
                    student["Program_Name"],

                "Semester_Name":
                    student["Semester_Name"],

                "Overall_Percentage":
                    overall[
                        "Overall_Percentage"
                    ],

                "Grade":
                    overall[
                        "Overall_Grade"
                    ],

                "Strong_Subject":
                    overall[
                        "Strong_Subject"
                    ],

                "Weak_Subject":
                    overall[
                        "Weak_Subject"
                    ],

                "Subjects":
                    subject_results
            }
        )

    cursor.close()
    connection.close()

    return render_template(
        "admin_performance_analysis.html",
        performance_data=performance_data
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

@app.route("/recommendations")
def recommendations():

    if (
        "admin_id" not in session
        and "teacher_id" not in session
        and "student_id" not in session
    ):
        return redirect(
            url_for("home")
        )

    subject_file = (
        ANALYSIS_DIR
        / "student"
        / "student_subject_performance.csv"
    )

    overall_file = (
        ANALYSIS_DIR
        / "overall_performance_analysis.csv"
    )

    if (
        not subject_file.exists()
        or not overall_file.exists()
    ):
        return render_template(
            "recommendations.html",
            recommendation_data=[]
        )

    subject_df = pd.read_csv(
        subject_file
    )

    overall_df = pd.read_csv(
        overall_file
    )

    if "student_id" in session:

        student_id = session[
            "student_id"
        ]

        overall_df = overall_df[
            overall_df["Student_ID"]
            == student_id
        ]

        subject_df = subject_df[
            subject_df["Student_ID"]
            == student_id
        ]

    career_skill_mapping = {

        "Data Analytics": [
            "Python",
            "SQL",
            "Statistics",
            "Data Analytics",
            "Database"
        ],

        "Data Science": [
            "Python",
            "Statistics",
            "Machine Learning",
            "Data Science",
            "Artificial Intelligence"
        ],

        "Artificial Intelligence / Machine Learning": [
            "Python",
            "Artificial Intelligence",
            "Machine Learning",
            "Deep Learning"
        ],

        "Software Development": [
            "Java",
            "Python",
            "Programming",
            "Object Oriented Programming",
            "Data Structures"
        ],

        "Web Development": [
            "HTML",
            "CSS",
            "JavaScript",
            "Web Development",
            "PHP"
        ],

        "Mobile App Development": [
            "Java",
            "Kotlin",
            "Dart",
            "Android",
            "Flutter"
        ],

        "Cloud Computing": [
            "Cloud Computing",
            "AWS",
            "Azure",
            "Google Cloud"
        ],

        "DevOps / DevSecOps": [
            "DevOps",
            "Docker",
            "Kubernetes",
            "Jenkins",
            "Git"
        ],

        "Database / SQL": [
            "SQL",
            "Database",
            "DBMS",
            "MySQL",
            "PostgreSQL"
        ],

        "Cybersecurity": [
            "Computer Networks",
            "Cyber Security",
            "Network Security",
            "Operating Systems"
        ],

        "QA / Software Testing": [
            "Software Testing",
            "Testing",
            "Selenium",
            "Java",
            "Python"
        ],

        "Business Intelligence": [
            "SQL",
            "DAX",
            "Power BI",
            "Tableau",
            "Excel"
        ],

        "UI/UX & Frontend Development": [
            "HTML",
            "CSS",
            "JavaScript",
            "UI/UX",
            "Frontend",
            "React"
        ],

        "Network Engineering": [
            "Computer Network",
            "Networking",
            "Cisco",
            "Wireshark"
        ],

        "System Administration": [
            "Operating Systems",
            "Linux",
            "Windows Server",
            "System Administration"
        ]
    }

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Domain_Name,
            Languages,
            Tools,
            Certifications,
            Projects
        FROM Career_Domain
        """
    )

    career_domain_rows = cursor.fetchall()

    cursor.close()
    connection.close()

    career_domain_info = {
        str(row["Domain_Name"])
        .strip()
        .lower(): row
        for row in career_domain_rows
    }

    recommendation_data = []

    for _, student in overall_df.iterrows():

        student_id = student[
            "Student_ID"
        ]

        student_subjects = subject_df[
            subject_df["Student_ID"]
            == student_id
        ].copy()

        if student_subjects.empty:
            continue

        overall = float(
            student[
                "Overall_Performance_Score"
            ]
        )

        strong_row = student_subjects.loc[
            student_subjects[
                "Average_Overall"
            ].idxmax()
        ]

        weak_row = student_subjects.loc[
            student_subjects[
                "Average_Overall"
            ].idxmin()
        ]

        strong_subject = strong_row.get(
            "Subject_Name",
            "N/A"
        )

        weak_subject = weak_row.get(
            "Subject_Name",
            "N/A"
        )

        weak_score = float(
            weak_row[
                "Average_Overall"
            ]
        )

        if overall >= 80:

            academic_advice = (
                "Excellent academic performance. "
                "Maintain your current performance "
                "and continue regular practice."
            )

        elif overall >= 60:

            academic_advice = (
                "Good academic performance with "
                "scope for improvement. Focus more "
                "on your weaker subjects."
            )

        else:

            academic_advice = (
                "Academic performance needs improvement. "
                "Focus on regular study, assignments "
                "and test preparation."
            )

        if weak_score < 60:

            academic_advice += (
                f" Give special attention to "
                f"{weak_subject}."
            )

        career_scores = {}

        for domain, relevant_subjects in (
            career_skill_mapping.items()
        ):

            matching_subject_scores = []

            for _, subject in (
                student_subjects.iterrows()
            ):

                subject_name = str(
                    subject.get(
                        "Subject_Name",
                        ""
                    )
                ).strip().lower()

                for relevant_subject in (
                    relevant_subjects
                ):

                    relevant_name = str(
                        relevant_subject
                    ).strip().lower()

                    if (
                        relevant_name
                        in subject_name
                        or subject_name
                        in relevant_name
                    ):

                        matching_subject_scores.append(
                            subject[
                                "Average_Overall"
                            ]
                        )

                        break

            if matching_subject_scores:

                career_scores[domain] = round(
                    sum(
                        matching_subject_scores
                    )
                    / len(
                        matching_subject_scores
                    ),
                    2
                )

        if not career_scores:

            career_scores = {
                "General IT / Skill Development":
                    round(overall, 2)
            }

        sorted_domains = sorted(
            career_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        recommended_domain = (
            sorted_domains[0][0]
        )

        recommended_score = (
            sorted_domains[0][1]
        )

        recommended_domain_info = (
            career_domain_info.get(
                recommended_domain
                .strip()
                .lower()
            )
        )

        top_domains = []

        for domain, score in (
            sorted_domains[:3]
        ):

            top_domains.append(
                {
                    "Domain_Name": domain,
                    "Suitability_Score": score
                }
            )

        career_explanation = (
            f"{recommended_domain} is suggested "
            f"based on your performance in subjects "
            f"related to this career domain."
        )

        placement_advice = (
            "Prepare a resume, practice aptitude "
            "questions, improve communication skills "
            "and work on technical interview "
            "preparation."
        )

        learning_resources = (
            f"Focus on {weak_subject} and strengthen "
            "relevant technical skills through "
            "practical projects, regular practice "
            "and learning resources."
        )

        semester_name = student.get(
            "Semester_Name",
            student.get(
                "Semester_ID",
                ""
            )
        )

        recommendation_data.append(
            {
                "Student_ID":
                    student_id,

                "Name":
                    student.get(
                        "Name",
                        ""
                    ),

                "Roll_No":
                    student.get(
                        "Roll_No",
                        ""
                    ),

                "Semester_Name":
                    semester_name,

                "Overall":
                    round(
                        overall,
                        2
                    ),

                "Strong_Subject":
                    strong_subject,

                "Weak_Subject":
                    weak_subject,

                "Academic_Advice":
                    academic_advice,

                "Placement_Advice":
                    placement_advice,

                "Career_Domain":
                    recommended_domain,

                "Career_Suitability":
                    recommended_score,

                "Career_Domain_Info":
                    recommended_domain_info,

                "Career_Explanation":
                    career_explanation,

                "Top_Career_Domains":
                    top_domains,

                "Learning_Resources":
                    learning_resources
            }
        )

    return render_template(
        "recommendations.html",
        recommendation_data=
            recommendation_data
    )


# ============================================================
# CAREER DOMAINS
# ============================================================

@app.route("/career-domains")
def career_domains():

    if "student_id" not in session:
        return redirect(
            url_for("student_login")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT
            Domain_ID,
            Domain_Name,
            Languages,
            Tools,
            Certifications,
            Projects
        FROM Career_Domain
        ORDER BY Domain_Name
        """
    )

    career_domains_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "career_domains.html",
        career_domains=
            career_domains_data
    )


# ============================================================
# REPORT
# ============================================================

@app.route("/report")
def report():

    if (
        "admin_id" not in session
        and "teacher_id" not in session
        and "student_id" not in session
    ):
        return redirect(
            url_for("home")
        )

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    if "student_id" in session:

        cursor.execute(
            """
            SELECT
                s.Student_ID,
                s.Roll_No,
                s.Name,
                d.Department_Name,
                p.Program_Name,
                sem.Semester_Name,
                s.Semester_ID
            FROM Student s
            LEFT JOIN Department d
                ON s.Department_ID =
                   d.Department_ID
            LEFT JOIN Program p
                ON s.Program_ID =
                   p.Program_ID
            LEFT JOIN Semester sem
                ON s.Semester_ID =
                   sem.Semester_ID
               AND s.Program_ID =
                   sem.Program_ID
            WHERE s.Student_ID = %s
            """,
            (session["student_id"],)
        )

    else:

        cursor.execute(
            """
            SELECT
                s.Student_ID,
                s.Roll_No,
                s.Name,
                d.Department_Name,
                p.Program_Name,
                sem.Semester_Name,
                s.Semester_ID
            FROM Student s
            LEFT JOIN Department d
                ON s.Department_ID =
                   d.Department_ID
            LEFT JOIN Program p
                ON s.Program_ID =
                   p.Program_ID
            LEFT JOIN Semester sem
                ON s.Semester_ID =
                   sem.Semester_ID
               AND s.Program_ID =
                   sem.Program_ID
            ORDER BY s.Roll_No
            """
        )

    students_data = cursor.fetchall()

    report_data = []

    for student in students_data:

        subject_results = (
            get_student_subject_results(
                cursor,
                student["Student_ID"],
                student["Semester_ID"]
            )
        )

        overall = calculate_student_overall(
            subject_results
        )

        report_data.append(
            {
                "Student_ID":
                    student["Student_ID"],

                "Roll_No":
                    student["Roll_No"],

                "Name":
                    student["Name"],

                "Department_Name":
                    student["Department_Name"],

                "Program_Name":
                    student["Program_Name"],

                "Semester_Name":
                    student["Semester_Name"],

                "Overall_Percentage":
                    overall[
                        "Overall_Percentage"
                    ],

                "Grade":
                    overall[
                        "Overall_Grade"
                    ],

                "Strong_Subject":
                    overall[
                        "Strong_Subject"
                    ],

                "Weak_Subject":
                    overall[
                        "Weak_Subject"
                    ],

                "Subjects":
                    subject_results
            }
        )

    cursor.close()
    connection.close()

    if "student_id" in session:

        dashboard_url = url_for(
            "student_dashboard"
        )

    elif "admin_id" in session:

        dashboard_url = url_for(
            "admin_dashboard"
        )

    else:

        dashboard_url = url_for(
            "teacher_dashboard"
        )

    return render_template(
        "report.html",
        report_data=report_data,
        dashboard_url=dashboard_url
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)