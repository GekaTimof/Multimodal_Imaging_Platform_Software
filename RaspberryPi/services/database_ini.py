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
    AeEnable INTEGER NOT NULL DEFAULT 1 CHECK(AeEnable IN (0, 1)),
    AwbEnable INTEGER NOT NULL DEFAULT 1 CHECK(AwbEnable IN (0, 1)),
    ExposureTime INTEGER NOT NULL DEFAULT 10000 CHECK(ExposureTime BETWEEN 100 AND 3000000),
    AnalogueGain REAL NOT NULL DEFAULT 1.0 CHECK(AnalogueGain BETWEEN 0.0 AND 32.0),
    ExposureValue REAL NOT NULL DEFAULT 0.0 CHECK(ExposureValue BETWEEN -10.0 AND 10.0),
    RedGain REAL NOT NULL DEFAULT 1.0 CHECK(RedGain BETWEEN 0.0 AND 8.0),
    BlueGain REAL NOT NULL DEFAULT 1.0 CHECK(BlueGain BETWEEN 0.0 AND 8.0)
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

# Insert default camera settings if table is empty
cursor.execute("SELECT COUNT(*) FROM CameraSettings")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO CameraSettings (AeEnable, AwbEnable, ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
    VALUES (1, 1, 10000, 1.0, 0.0, 1.0, 1.0)
    """)

conn.commit()
conn.close()

print(f"Database created: {db_path}")

def main():
    """Main function to initialize database"""
    # The database initialization code above runs when the module is imported
    # This function exists for explicit calls if needed
    pass