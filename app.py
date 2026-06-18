import os

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
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

# ---------------- FIX: DATABASE ----------------
db_url = os.getenv("DATABASE_URL")

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or app.config.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ---------------- EXTENSIONS ----------------
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


# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))



# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")


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

            if user.role == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        flash("Invalid password")
        return redirect(url_for("login"))

    return render_template("login.html")

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot_password", methods=["GET" , "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("If email exists, reset link has been sent.")
            return redirect(url_for("login"))

        token = serializer.dumps(email, salt="password-reset-salt")

        reset_link = url_for("reset_password", token=token, _external=True)

        send_email(
            subject="SafeWatch Password Reset",
            recipients=[email],
            body=f"Click the link to reset your password:\n\n{reset_link}"
        )

        flash("Reset link sent to your email")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")

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

def create_admin_user():
    email = "chilzchiwenite@gmail.com"

    admin = User.query.filter_by(email=email).first()

    if not admin:
        hashed_pw = bcrypt.generate_password_hash("chimeral1").decode("utf-8")

        admin = User(
            username="admin",
            email=email,
            password=hashed_pw,
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()
# ---------------- DB INIT ----------------
with app.app_context():
    db.create_all()
    create_admin_user()



@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.role == "admin":
        return "Unauthorized", 403

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return redirect(url_for('admin'))


# ---------------- API ----------------
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

@app.route("/api/reports")
@login_required
def api_reports():
    reports = Report.query.all()

    return jsonify([
        {
            "title": r.title,
            "category": r.category,
            "severity": r.severity,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "created_at": str(r.created_at)
        }
        for r in reports
    ])

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)