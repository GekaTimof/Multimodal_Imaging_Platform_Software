import sqlite3
import os

db_folder = "."
db_name = "DevicesSettings.db"

os.makedirs(db_folder, exist_ok=True)

db_path = os.path.join(db_folder, db_name)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS CameraSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SettingsName TEXT NOT NULL DEFAULT 'Basic',
    Resolution TEXT NOT NULL DEFAULT '1920x1080',
    PhotoResolution TEXT NOT NULL DEFAULT '3280x2464',
    VideoResolution TEXT NOT NULL DEFAULT '1920x1080',
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
    SettingsName TEXT NOT NULL DEFAULT 'Basic',
    parameter1 TEXT,
    parameter2 TEXT,
    parameter3 TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS PositionerSettings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    SettingsName TEXT NOT NULL DEFAULT 'Basic',
    parameter1 TEXT,
    parameter2 TEXT,
    parameter3 TEXT
)
""")

# Check if PhotoResolution and VideoResolution columns exist, add them if not
cursor.execute("PRAGMA table_info(CameraSettings)")
columns = [row[1] for row in cursor.fetchall()]
if 'PhotoResolution' not in columns:
    cursor.execute("ALTER TABLE CameraSettings ADD COLUMN PhotoResolution TEXT NOT NULL DEFAULT '3280x2464'")
if 'VideoResolution' not in columns:
    cursor.execute("ALTER TABLE CameraSettings ADD COLUMN VideoResolution TEXT NOT NULL DEFAULT '1920x1080'")

# Insert default camera settings for slot 0 if not exists
cursor.execute("SELECT COUNT(*) FROM CameraSettings WHERE id = 0")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
    INSERT INTO CameraSettings (id, SettingsName, Resolution, PhotoResolution, VideoResolution, AeEnable, AwbEnable, ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
    VALUES (0, 'Basic', '1920x1080', '3280x2464', '1920x1080', 1, 1, 10000, 1.0, 0.0, 1.0, 1.0)
    """)

conn.commit()
conn.close()

print(f"Database created: {db_path}")

def main():
    """Main function to initialize database"""
    # The database initialization code above runs when the module is imported
    # This function exists for explicit calls if needed
    pass