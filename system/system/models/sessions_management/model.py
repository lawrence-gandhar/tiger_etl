"""Session management model for TimescaleDB with hypertable support.

This module contains SQLAlchemy models for managing user sessions with TimescaleDB
optimizations including hypertable creation and time-series data management.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Index, Boolean, Text, event, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.engine import Engine

Base = declarative_base()


class UserSession(Base):
    """SQLAlchemy model for user session management with TimescaleDB support.
    
    This model manages user sessions with time-series optimizations for TimescaleDB.
    It tracks login/logout times, session status, and additional metadata.
    
    Attributes:
        id: Primary key with auto-increment
        user_id: Foreign key reference to User.id
        session_id: Unique session identifier (UUID or token)
        login_datetime: Timestamp when user logged in (with timezone, indexed)
        logout_datetime: Timestamp when user logged out (nullable, with timezone)
        is_active: Boolean flag for session status (default: True)
        ip_address: Client IP address (optional)
        user_agent: Client user agent string (optional)
        device_info: Additional device information (optional)
        last_activity: Timestamp of last user activity (auto-updated)
        session_duration: Calculated session duration in seconds (computed)
    """
    
    __tablename__ = 'user_sessions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Foreign key to User model
    user_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Unique session identifier
    session_id = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Unique session identifier (UUID or token)"
    )
    
    # Login timestamp - PRIMARY TIME DIMENSION for TimescaleDB hypertable
    login_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Login timestamp (primary time dimension)"
    )
    
    # Logout timestamp - nullable for active sessions
    logout_datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Logout timestamp (null for active sessions)"
    )
    
    # Session status
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
        index=True,
        comment="Session active status"
    )
    
    # Client information
    ip_address = Column(
        String(45),  # Supports IPv6
        nullable=True,
        index=True,
        comment="Client IP address (IPv4 or IPv6)"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client user agent string"
    )
    
    device_info = Column(
        Text,
        nullable=True,
        comment="Additional device information (JSON or text)"
    )
    
    # Activity tracking
    last_activity = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
        comment="Last activity timestamp (auto-updated)"
    )
    
    # Computed session duration (in seconds)
    # This will be calculated in application logic or database triggers
    session_duration = Column(
        Integer,
        nullable=True,
        comment="Session duration in seconds (computed)"
    )
    
    # Additional indexes for TimescaleDB optimization
    __table_args__ = (
        # Primary time-based index (most important for TimescaleDB)
        Index('idx_user_sessions_login_time', 'login_datetime'),
        
        # Composite indexes for common queries
        Index('idx_user_sessions_user_login', 'user_id', 'login_datetime'),
        Index('idx_user_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_user_sessions_active_login', 'is_active', 'login_datetime'),
        
        # Session lookup indexes
        Index('idx_user_sessions_session_id', 'session_id'),
        Index('idx_user_sessions_user_session', 'user_id', 'session_id'),
        
        # Activity and logout indexes
        Index('idx_user_sessions_last_activity', 'last_activity'),
        Index('idx_user_sessions_logout_time', 'logout_datetime'),
        
        # IP address index for security monitoring
        Index('idx_user_sessions_ip_address', 'ip_address'),
        
        # Time range queries optimization
        Index('idx_user_sessions_time_range', 'login_datetime', 'logout_datetime'),
    )
    
    # Relationship to User model
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        """String representation of UserSession instance."""
        status = "Active" if self.is_active else "Inactive"
        duration = f", duration={self.session_duration}s" if self.session_duration else ""
        return (
            f"<UserSession("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"session_id='{self.session_id[:8]}...', "
            f"login={self.login_datetime.isoformat() if self.login_datetime else 'None'}, "
            f"status={status}"
            f"{duration}"
            f")>"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "Active" if self.is_active else "Ended"
        login_str = self.login_datetime.strftime('%Y-%m-%d %H:%M:%S UTC') if self.login_datetime else 'Unknown'
        return f"Session {self.session_id[:8]}... ({status}) - Login: {login_str}"
    
    def activate(self) -> None:
        """Activate the session and update last activity."""
        self.is_active = True
        self.last_activity = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Deactivate the session and set logout time."""
        self.is_active = False
        self.logout_datetime = datetime.now(timezone.utc)
        self._calculate_duration()
    
    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)
    
    def logout(self) -> None:
        """End the session by setting logout time and deactivating."""
        if self.is_active:
            self.logout_datetime = datetime.now(timezone.utc)
            self.is_active = False
            self._calculate_duration()
    
    def _calculate_duration(self) -> None:
        """Calculate and set session duration in seconds."""
        if self.login_datetime and self.logout_datetime:
            delta = self.logout_datetime - self.login_datetime
            self.session_duration = int(delta.total_seconds())
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Get session duration in seconds.
        
        Returns:
            Optional[int]: Duration in seconds, or None if session is still active
        """
        if self.session_duration:
            return self.session_duration
        elif self.login_datetime and self.logout_datetime:
            delta = self.logout_datetime - self.login_datetime
            return int(delta.total_seconds())
        return None
    
    @property
    def current_duration_seconds(self) -> Optional[int]:
        """Get current session duration in seconds (for active sessions).
        
        Returns:
            Optional[int]: Current duration in seconds
        """
        if self.login_datetime:
            end_time = self.logout_datetime or datetime.now(timezone.utc)
            delta = end_time - self.login_datetime
            return int(delta.total_seconds())
        return None
    
    @property
    def status(self) -> str:
        """Get the current session status as a string.
        
        Returns:
            str: 'Active' if is_active is True, 'Ended' otherwise
        """
        return 'Active' if self.is_active else 'Ended'
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired based on inactivity.
        
        Note: This is a basic check. Implement your own expiration logic.
        
        Returns:
            bool: True if session appears expired
        """
        if not self.is_active:
            return True
        
        if self.last_activity:
            # Example: Consider session expired after 24 hours of inactivity
            inactive_hours = (datetime.now(timezone.utc) - self.last_activity).total_seconds() / 3600
            return inactive_hours > 24
        
        return False
    
    def to_dict(self) -> dict:
        """Convert the UserSession instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the session
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'login_datetime': self.login_datetime.isoformat() if self.login_datetime else None,
            'logout_datetime': self.logout_datetime.isoformat() if self.logout_datetime else None,
            'is_active': self.is_active,
            'status': self.status,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_info': self.device_info,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'session_duration': self.session_duration,
            'current_duration_seconds': self.current_duration_seconds,
            'is_expired': self.is_expired
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserSession':
        """Create a UserSession instance from a dictionary.
        
        Args:
            data: Dictionary containing session data
            
        Returns:
            UserSession: New session instance
        """
        return cls(
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            login_datetime=data.get('login_datetime'),
            logout_datetime=data.get('logout_datetime'),
            is_active=data.get('is_active', True),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            device_info=data.get('device_info'),
            last_activity=data.get('last_activity')
        )


# TimescaleDB Hypertable Creation Functions
def create_hypertable(engine: Engine, chunk_time_interval: str = '1 day') -> None:
    """Create TimescaleDB hypertable for user_sessions table.
    
    This function creates a hypertable optimized for time-series data storage
    with automatic partitioning based on the login_datetime column.
    
    Args:
        engine: SQLAlchemy engine connected to TimescaleDB
        chunk_time_interval: Time interval for chunk partitioning (default: '1 day')
    
    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine('postgresql://user:pass@localhost/db')
        >>> create_hypertable(engine, '1 day')
    """
    
    # SQL to create hypertable
    create_hypertable_sql = f"""
    -- Create hypertable for user_sessions
    SELECT create_hypertable(
        'user_sessions',
        'login_datetime',
        chunk_time_interval => INTERVAL '{chunk_time_interval}',
        if_not_exists => TRUE
    );
    """
    
    # Additional TimescaleDB optimizations
    optimization_sql = """
    -- Create additional indexes for time-series queries
    CREATE INDEX IF NOT EXISTS idx_user_sessions_login_time_hash 
    ON user_sessions USING HASH (date_trunc('hour', login_datetime));
    
    -- Create index for user activity analysis
    CREATE INDEX IF NOT EXISTS idx_user_sessions_user_time_active 
    ON user_sessions (user_id, login_datetime, is_active) 
    WHERE is_active = true;
    
    -- Create index for session duration analysis
    CREATE INDEX IF NOT EXISTS idx_user_sessions_duration 
    ON user_sessions (session_duration) 
    WHERE session_duration IS NOT NULL;
    
    -- Create index for IP-based security analysis
    CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_time 
    ON user_sessions (ip_address, login_datetime) 
    WHERE ip_address IS NOT NULL;
    """
    
    with engine.connect() as conn:
        try:
            # Create hypertable
            conn.execute(text(create_hypertable_sql))
            print(f"✅ Hypertable created successfully with {chunk_time_interval} chunks")
            
            # Apply optimizations
            conn.execute(text(optimization_sql))
            print("✅ TimescaleDB optimizations applied successfully")
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error creating hypertable: {e}")
            conn.rollback()
            raise


def setup_compression_policy(engine: Engine, compress_after: str = '7 days') -> None:
    """Setup compression policy for older session data.
    
    Args:
        engine: SQLAlchemy engine connected to TimescaleDB
        compress_after: Time after which to compress data (default: '7 days')
    """
    
    compression_sql = f"""
    -- Enable compression on user_sessions hypertable
    ALTER TABLE user_sessions SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'user_id',
        timescaledb.compress_orderby = 'login_datetime DESC'
    );
    
    -- Create compression policy
    SELECT add_compression_policy(
        'user_sessions',
        INTERVAL '{compress_after}',
        if_not_exists => TRUE
    );
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(compression_sql))
            print(f"✅ Compression policy set up to compress data older than {compress_after}")
            conn.commit()
        except Exception as e:
            print(f"❌ Error setting up compression: {e}")
            conn.rollback()
            raise


