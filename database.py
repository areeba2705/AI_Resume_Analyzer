import pymysql

try:
    connection = pymysql.connect(
        host="localhost",
        port=3307,
        user="root",
        password="Areeba_1234",
        database="ai_resume_system"    # Python -> Mysql -> ai_resume_system
    )

    print("Database Connected Successfully!")

    cursor = connection.cursor()    #A cursor is used to send SQL commands from Python to MySQL

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            candidate_name VARCHAR(100),
            email VARCHAR(100),
            resume VARCHAR(255),
            job_role VARCHAR(100),
            match_score FLOAT,
            skills TEXT,
            status VARCHAR(50)
        )
    """)

    connection.commit()    #Save these changes permanently.

    print("Resumes Table Created Successfully!")

except Exception as e:
    print("Error:", e)