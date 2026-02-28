from dotenv import load_dotenv
import os

load_dotenv() # Carrega o arquivo .env

DATABASE_URL = os.getenv("DATABASE_URL")

# ── AWS S3 ──
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION            = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME        = os.getenv("S3_BUCKET_NAME")