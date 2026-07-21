"""One-off CLI to create your own login, or reset its password if it already
exists. There's no public /auth/register endpoint on purpose — this app is
single-user, not multi-tenant, so keeping account creation off the network
entirely keeps the attack surface small.

A password reset updates the existing row in place rather than deleting and
recreating the user — deleting would orphan every QuizAttempt/
UserBookProgress/UserBadge row still pointing at that user_id, silently
wiping quiz history, XP, and badges.

Usage: .venv/bin/python -m scripts.create_user <username>
"""

import sys
from getpass import getpass

from app import crud
from app.auth import hash_password
from app.database import Base, SessionLocal, engine


def create_or_reset_user(username: str, password: str) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = crud.get_user_by_username(db, username)
        if existing is not None:
            answer = input(f"User '{username}' already exists. Reset their password? [y/N] ").strip().lower()
            if answer != "y":
                print("Left unchanged.")
                return
            crud.update_user_password(db, existing, hash_password(password))
            print(f"Password updated for '{username}'.")
            return
        crud.create_user(db, username, hash_password(password))
        print(f"Created user '{username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.create_user <username>")
        sys.exit(1)

    username_arg = sys.argv[1]
    password_arg = getpass("Password: ")
    confirm_arg = getpass("Confirm password: ")
    if password_arg != confirm_arg:
        print("Passwords didn't match.")
        sys.exit(1)

    create_or_reset_user(username_arg, password_arg)
