# app/settings.py
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# --- Project Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
CONFIG_PATH = BASE_DIR / "config/mappings.yml"
OUTPUT_DIR = BASE_DIR / "data/output"
INPUT_DIR = BASE_DIR / "data/input"

# --- Database Configuration ---
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# --- Mappings Configuration ---
try:
    with open(CONFIG_PATH, 'r', encoding="utf-8") as f:
        MAPPINGS = yaml.safe_load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"El archivo de mapeos no se encontró en: {CONFIG_PATH}")

# --- Application Constants ---
CLIENT_SOURCE_FILE = "DATOS_ESTRATEGIA.xlsx"
SEND_SOURCE_DIR = "CONSOLIDADO"