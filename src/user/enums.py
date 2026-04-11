from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AccountType(str, Enum):
    AGENT = "agent"
    USER = "user"