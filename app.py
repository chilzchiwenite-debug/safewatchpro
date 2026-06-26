import os

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from dotenv import load_dotenv

from db import db
from models import User, Report
from engine import calculate_severity



# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- APP SETUP ----------------
app = Flask(_name_)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USE_SSL"] = False

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

# DB
db_url = os.getenv("DATABASE_URL")

if db_url:
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300
}

# Upload folder
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ---------------- EXTENSIONS ----------------
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ---------------- TWILIO SETUP ----------------


# ---------------- AUTHORITY NUMBERS ----------------
AUTHORITY_NUMBERS = {
    "Nigeria Police Force": "+2347057337653",
    "Fire Service": "+2347065409291",
    "FRSC (Road Safety)": "+2349139600038",
    "Ambulance / Hospital Emergency": "+2348044444444",
    "Local Security Agency": "+2348055555555"
}

# ---------------- AUTHORITY LOGIC ----------------
def get_authority(category):
    category = (category or "").lower()

    if category in ["robbery", "kidnapping", "violence"]:
        return "Nigeria Police Force"
    elif category == "fire":
        return "Fire Service"
    elif category == "accident":
        return "FRSC (Road Safety)"
    elif category == "medical_emergency":
        return "Ambulance / Hospital Emergency"
    else:
        return "Local Security Agency"

# ---------------- SMS FUNCTION ----------------


# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------------- ROUTES ----------------
@app.route("/")
def index():

    if current_user.is_authenticated and current_user.role =="admin":
        return redirect(url_for("admin"))


    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role =="admin":
        return redirect(url_for("admin"))

    reports = Report.query.order_by(Report.id.desc()).all()
    return render_template("dashboard.html", reports=reports)


# ---------------- REPORT ----------------
@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    if request.method == "POST":

        name = request.form.get("name")
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        state = request.form.get("state")
        address = request.form.get("address")

        severity = calculate_severity(category)

        file = request.files.get("image")
        filename = None

        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        authority = get_authority(category)

        new_report = Report(
            name=name,
            title=title,
            description=description,
            category=category,
            severity=severity,
            state=state,
            address=address,
            image=filename,
            user_id=current_user.id,
            status="pending",
            authority=authority
        )

        db.session.add(new_report)
        db.session.commit()

        # 🚨 SEND SMS AFTER SAVE
        send_sms_to_authority(new_report)

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
    reports = Report.query.order_by(Report.id.desc()).all()

    return render_template("admin.html", users=users, reports=reports)


# ---------------- AUTH ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)

            if user.role == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/make-admin")
def make_admin():

    user = User.query.filter_by(
        email="chilzchiwenite@gmail.com"
    ).first()

    if not user:
        return "User not found"

    user.role = "admin"

    db.session.commit()

    return "User is now an admin"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))



@app.route("/map")
@login_required
def map_view():
    reports = Report.query.all()
    return render_template("map.html", reports=reports)


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            role="user"
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":
        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(user.email, salt="password-reset")

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            msg = Message(
                subject="SafeWatchPro Password Reset",
                recipients=[user.email]
            )

            msg.body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

This link expires in 1 hour.

SafeWatchPro Team
"""

            try:
                mail.send(msg)
                flash("If the email exists, a reset link has been sent.")
            except Exception as e:
                return f"Mail Error: {e}"

        else:
            flash("If the email exists, a reset link has been sent.")

        return redirect(url_for("login"))

    return render_template("forgot_password.html")




@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600
        )
    except:
        flash("Reset link is invalid or expired.")
        return redirect(url_for("forgot_password"))

    user = User.query.filter_by(email=email).first()

    if request.method == "POST":
        new_password = request.form.get("password")

        user.password = bcrypt.generate_password_hash(
            new_password
        ).decode("utf-8")

        db.session.commit()

        flash("Password updated successfully.")
        return redirect(url_for("login"))

    return render_template("reset_password.html")


@app.route("/delete-user/<int:user_id>")
@login_required
def delete_user(user_id):

    if current_user.role != "admin":
        flash("Access denied")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully")
    return redirect(url_for("admin"))
    


# ---------------- INIT DB ----------------
#with app.app_context():
    #db.create_all()#

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)