from datetime import datetime
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import db

# Login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# User model

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    village_ids = db.Column(db.JSON, default=list)  # list of village USERID strings

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Auth helpers

def register_user(username, password):
    """Register a new user. Returns (user, error_msg)."""
    if not username or not password:
        return None, "Username and password are required."
    if len(username) < 3:
        return None, "Username must be at least 3 characters."
    if len(password) < 4:
        return None, "Password must be at least 4 characters."
    if User.query.filter_by(username=username).first():
        return None, "Username already exists."

    user = User(username=username, village_ids=[])
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user, None

def authenticate_user(username, password):
    """Authenticate a user. Returns (user, error_msg)."""
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return None, "Invalid username or password."
    return user, None

def link_village_to_user(user, village_id):
    """Link a village save to a user account."""
    if village_id not in user.village_ids:
        villages = list(user.village_ids) if user.village_ids else []
        villages.append(village_id)
        user.village_ids = villages
        db.session.commit()

def get_user_villages(user):
    """Get the list of village IDs for a user."""
    return user.village_ids if user.village_ids else []
