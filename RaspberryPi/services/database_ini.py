import sqlite3
import os

db_folder = "RaspberryPi"
db_name = "DevicesSettings.db"

os.makedirs(db_folder, exist_ok=True)

db_path = os.path.join(db_folder, db_name)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS CameraSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parameter1 TEXT,
    parameter2 TEXT,
    parameter3 TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS SpectrometerSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parameter1 TEXT,
    parameter2 TEXT,
    parameter3 TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS PositionerSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parameter1 TEXT,
    parameter2 TEXT,
    parameter3 TEXT
)
""")

conn.commit()
conn.close()

print(f"Database created: {db_path}")