from werkzeug.security import generate_password_hash
from db import get_db_connection


# -------------------------
# Create Admin Account
# -------------------------

admin_username = "teacher1"
admin_password = "Teacher@123"

admin_password_hash = generate_password_hash(admin_password)


# -------------------------
# Create Student Account
# -------------------------

student_roll_no = "TEST001"
student_name = "Test Student"
student_password = "Student@123"

student_password_hash = generate_password_hash(student_password)


connection = get_db_connection()
cursor = connection.cursor()


# Insert Admin
cursor.execute(
    """
    INSERT INTO Admin (Username, Password)
    VALUES (%s, %s)
    """,
    (admin_username, admin_password_hash)
)


# Insert Student
cursor.execute(
    """
    INSERT INTO Student
    (Roll_No, Name, Password)
    VALUES (%s, %s, %s)
    """,
    (student_roll_no, student_name, student_password_hash)
)


connection.commit()

cursor.close()
connection.close()

print("Admin and Student accounts created successfully!")