def setup_retention_policy(engine: Engine, retain_for: str = '1 year') -> None:
    """Setup data retention policy for session data.
    
    Args:
        engine: SQLAlchemy engine connected to TimescaleDB
        retain_for: Time to retain data (default: '1 year')
    """
    
    retention_sql = f"""
    -- Create retention policy to automatically drop old data
    SELECT add_retention_policy(
        'user_sessions',
        INTERVAL '{retain_for}',
        if_not_exists => TRUE
    );
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(retention_sql))
            print(f"✅ Retention policy set up to retain data for {retain_for}")
            conn.commit()
        except Exception as e:
            print(f"❌ Error setting up retention policy: {e}")
            conn.rollback()
            raise


# SQLAlchemy event listeners for automatic hypertable creation
@event.listens_for(UserSession.__table__, 'after_create')
def create_hypertable_after_table_creation(target, connection, **kw):
    """Automatically create hypertable after table creation."""
    try:
        # Note: This requires the connection to be to a TimescaleDB instance
        create_hypertable_sql = """
        SELECT create_hypertable(
            'user_sessions',
            'login_datetime',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
        """
        connection.execute(text(create_hypertable_sql))
        print("✅ Hypertable created automatically after table creation")
    except Exception as e:
        print(f"⚠️  Could not create hypertable automatically: {e}")
        print("💡 Make sure you're using TimescaleDB and create hypertable manually")
