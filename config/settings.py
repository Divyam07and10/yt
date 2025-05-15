from dotenv import load_dotenv
import os

load_dotenv()

MOCK_S3_BUCKET = os.getenv("MOCK_S3_BUCKET", "my-youtube-videos")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "mock_access_key")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "mock_secret_key")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "youtube")
DB_USER = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "secret")

MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB