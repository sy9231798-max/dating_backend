import random
from datetime import date, datetime
from faker import Faker
from sqlmodel import SQLModel, Session, create_engine, Field, Column
from sqlalchemy import JSON, DateTime, func
from typing import Optional, List
from enum import Enum

from src.database import settings
from src.user.enums import Gender, AccountType
from src.user.models import UserModel, UserAdditionPicture, FriendTable

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

HOBBIES = [
    "reading", "gaming", "cooking", "hiking", "painting",
    "photography", "music", "cycling", "yoga", "travelling",
    "gardening", "dancing", "swimming", "coding", "writing",
]

STEP_STATUSES = ["COMPLETED"]

def generate_indian_phone_number():
    # First digit: 6-9
    first_digit = random.choice(['6', '7', '8', '9'])
    # Remaining 9 digits: 0-9
    remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    return first_digit + remaining_digits
def make_user(fake: Faker) -> UserModel:
    gender = Gender.FEMALE
    dob = fake.date_of_birth(minimum_age=18, maximum_age=60)

    return UserModel(
        first_name=fake.first_name_male() if gender == Gender.MALE else fake.first_name_female(),
        last_name=fake.last_name(),
        email=fake.unique.email(),
        phone_number=generate_indian_phone_number(),
        profile_picture=f"uploads/20260412_170232_706821.jpg",
        video_picture=f"uploads/20260411_203720_977044.mp4",
        dob=dob.isoformat(),
        gender=gender,
        hobby=random.sample(HOBBIES, k=random.randint(1, 4)),
        state=fake.state(),
        city=fake.city(),
        lvl=1,
        score=random.randint(100, 1000),
        step_1_error=random.choice(STEP_STATUSES),
        step_2_error=random.choice(STEP_STATUSES),
        step_3_error=random.choice(STEP_STATUSES),
        account_type=AccountType.AGENT,
        is_active=random.choice([False]),
    )


def make_addition_images(userId: int) -> UserAdditionPicture:
    return UserAdditionPicture(
        image_path="uploads/20260412_170232_709414.jpg" if userId % 2 == 0 else "uploads/20260426_090730_173040.jpg",
        user_id=userId
    )


def make_friends(userId: int) -> List[FriendTable]:
    return [
        FriendTable(
            user_id=userId,
            friend_id= i
        )
        for i in range(1,1001)
    ]


def seed(n: int = 100) -> None:
    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)  # creates tables if they don't exist

    fake = Faker("en_IN")
    Faker.seed(42)  # reproducible data; remove for random

    users = [make_user(fake) for _ in range(n)]
    with Session(engine) as session:
        session.add_all(users)
        session.commit()
        for i in users:
            all_addition_images = [make_addition_images(i.id) for _ in range(3)]
            session.add_all(all_addition_images)
            session.commit()
            # all_friends = make_friends(i.id)
            # session.add_all(all_friends)
            # session.commit()





    print(f"✅  Inserted {n} fake users into '{DATABASE_URL}'")


from src.password_handler import pwd_context
if __name__ == "__main__":
    seed(100)
    # print(pwd_context.hash("Admin@121"))
