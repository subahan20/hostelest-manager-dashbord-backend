from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import BaseModel


class UserRole:
    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    MANAGER = "manager"

    ALL_ROLES = [SUPER_ADMIN, OWNER, MANAGER]


class User(BaseModel):
    __tablename__ = "users"

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(100), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default=UserRole.MANAGER, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    owner = db.relationship(
        "Owner",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    manager = db.relationship(
        "Manager",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against stored hash (supporting bcrypt, werkzeug scrypt/pbkdf2, sha256, md5, plain)."""
        if not self.password_hash or not password:
            return False

        pwd_candidates = [password]
        trimmed = password.strip()
        if trimmed != password:
            pwd_candidates.append(trimmed)

        for pwd in pwd_candidates:
            # 1. Try standard bcrypt if starts with $2
            if self.password_hash.startswith(("$2a$", "$2b$", "$2y$")):
                try:
                    import bcrypt
                    if bcrypt.checkpw(pwd.encode("utf-8"), self.password_hash.encode("utf-8")):
                        return True
                except Exception:
                    pass

            # 2. Try werkzeug (scrypt, pbkdf2, etc.)
            try:
                if check_password_hash(self.password_hash, pwd):
                    return True
            except Exception:
                pass

            # 3. Fallback bcrypt attempt
            try:
                import bcrypt
                if bcrypt.checkpw(pwd.encode("utf-8"), self.password_hash.encode("utf-8")):
                    return True
            except Exception:
                pass

            # 4. Try sha256 / md5 hex
            try:
                import hashlib
                if hashlib.sha256(pwd.encode("utf-8")).hexdigest() == self.password_hash:
                    return True
                if hashlib.md5(pwd.encode("utf-8")).hexdigest() == self.password_hash:
                    return True
            except Exception:
                pass

            # 5. Plain equality (for dev / seed fixtures)
            if self.password_hash == pwd:
                return True

        return False

    def to_dict(self) -> dict:
        """Return safe dictionary representation without password hash."""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
