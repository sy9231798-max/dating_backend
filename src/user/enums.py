from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class AccountType(str, Enum):
    AGENT = "agent"
    USER = "user"


class CallStatus(str, Enum):
    REJECTED = "rejected"
    NONE = "none"
    MISSED = "missed"
    ANSWERED = "answered"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    REJECTED = "rejected"
    NONE = "none"
    COMPLETED = "completed"
