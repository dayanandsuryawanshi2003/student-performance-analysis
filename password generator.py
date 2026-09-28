from werkzeug.security import generate_password_hash

admin_password = "Admin@123"
teacher_password = "Teacher@123"
student_password = "Test@123"

admin_hash = generate_password_hash(admin_password)
teacher_hash = generate_password_hash(teacher_password)
student_hash = generate_password_hash(student_password)

print("ADMIN HASH:")
print(admin_hash)

print("\nTEACHER HASH:")
print(teacher_hash)

print("\nSTUDENT HASH:")
print(student_hash)