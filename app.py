
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


# Database connection
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database
def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            major TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Home page + Search + Statistics
@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        WHERE name LIKE ?
        OR email LIKE ?
        OR major LIKE ?
        ORDER BY id DESC
    """, (
        f"%{search}%",
        f"%{search}%",
        f"%{search}%"
    )).fetchall()

    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        students=students,
        search=search,
        total_students=total_students
    )


# Add student
@app.route("/add", methods=["POST"])
def add_student():
    name = request.form["name"].strip()
    email = request.form["email"].strip()
    major = request.form["major"].strip()

    if not name or not email or not major:
        return "All fields are required!", 400

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM students WHERE LOWER(email) = LOWER(?)",
        (email,)
    ).fetchone()

    if existing:
        conn.close()
        return "This email already exists!", 409

    conn.execute("""
        INSERT INTO students (name, email, major)
        VALUES (?, ?, ?)
    """, (name, email, major))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# Edit student
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?", (id,)
    ).fetchone()

    if student is None:
        conn.close()
        return "Student not found", 404

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        major = request.form["major"].strip()

        if not name or not email or not major:
            conn.close()
            return "All fields are required!", 400

        existing = conn.execute("""
            SELECT id FROM students
            WHERE LOWER(email) = LOWER(?) AND id != ?
        """, (email, id)).fetchone()

        if existing:
            conn.close()
            return "This email already exists!", 409

        conn.execute("""
            UPDATE students
            SET name = ?, email = ?, major = ?
            WHERE id = ?
        """, (name, email, major, id))

        conn.commit()
        conn.close()

        return redirect(url_for("index"))

    conn.close()

    return render_template("edit.html", student=student)


# Delete student
@app.route("/delete/<int:id>", methods=["POST"])
def delete_student(id):
    conn = get_db_connection()

    conn.execute(
        "DELETE FROM students WHERE id = ?", (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# Run application
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
