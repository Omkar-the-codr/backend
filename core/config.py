import os

from dotenv import load_dotenv  # type: ignore

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES"))
FRIEND_INVITE_EXPIRE_MINUTES = int(
    os.getenv("FRIEND_INVITE_EXPIRE_MINUTES")
)

# Resend email
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM")

# celery
# CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
# CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

# backed frontend url
BACKEND_URL = os.getenv("BACKEND_URL")

# GOOGLE client id
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
