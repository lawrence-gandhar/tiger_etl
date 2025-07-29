"""User groups model for managing user groups and roles.

This module contains SQLAlchemy models for managing user groups
including group creation, updates, and status management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserGroups(Base):
    """SQLAlchemy model for user groups management.
    
    This model manages user groups including group names, status,
    and timestamp tracking for creation and updates.
    
    Attributes:
        id: Primary key with auto-increment
        group_name: Unique group name (cannot be null)
        is_active: Boolean flag for group status (default: True)
        created_on: Timestamp when the group was created (auto-set on creation)
        updated_on: Timestamp when the group was last updated (auto-updated on changes)
    """
    
    __tablename__ = 'user_groups'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Group name - unique and required
    group_name = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True
    )
    
    # Active status - default True
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamp fields
    created_on = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_on = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    user_mappings = relationship("UserGroupMapper", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        """String representation of UserGroups instance."""
        return (
            f"<UserGroups("
            f"id={self.id}, "
            f"group_name='{self.group_name}', "
            f"is_active={self.is_active}, "
            f"created_on={self.created_on}"
            f")>"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Group: {self.group_name} ({'Active' if self.is_active else 'Inactive'})"
    
    def activate(self) -> None:
        """Activate the user group."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the user group."""
        self.is_active = False
    
    def toggle_status(self) -> bool:
        """Toggle the active status of the group.
        
        Returns:
            bool: The new status after toggling
        """
        self.is_active = not self.is_active
        return self.is_active
    
    @property
    def status(self) -> str:
        """Get the current status as a string.
        
        Returns:
            str: 'Active' if is_active is True, 'Inactive' otherwise
        """
        return 'Active' if self.is_active else 'Inactive'
    
    @property
    def age_in_days(self) -> int:
        """Calculate the age of the group in days.
        
        Returns:
            int: Number of days since the group was created
        """
        if self.created_on:
            now = datetime.now(self.created_on.tzinfo) if self.created_on.tzinfo else datetime.now()
            return (now - self.created_on).days
        return 0
    
    def to_dict(self) -> dict:
        """Convert the UserGroups instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the group
        """
        return {
            'id': self.id,
            'group_name': self.group_name,
            'is_active': self.is_active,
            'status': self.status,
            'created_on': self.created_on.isoformat() if self.created_on else None,
            'updated_on': self.updated_on.isoformat() if self.updated_on else None,
            'age_in_days': self.age_in_days,
            'user_count': len(self.user_mappings) if self.user_mappings else 0
        }
    
    def get_active_users(self) -> list:
        """Get list of active user mappings for this group.
        
        Returns:
            list: List of active UserGroupMapper instances
        """
        return [mapping for mapping in self.user_mappings if mapping.is_active]
    
    def get_user_ids(self) -> list:
        """Get list of user IDs that belong to this group.
        
        Returns:
            list: List of user IDs (active mappings only)
        """
        return [mapping.user_id for mapping in self.get_active_users()]
    
    @property
    def active_user_count(self) -> int:
        """Get count of active users in this group.
        
        Returns:
            int: Number of active users in the group
        """
        return len(self.get_active_users())
    

class UserGroupMapper(Base):
    """SQLAlchemy model for mapping users to groups (many-to-many relationship).
    
    This model creates a junction table that maps users to groups, allowing:
    - One user to belong to multiple groups
    - One group to contain multiple users
    
    Attributes:
        id: Primary key with auto-increment
        group_id: Foreign key reference to UserGroups.id
        user_id: Foreign key reference to User.id
        created_on: Timestamp when the mapping was created
        is_active: Boolean flag for mapping status (default: True)
    """
    
    __tablename__ = 'user_group_mapper'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Foreign key to UserGroups
    group_id = Column(
        Integer, 
        ForeignKey('user_groups.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Foreign key to User model
    user_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Active status for the mapping
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamp when the mapping was created
    created_on = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    group = relationship("UserGroups", back_populates="user_mappings")
    user = relationship("User", back_populates="group_mappings")
    
    def __repr__(self) -> str:
        """String representation of UserGroupMapper instance."""
        return (
            f"<UserGroupMapper("
            f"id={self.id}, "
            f"group_id={self.group_id}, "
            f"user_id={self.user_id}, "
            f"is_active={self.is_active}"
            f")>"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "Active" if self.is_active else "Inactive"
        return f"User {self.user_id} -> Group {self.group_id} ({status})"
    
    def activate(self) -> None:
        """Activate the user-group mapping."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Deactivate the user-group mapping."""
        self.is_active = False
    
    def toggle_status(self) -> bool:
        """Toggle the active status of the mapping.
        
        Returns:
            bool: The new status after toggling
        """
        self.is_active = not self.is_active
        return self.is_active
    
    @property
    def status(self) -> str:
        """Get the current status as a string.
        
        Returns:
            str: 'Active' if is_active is True, 'Inactive' otherwise
        """
        return 'Active' if self.is_active else 'Inactive'
    
    def to_dict(self) -> dict:
        """Convert the UserGroupMapper instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the mapping
        """
        return {
            'id': self.id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'status': self.status,
            'created_on': self.created_on.isoformat() if self.created_on else None,
        }