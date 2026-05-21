import sqlite3
import os

def main():
    """Main function to initialize database"""
    # Use the same path as config to avoid multiple databases
    from src.config.settings import config
    db_path = config.get_database_path()
    
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
        ExposureTime INTEGER NOT NULL DEFAULT 10000 CHECK(ExposureTime BETWEEN 100 AND 300000000),
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
        IntegralTime INTEGER NOT NULL DEFAULT 100 CHECK(IntegralTime BETWEEN 1 AND 99999),
        DarkSpectrumPath TEXT DEFAULT '',
        AutoDarkCorrection INTEGER NOT NULL DEFAULT 1 CHECK(AutoDarkCorrection IN (0, 1)),
        OverilluminationThreshold INTEGER NOT NULL DEFAULT 65535 CHECK(OverilluminationThreshold BETWEEN 0 AND 65535),
        LastUpdated TEXT DEFAULT CURRENT_TIMESTAMP
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
    
    # Check if SpectrometerSettings table has the new structure, migrate if needed
    cursor.execute("PRAGMA table_info(SpectrometerSettings)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # If old structure exists, drop and recreate
    if 'parameter1' in columns:
        cursor.execute("DROP TABLE SpectrometerSettings")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS SpectrometerSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            SettingsName TEXT NOT NULL DEFAULT 'Basic',
            IntegralTime INTEGER NOT NULL DEFAULT 100 CHECK(IntegralTime BETWEEN 1 AND 99999),
            DarkSpectrumPath TEXT DEFAULT '',
            AutoDarkCorrection INTEGER NOT NULL DEFAULT 1 CHECK(AutoDarkCorrection IN (0, 1)),
            OverilluminationThreshold INTEGER NOT NULL DEFAULT 65535 CHECK(OverilluminationThreshold BETWEEN 0 AND 65535),
            LastUpdated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
    
    # Insert default spectrometer settings for slot 0 if not exists
    cursor.execute("SELECT COUNT(*) FROM SpectrometerSettings WHERE id = 0")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO SpectrometerSettings (id, SettingsName, IntegralTime, DarkSpectrumPath, AutoDarkCorrection, OverilluminationThreshold, LastUpdated)
        VALUES (0, 'Basic', 100, '', 1, 65535, datetime('now'))
        """)
    
    conn.commit()
    conn.close()
    
    print(f"Database created: {db_path}")

if __name__ == "__main__":
    main()