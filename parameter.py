import functools
import jwt


SECRET_KEY = "2ec26ad9-e039-445e-915e-a482dc6f5e3b"
ALGORITHM = "HS256"
auth_key = 'dARsJZWhU3h5G787m0bHwVHYExZQU42qbDY9BM7WBZHbDM9ttFVxE3upvPxk'
def get_token():
    return auth_key
