# Database Implementation

This document explains the database implementation for the Mergington High School Activities System.

## Overview

The application has been upgraded from in-memory storage to persistent SQLite database storage. This ensures data persistence across server restarts and provides a foundation for more advanced features.

## Database Schema

### Tables

1. **users**
   - `id` (INTEGER PRIMARY KEY) - Unique user identifier
   - `email` (VARCHAR UNIQUE) - User email address
   - `name` (VARCHAR) - User full name (optional)
   - `grade_level` (INTEGER) - Student grade level (optional)
   - `created_at` (TIMESTAMP) - Account creation timestamp

2. **activities**
   - `id` (INTEGER PRIMARY KEY) - Unique activity identifier
   - `name` (VARCHAR UNIQUE) - Activity name
   - `description` (TEXT) - Activity description
   - `schedule` (VARCHAR) - Activity schedule
   - `max_participants` (INTEGER) - Maximum number of participants
   - `created_by` (INTEGER) - User ID of activity creator (optional)
   - `created_at` (TIMESTAMP) - Activity creation timestamp

3. **registrations**
   - `id` (INTEGER PRIMARY KEY) - Unique registration identifier
   - `user_id` (INTEGER) - Foreign key to users table
   - `activity_id` (INTEGER) - Foreign key to activities table
   - `registered_at` (TIMESTAMP) - Registration timestamp
   - UNIQUE constraint on (user_id, activity_id) to prevent duplicate registrations

## Files

- `database.py` - Database management module
  - `DatabaseManager` - Handles database connections and initialization
  - `ActivityRepository` - Activity-related database operations
  - `UserRepository` - User-related database operations
  - `RegistrationRepository` - Registration-related database operations

- `activities.db` - SQLite database file (created automatically)

## Migration

The system automatically migrates existing in-memory data to the database on first run. This ensures backwards compatibility and seamless transition.

## Benefits

1. **Data Persistence** - Data survives server restarts
2. **Data Integrity** - Foreign key relationships and constraints
3. **Scalability** - Foundation for advanced features
4. **Performance** - Indexed queries for better performance
5. **Backup/Recovery** - Database can be backed up and restored

## API Compatibility

All existing API endpoints remain unchanged and fully compatible. The database implementation is transparent to API users.

## Future Enhancements

This database foundation enables:
- User authentication and authorization
- Advanced activity management
- User dashboards and profiles
- Reporting and analytics
- Data backup and recovery procedures