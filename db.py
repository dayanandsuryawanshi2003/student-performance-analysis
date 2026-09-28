import mysql.connector


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="student_performance_app",
        password="StudentApp@123",
        database="student_performance_db"
    )

    return connection

if __name__ == "__main__":
    connection = get_db_connection()

    if connection.is_connected():
        print("MySQL connected successfully!")

    connection.close()