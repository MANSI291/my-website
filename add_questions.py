import sqlite3
from pathlib import Path

# Connect to the existing CyberWise database
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"

new_questions = [
    (
        "What is the purpose of two-factor authentication (2FA)?",
        "To make passwords shorter",
        "To add an extra layer of account security",
        "To share accounts with friends",
        "To remove antivirus software",
        "B"
    ),
    (
        "What should you do if someone cyberbullies you online?",
        "Respond with threats",
        "Share their private information",
        "Save evidence, block or report them, and seek help",
        "Create a fake account to retaliate",
        "C"
    ),
    (
        "Which action respects copyright online?",
        "Copying any image without permission",
        "Claiming someone else's work as your own",
        "Sharing paid software without permission",
        "Getting permission or using properly licensed content",
        "D"
    ),
    (
        "Which is the safest way to protect your personal information?",
        "Post your home address publicly",
        "Share passwords with online friends",
        "Review privacy settings and limit personal information shared",
        "Use the same password everywhere",
        "C"
    ),
    (
        "What should you do before sharing a shocking news story online?",
        "Share it immediately",
        "Verify it using reliable sources",
        "Trust it because many people shared it",
        "Change the headline to make it exciting",
        "B"
    )
]

conn = sqlite3.connect(str(DATABASE))

try:
    # Confirm that the expected table exists
    table = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'questions'
    """).fetchone()

    if table is None:
        raise RuntimeError(
            "Questions table not found. Initialize the database first."
        )

    # Insert the five new questions
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
    """, new_questions)

    conn.commit()

    total = conn.execute(
        "SELECT COUNT(*) FROM questions"
    ).fetchone()[0]

    print("Five new CyberWise questions added successfully!")
    print("Total questions in database:", total)

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()