from dotenv import load_dotenv
import os

load_dotenv() # Carrega o arquivo .env

DATABASE_URL = os.getenv("DATABASE_URL")