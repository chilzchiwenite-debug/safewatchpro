from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(email="chilzchiwenite@gmail.com").first()

    if user:
        print("Before:", user.role)

        user.role = "admin"
        db.session.commit()

        updated_user = User.query.filter_by(email="chilzchiwenite@gmail.com").first()
        print("After:", updated_user.role)
    else:
        print("User not found")