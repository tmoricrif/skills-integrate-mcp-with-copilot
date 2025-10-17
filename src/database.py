"""
Database module for Mergington High School Activities System
Handles SQLite database operations and models
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Database path
DB_PATH = Path(__file__).parent / "activities.db"


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        try:
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR UNIQUE NOT NULL,
                    name VARCHAR,
                    grade_level INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create activities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR UNIQUE NOT NULL,
                    description TEXT,
                    schedule VARCHAR,
                    max_participants INTEGER DEFAULT 0,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """)
            
            # Create registrations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    activity_id INTEGER NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (activity_id) REFERENCES activities(id),
                    UNIQUE(user_id, activity_id)
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def migrate_existing_data(self, activities_data: Dict):
        """Migrate existing in-memory data to database"""
        conn = self.get_connection()
        try:
            # Check if activities table is empty
            cursor = conn.execute("SELECT COUNT(*) FROM activities")
            count = cursor.fetchone()[0]
            
            if count == 0:  # Only migrate if table is empty
                print("Migrating existing activity data to database...")
                
                # Insert activities
                for activity_name, activity_data in activities_data.items():
                    cursor = conn.execute(
                        "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
                        (activity_name, activity_data["description"], activity_data["schedule"], activity_data["max_participants"])
                    )
                    activity_id = cursor.lastrowid
                    
                    # Insert participants as users and registrations
                    for participant_email in activity_data["participants"]:
                        # Insert or get user
                        conn.execute(
                            "INSERT OR IGNORE INTO users (email) VALUES (?)",
                            (participant_email,)
                        )
                        
                        # Get user ID
                        user_cursor = conn.execute(
                            "SELECT id FROM users WHERE email = ?",
                            (participant_email,)
                        )
                        user_id = user_cursor.fetchone()[0]
                        
                        # Insert registration
                        conn.execute(
                            "INSERT OR IGNORE INTO registrations (user_id, activity_id) VALUES (?, ?)",
                            (user_id, activity_id)
                        )
                
                conn.commit()
                print("Data migration completed!")
        finally:
            conn.close()


class ActivityRepository:
    """Repository for activity-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_all_activities(self) -> Dict:
        """Get all activities in the original format for backwards compatibility"""
        conn = self.db_manager.get_connection()
        try:
            # Get activities with participant counts
            cursor = conn.execute("""
                SELECT a.*, COUNT(r.user_id) as participant_count
                FROM activities a
                LEFT JOIN registrations r ON a.id = r.activity_id
                GROUP BY a.id, a.name, a.description, a.schedule, a.max_participants
            """)
            
            activities = {}
            for row in cursor.fetchall():
                # Get participants for this activity
                participants_cursor = conn.execute("""
                    SELECT u.email
                    FROM users u
                    JOIN registrations r ON u.id = r.user_id
                    WHERE r.activity_id = ?
                """, (row["id"],))
                
                participants = [p["email"] for p in participants_cursor.fetchall()]
                
                activities[row["name"]] = {
                    "description": row["description"],
                    "schedule": row["schedule"],
                    "max_participants": row["max_participants"],
                    "participants": participants
                }
            
            return activities
        finally:
            conn.close()
    
    def activity_exists(self, activity_name: str) -> bool:
        """Check if an activity exists"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id FROM activities WHERE name = ?",
                (activity_name,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def get_activity_id(self, activity_name: str) -> Optional[int]:
        """Get activity ID by name"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id FROM activities WHERE name = ?",
                (activity_name,)
            )
            row = cursor.fetchone()
            return row["id"] if row else None
        finally:
            conn.close()


class UserRepository:
    """Repository for user-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_or_create_user(self, email: str) -> int:
        """Get existing user or create new one, return user ID"""
        conn = self.db_manager.get_connection()
        try:
            # Try to get existing user
            cursor = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            
            if row:
                return row["id"]
            
            # Create new user
            cursor = conn.execute(
                "INSERT INTO users (email) VALUES (?)",
                (email,)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def is_user_registered(self, user_id: int, activity_id: int) -> bool:
        """Check if user is registered for an activity"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "SELECT id FROM registrations WHERE user_id = ? AND activity_id = ?",
                (user_id, activity_id)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()


class RegistrationRepository:
    """Repository for registration-related database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def register_user(self, user_id: int, activity_id: int):
        """Register a user for an activity"""
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "INSERT INTO registrations (user_id, activity_id) VALUES (?, ?)",
                (user_id, activity_id)
            )
            conn.commit()
        finally:
            conn.close()
    
    def unregister_user(self, user_id: int, activity_id: int):
        """Unregister a user from an activity"""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM registrations WHERE user_id = ? AND activity_id = ?",
                (user_id, activity_id)
            )
            conn.commit()
            return cursor.rowcount > 0  # Return True if a row was deleted
        finally:
            conn.close()


# Global instances
db_manager = DatabaseManager()
activity_repo = ActivityRepository(db_manager)
user_repo = UserRepository(db_manager)
registration_repo = RegistrationRepository(db_manager)