
import sqlite3
import os
from pathlib import Path
from flask import (
    Flask, render_template, request, abort,
    session, redirect, url_for, flash
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-for-local-testing")

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"


# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(str(DATABASE))
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables and insert quiz questions
def create_database():
    conn = get_db_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                answer TEXT NOT NULL
            )
        """)

        
        # Create the results table first
        conn.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL
            )
        """)

        # Add user_id if it does not exist
        columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(results)"
            ).fetchall()
        ]

        if "user_id" not in columns:
            conn.execute(
                "ALTER TABLE results ADD COLUMN user_id INTEGER"
            )

        # Create accounts for students and the website owner
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            )
        """)

       


        # Insert questions only if none exist
        count = conn.execute(
            "SELECT COUNT(*) FROM questions"
        ).fetchone()[0]

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
        print("Database initialized successfully.")

    finally:
        conn.close()


# Home page
@app.route("/")
def home():
    return render_template("home.html")


# Lessons page
@app.route("/lessons")
def lessons():
    return render_template("lessons.html")



# Quiz page
@app.route("/quiz")
def quiz():
    conn = get_db_connection()

    try:
        questions = conn.execute(
            "SELECT * FROM questions ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    return render_template("quiz.html", questions=questions)


# Process submitted quiz answers
@app.route("/submit", methods=["POST"])
def submit():
    # Require the student to log in first
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:
        questions = conn.execute(
            "SELECT * FROM questions ORDER BY id"
        ).fetchall()

        score = 0

        for question in questions:
            user_answer = request.form.get(
                f"question_{question['id']}"
            )

            if user_answer == question["answer"]:
                score += 1

        total = len(questions)
        name = session.get("student", "Student")

        # Save the result with the logged-in user's ID
        conn.execute("""
            INSERT INTO results (name, score, total, user_id)
            VALUES (?, ?, ?, ?)
        """, (name, score, total, session["user_id"]))

        conn.commit()

    finally:
        conn.close()

    return render_template(
        "result.html",
        name=name,
        score=score,
        total=total
    )
# View all students' quiz results

from flask import render_template, session, redirect, url_for
import sqlite3


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not name or not username or not password:
            return "Please fill in all fields.", 400

        conn = get_db_connection()
        try:
            conn.execute(
                """INSERT INTO users
                   (name, username, password_hash, role)
                   VALUES (?, ?, ?, 'student')""",
                (name, username, generate_password_hash(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists. Please choose another.", 400
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
        finally:
            conn.close()

        if user and check_password_hash(
            user["password_hash"], password
        ):
            session.clear()
            session["user_id"] = user["id"]
            session["student"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("results_page"))

            return redirect(url_for("lessons"))

        flash("Invalid username or password.")

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))





@app.route("/results")
def results_page():
    # Only logged-in users should view results
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    # Admin can see every student's result
    if session.get("role") == "admin":
        results = conn.execute("""
            SELECT name, score, total
            FROM results
            ORDER BY id DESC
        """).fetchall()

    # Student can see only their own results
    else:
        results = conn.execute("""
            SELECT name, score, total
            FROM results
            WHERE user_id = ?
            ORDER BY id DESC
        """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "results.html",
        results=results,
        is_admin=(session.get("role") == "admin")
    )


# Lesson content for each card
# Detailed lesson content for all six cards
LESSONS = {
    "strong-passwords": {
        "title": "Digital Safety: Strong Passwords",
        "icon": "🔑",
        "sections": [
            {
                "heading": "Introduction",
                "paragraph": (
                    "Strong passwords help defend against unauthorized access, "
                    "data breaches, and identity theft. They protect sensitive "
                    "personal, financial, and professional information."
                )
            },
            {
                "heading": "Crucial Components of a Strong Password",
                "paragraph": "Use these principles to create strong passwords:",
                "points": [
                    "Length: Use at least 12–16 characters. Longer passwords are generally harder to crack.",
                    "Character Variety: Mix uppercase letters, lowercase letters, numbers, and special symbols.",
                    "Uniqueness: Never reuse the same password across multiple platforms.",
                    "Randomness: Avoid predictable patterns such as 12345 or qwerty, names, and birthdays."
                ]
            },
            {
                "heading": "Best Practices for Managing Passwords",
                "points": [
                    "Password Managers: Use a reputable password manager to generate and securely store passwords.",
                    "Multi-Factor Authentication (MFA): Enable MFA or 2FA wherever available.",
                    "Regular Audits: Check for exposed passwords and promptly change compromised credentials."
                ]
            }
        ],
        
    },

    "protect-privacy": {
        "title": "Protect Privacy",
        "icon": "🔒",
        "sections": [
            {
                "heading": "Introduction",
                "paragraph": (
                    "Digital privacy means protecting your personal information "
                    "when using websites, apps, social media, and other online services."
                )
            },
            {
                "heading": "Information You Should Protect",
                "points": [
                    "Security Credentials: Never share passwords, PINs, OTPs, or security answers.",
                    "Location Details: Avoid publicly sharing your home address, school, or frequent locations.",
                    "Financial Data: Keep credit card numbers, banking details, and government identification private."
                ]
            },
            {
                "heading": "Why Privacy Matters",
                "points": [
                    "Identity Theft: Criminals may misuse personal information in your name.",
                    "Financial Fraud: Exposed banking details can lead to unauthorized transactions.",
                    "Phishing and Social Engineering: Scammers can use personal details to create convincing scams."
                ]
            },
            {
                "heading": "Best Practices for Privacy Protection",
                "points": [
                    "Verify the Source: Be cautious of unexpected calls, texts, and emails requesting personal information.",
                    "Use Strong Credentials: Create unique passwords and enable MFA.",
                    "Review Privacy Settings: Limit what strangers can see on social media and in mobile apps."
                ]
            }
        ],
        
    },

    "avoid-phishing": {
        "title": "Avoid Phishing",
        "icon": "🎣",
        "sections": [
            {
                "heading": "Introduction",
                "paragraph": (
                    "Phishing is a scam in which cybercriminals pretend to be "
                    "trustworthy people or organizations to steal sensitive information "
                    "such as passwords and financial details."
                )
            },
            {
                "heading": "How Phishing Works",
                "paragraph": (
                    "Attackers may send fake emails, text messages, or direct messages "
                    "that imitate banks, government agencies, or familiar online services. "
                    "They may direct you to fake websites designed to steal your credentials."
                )
            },
            {
                "heading": "Warning Signs of Phishing",
                "points": [
                    "Suspicious Sender Addresses: Look for misspelled or unfamiliar email domains.",
                    "Urgent Messages: Be cautious of threats about account suspension or immediate payment.",
                    "Generic Greetings: Messages such as 'Dear Customer' may be suspicious, especially alongside other warning signs.",
                    "Unexpected Links or Attachments: Avoid opening unexpected links or unfamiliar files."
                ]
            },
            {
                "heading": "Best Practices for Digital Safety",
                "points": [
                    "Verify Directly: Visit the official website yourself instead of clicking suspicious links.",
                    "Inspect URLs: Check the website address carefully before entering sensitive information.",
                    "Enable MFA: Add another layer of protection to your accounts.",
                    "Keep Software Updated: Install updates for your operating system, browser, and security software."
                ]
            }
        ],
        
    },

    "respect-others": {
        "title": "Respect Others",
        "icon": "🤝",
        "sections": [
            {
                "heading": "Introduction",
                "paragraph": (
                    "Digital citizenship means behaving safely, legally, and respectfully "
                    "online. Treat people in digital spaces with the same kindness and "
                    "respect you would show them in person."
                )
            },
            {
                "heading": "Behaviors to Avoid",
                "points": [
                    "Cyberbullying: Do not threaten, insult, or repeatedly target people online.",
                    "Harassment: Do not send abusive or intimidating messages.",
                    "Doxxing: Never publish someone's private information without their consent.",
                    "Privacy Violations: Do not share another person's private photos, messages, or personal details without permission."
                ]
            },
            {
                "heading": "How to Be Respectful Online",
                "points": [
                    "Think Before Posting: Consider how your words may affect other people.",
                    "Respect Differences: Communicate politely even when opinions differ.",
                    "Protect Privacy: Ask permission before sharing someone else's information.",
                    "Block and Report: Use platform reporting tools when you encounter harassment or abusive behavior.",
                    "Follow Community Guidelines: Read and follow the rules of websites and online communities."
                ]
            }
        ],
        
    },

    "verify-information": {
        "title": "Verify Information",
        "icon": "📰",
        "sections": [
            {
                "heading": "Introduction",
                "paragraph": (
                    "Digital literacy includes checking whether online information is "
                    "accurate before believing it or sharing it with others. False claims "
                    "and manipulated media can spread quickly and cause harm."
                )
            },
            {
                "heading": "Why Verification Matters",
                "points": [
                    "Misinformation: Incorrect information can mislead people.",
                    "Rumors: Unverified claims can cause unnecessary fear or confusion.",
                    "Reputation: Sharing false claims can harm individuals and organizations.",
                    "Online Safety: Fake information may be used to promote scams."
                ]
            },
            {
                "heading": "How to Verify Information",
                "points": [
                    "Check the Source: Find out who published the information and whether the source is trustworthy.",
                    "Compare Sources: Look for confirmation from other reliable sources.",
                    "Check the Date: Old information may no longer be accurate.",
                    "Look for Evidence: Check whether the claim includes supporting facts or credible references.",
                    "Use Fact-Checking Resources: Consult reputable independent fact-checking organizations when needed.",
                    "Think Before Sharing: Do not forward information you cannot verify."
                ]
            }
        ],
        
    },

    "use-technology-responsibly": {
        "title": "Use Technology Responsibly",
        "icon": "💻",
        "sections": [
            {
                "heading": "Introduction",
                "paragraph": (
                    "Responsible technology use means using digital devices, websites, "
                    "and applications safely, ethically, and legally. Your online actions "
                    "can affect your privacy, reputation, relationships, and future opportunities."
                )
            },
            {
                "heading": "Use Technology for Positive Purposes",
                "points": [
                    "Learn and Create: Use digital tools to study, develop skills, and create useful projects.",
                    "Collaborate: Communicate respectfully and work with others online.",
                    "Share Responsibly: Avoid spreading misinformation, hate speech, or harmful content.",
                    "Protect Yourself: Avoid downloading files or software from unknown sources."
                ]
            },
            {
                "heading": "Respect Laws and Rules",
                "points": [
                    "Copyright: Do not copy or distribute someone else's creative work without appropriate permission.",
                    "Website Rules: Follow the terms and community guidelines of the services you use.",
                    "Digital Property: Respect other people's accounts, files, work, and creations.",
                    "Privacy: Keep personal information secure and respect other users' digital boundaries."
                ]
            },
            {
                "heading": "Build Healthy Digital Habits",
                "points": [
                    "Balance Screen Time: Make time for sleep, physical activity, and offline activities.",
                    "Be Kind: Communicate with empathy and respect.",
                    "Check Before Sharing: Verify information before forwarding it.",
                    "Maintain Security: Keep devices and applications updated."
                ]
            }
        ],
        
    }
}

# ADD THIS ROUTE BELOW YOUR EXISTING ROUTES
@app.route("/lesson/<slug>")
def lesson_detail(slug):
    lesson = LESSONS.get(slug)

    if lesson is None:
        abort(404)

    return render_template("lesson_detail.html", lesson=lesson)


# Initialize the database and start Flask
if __name__ == "__main__":
    create_database()
    app.run(debug=True)