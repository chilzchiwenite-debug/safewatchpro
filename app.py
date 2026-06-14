import os

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify
)

from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)

from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

from config import Config
from db import db
from models import User, Report
from engine import calculate_severity

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.config.from_object(Config)

app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ---------------- EMAIL ----------------
def send_email(subject, recipients, body):
    if not recipients:
        return

    msg = Message(
        subject=subject,
        sender=app.config.get("MAIL_DEFAULT_SENDER"),
        recipients=recipients,
        body=body
    )
    mail.send(msg)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------------- DB INIT ----------------
with app.app_context():
    db.create_all()

# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- MAP (FIXED MISSING ROUTE) ----------------
@app.route("/map")
@login_required
def map_view():
    return render_template("map.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(username=username, email=email, password=hashed_pw)

        db.session.add(user)
        db.session.commit()

        send_email(
            "Welcome to SafeWatch Pro 🚨",
            [email],
            f"Hello {username}, your account was created successfully."
        )

        flash("Registration successful")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User not found")
            return redirect(url_for("login"))

        if bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Welcome back")

            # 🚀 redirect admin properly
            if user.role == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        flash("Invalid password")
        return redirect(url_for("login"))

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully")
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("dashboard.html", reports=reports)

# ---------------- REPORT ----------------
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        address = request.form.get("address")

        severity = calculate_severity(category)

        file = request.files.get("image")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        new_report = Report(
            title=title,
            description=description,
            category=category,
            severity=severity,
            latitude=float(latitude),
            longitude=float(longitude),
            image=filename,
            address=address,
            user_id=current_user.id
        )

        db.session.add(new_report)
        db.session.commit()

        flash("Report submitted successfully")
        return redirect(url_for("dashboard"))

    return render_template("report.html")

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(email, salt="reset-password")
            link = url_for("reset_password", token=token, _external=True)

            send_email(
                "Reset Your Password",
                [email],
                f"Click to reset your password:\n{link}"
            )

        flash("If email exists, reset link sent.")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

# ---------------- RESET PASSWORD ----------------
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=3600)
    except:
        flash("Invalid or expired link")
        return redirect(url_for("login"))

    if request.method == "POST":
        new_password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user:
            user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
            db.session.commit()

        flash("Password updated successfully")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

# ---------------- ADMIN ----------------
@app.route("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        flash("Access denied")
        return redirect(url_for("dashboard"))

    users = User.query.all()
    reports = Report.query.all()

    return render_template("admin.html", users=users, reports=reports)

# ---------------- API STATS ----------------
@app.route("/api/stats")
@login_required
def stats():
    return jsonify({
        "users": User.query.count(),
        "reports": Report.query.count(),
        "high": Report.query.filter_by(severity="high").count(),
        "medium": Report.query.filter_by(severity="medium").count(),
        "low": Report.query.filter_by(severity="low").count()
    })

# ---------------- RUN ----------------
if __name__ == "__main__":
    print("🚀 SafeWatch Pro running...")
    with app.app_context():
        db.create_all()
    app.run(debug=True)