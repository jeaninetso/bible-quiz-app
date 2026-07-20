"""One-off CLI to create your own login. There's no public /auth/register
endpoint on purpose — this app is single-user, not multi-tenant, so keeping
account creation off the network entirely keeps the attack surface small.

Usage: .venv/bin/python -m scripts.create_user <username>
"""

import sys
from getpass import getpass

from app import crud
from app.auth import hash_password
from app.database import Base, SessionLocal, engine


def create_user(username: str, password: str) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if crud.get_user_by_username(db, username) is not None:
            print(f"User '{username}' already exists.")
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

    create_user(username_arg, password_arg)
