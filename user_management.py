"""
User management and role-based access control module
"""
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import logging
import traceback
from database import get_db_connection
from security import SecurityManager

logger = logging.getLogger(__name__)

class UserManagement:
    def __init__(self):
        self.security_manager = SecurityManager()
        self.init_user_tables()
    
    def init_user_tables(self):
        """Initialize user management tables"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create user activity log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id INTEGER,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("User management tables initialized")
            
            # Create default admin user if none exists
            self.create_default_admin()
            
        except Exception as e:
            logger.error(f"Error initializing user tables: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def create_default_admin(self):
        """Create a default admin user if none exists"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if any users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # Create default admin user
                username = "admin"
                email = "admin@algohub.com"
                password = "Admin123!"  # Should be changed in production
                role = "admin"
                
                password_hash = self.hash_password(password)
                
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                ''', (username, email, password_hash, role))
                
                conn.commit()
                logger.info("Default admin user created (username: admin, password: Admin123!)")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating default admin: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def hash_password(self, password):
        """Hash password using salt"""
        try:
            # Generate a random salt
            salt = secrets.token_hex(16)
            # Hash the password with the salt
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            # Return salt + hash for storage
            return salt + password_hash
        except Exception as e:
            logger.error(f"Error hashing password: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def verify_password(self, password, stored_hash):
        """Verify password against stored hash"""
        try:
            # Extract salt (first 32 characters for hex) and hash
            salt = stored_hash[:32]
            actual_hash = stored_hash[32:]
            
            # Hash the provided password with the stored salt
            provided_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            
            return provided_hash == actual_hash
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def create_user(self, username, email, password, role="viewer"):
        """Create a new user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            existing = cursor.fetchone()
            
            if existing:
                raise ValueError("Username or email already exists")
            
            # Validate role
            valid_roles = ["admin", "accountant", "viewer"]
            if role not in valid_roles:
                raise ValueError(f"Invalid role. Valid roles: {valid_roles}")
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"User {username} created with role {role}")
            return user_id
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, role, is_active
                FROM users 
                WHERE username = ? OR email = ?
            ''', (username, username))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and user[4]:  # Check if user exists and is active
                user_id, username, stored_hash, role, is_active = user
                if self.verify_password(password, stored_hash):
                    # Update last login
                    self.update_last_login(user_id)
                    logger.info(f"User {username} authenticated successfully")
                    return {"id": user_id, "username": username, "role": role}
            
            logger.warning(f"Failed authentication attempt for user: {username}")
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def update_last_login(self, user_id):
        """Update user's last login time"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating last login for user {user_id}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users 
                WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "role": user[3],
                    "created_at": user[4],
                    "last_login": user[5],
                    "is_active": user[6]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def update_user_role(self, user_id, new_role):
        """Update user role"""
        try:
            valid_roles = ["admin", "accountant", "viewer"]
            if new_role not in valid_roles:
                raise ValueError(f"Invalid role. Valid roles: {valid_roles}")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET role = ? 
                WHERE id = ?
            ''', (new_role, user_id))
            
            if cursor.rowcount == 0:
                raise ValueError(f"User with ID {user_id} not found")
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {user_id} role updated to {new_role}")
            
        except Exception as e:
            logger.error(f"Error updating role for user {user_id}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def delete_user(self, user_id):
        """Delete a user"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            if cursor.rowcount == 0:
                raise ValueError(f"User with ID {user_id} not found")
            
            conn.commit()
            conn.close()
            
            logger.info(f"User {user_id} deleted")
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def log_user_activity(self, user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None, user_agent=None):
        """Log user activity"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_activity 
                (user_id, action, entity_type, entity_id, details, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, action, entity_type, entity_id, details, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Activity logged for user {user_id}: {action}")
            
        except Exception as e:
            logger.error(f"Error logging user activity: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def get_user_activity(self, user_id, limit=50):
        """Get user activity log"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT action, entity_type, entity_id, details, timestamp
                FROM user_activity
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            activities = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "action": act[0],
                    "entity_type": act[1],
                    "entity_id": act[2],
                    "details": act[3],
                    "timestamp": act[4]
                }
                for act in activities
            ]
            
        except Exception as e:
            logger.error(f"Error getting user activity for user {user_id}: {str(e)}\n{traceback.format_exc()}")
            raise e
    
    def get_all_users(self):
        """Get all users"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, email, role, created_at, last_login, is_active
                FROM users
                ORDER BY created_at DESC
            ''')
            
            users = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "role": user[3],
                    "created_at": user[4],
                    "last_login": user[5],
                    "is_active": user[6]
                }
                for user in users
            ]
            
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}\n{traceback.format_exc()}")
            raise e

# Role-based access control helper functions
def has_permission(user_role, required_role):
    """Check if user has required permission level"""
    role_hierarchy = {
        "viewer": 1,
        "accountant": 2,
        "admin": 3
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def require_role(required_role):
    """Decorator to require specific role for functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be implemented in the Streamlit app to check user permissions
            # For now, we'll just return the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator