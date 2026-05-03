from database import SessionLocal, engine, Base
from models import News, User

db = SessionLocal()


def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)


def run_seed():
    # ===== News seed =====
    db.add_all([
        News(text="ด่วน! แชร์ให้ทุกคน", result="Fake", score=3),
        News(text="รัฐบาลประกาศวันหยุด", result="Likely Real", score=0),
        News(text="ได้เงินฟรี 100% คลิกเลย", result="Fake", score=4),
    ])

    # ===== Admin user seed =====
    db.add(
        User(
            username="admin",
            password="1234",   
            role="admin"
        )
    )

    db.commit()
    db.close()


if __name__ == "__main__":
    reset_database()
    run_seed()