import sqlite3
from pathlib import Path

# Get the project folder
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(str(DATABASE))
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db_connection()

    try:
        # Create questions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                answer TEXT NOT NULL
                    CHECK (answer IN ('A', 'B', 'C', 'D'))
            )
        """)

        # Create results table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL
            )
        """)

        # Check whether questions already exist
        count = conn.execute(
            "SELECT COUNT(*) FROM questions"
        ).fetchone()[0]

        # Insert five questions if the table is empty
        if count == 0:
            questions = [
                (
                    "Which of the following is a strong password?",
                    "123456",
                    "password",
                    "John2005",
                    "Cyb3r@Safe#2026",
                    "D"
                ),
                (
                    "What should you do if you receive a suspicious link?",
                    "Click it immediately",
                    "Share it with friends",
                    "Avoid clicking and verify the source",
                    "Download the attachment",
                    "C"
                ),
                (
                    "Which behavior is responsible on social media?",
                    "Sharing someone's private information",
                    "Respecting other people's privacy",
                    "Cyberbullying",
                    "Creating fake accounts",
                    "B"
                ),
                (
                    "What is phishing?",
                    "A type of online game",
                    "An attempt to steal information using fake messages or websites",
                    "A programming language",
                    "A computer operating system",
                    "B"
                ),
                (
                    "What should you do before sharing information online?",
                    "Check whether the information is reliable",
                    "Share it immediately",
                    "Ignore the source",
                    "Change the information",
                    "A"
                )
            ]

            conn.executemany("""
                INSERT INTO questions (
                    question,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    answer
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, questions)

        conn.commit()

        print("Database created successfully!")
        print("Database location:", DATABASE)
        print(
            "Total questions:",
            conn.execute(
                "SELECT COUNT(*) FROM questions"
            ).fetchone()[0]
        )
        print(
            "Total results:",
            conn.execute(
                "SELECT COUNT(*) FROM results"
            ).fetchone()[0]
        )

    finally:
        conn.close()


if __name__ == "__main__":
    create_database()