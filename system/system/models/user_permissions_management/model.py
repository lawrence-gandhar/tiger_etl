"""User permissions model for managing user access rights.

This module contains SQLAlchemy models for managing user permissions
including various access levels for database and application operations.
"""

from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserPermissions(Base):
    """SQLAlchemy model for user permissions management.
    
    This model manages various permission levels for users including
    full access, read, write, create, edit, delete, execute, drop, and view access.
    
    Attributes:
        id: Primary key with auto-increment
        user_id: Foreign key reference to User.id (one-to-many relationship)
        full_access: Boolean flag for full system access
        read_access: Boolean flag for read operations
        write_access: Boolean flag for write operations
        create_access: Boolean flag for create operations
        edit_access: Boolean flag for edit operations
        delete_access: Boolean flag for delete operations
        execute_access: Boolean flag for execute operations
        drop_access: Boolean flag for drop operations
        view_access: Boolean flag for view operations
        insert_access: Boolean flag for insert operations
        update_access: Boolean flag for update operations
    """
    
    __tablename__ = 'user_permissions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Foreign key relationship to User
    user_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    
    # Permission flags - all boolean fields with default False for security
    full_access = Column(Boolean, default=False, nullable=False)
    read_access = Column(Boolean, default=False, nullable=False)
    write_access = Column(Boolean, default=False, nullable=False)
    create_access = Column(Boolean, default=False, nullable=False)
    edit_access = Column(Boolean, default=False, nullable=False)
    execute_access = Column(Boolean, default=False, nullable=False)
    drop_access = Column(Boolean, default=False, nullable=False)
    view_access = Column(Boolean, default=False, nullable=False)
    insert_access = Column(Boolean, default=False, nullable=False)
    update_access = Column(Boolean, default=False, nullable=False)
    delete_access = Column(Boolean, default=False, nullable=False)


    # Relationship back to User (one user can have many permission records)
    user = relationship("User", back_populates="permissions")
    
    def __repr__(self) -> str:
        """String representation of UserPermissions instance."""
        return (
            f"<UserPermissions("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"full_access={self.full_access}, "
            f"read_access={self.read_access}, "
            f"write_access={self.write_access}, "
            f"create_access={self.create_access}, "
            f"edit_access={self.edit_access}, "
            f"execute_access={self.execute_access}, "
            f"drop_access={self.drop_access}, "
            f"view_access={self.view_access}, "
            f"insert_access={self.insert_access}, "
            f"update_access={self.update_access}, "
            f"delete_access={self.delete_access}"
            f")>"
        )
    
    def has_permission(self, permission_type: str) -> bool:
        """Check if user has a specific permission.
        
        Args:
            permission_type: The type of permission to check
            
        Returns:
            bool: True if user has the permission, False otherwise
            
        Raises:
            ValueError: If permission_type is not valid
        """
        valid_permissions = {
            'full_access', 'read_access', 'write_access', 'create_access',
            'edit_access', 'delete_access', 'execute_access', 
            'drop_access', 'view_access', 'insert_access', 'update_access'
        }
        
        if permission_type not in valid_permissions:
            raise ValueError(f"Invalid permission type: {permission_type}")
            
        return getattr(self, permission_type, False)
    
    def grant_permission(self, permission_type: str) -> None:
        """Grant a specific permission to the user.
        
        Args:
            permission_type: The type of permission to grant
            
        Raises:
            ValueError: If permission_type is not valid
        """
        valid_permissions = {
            'full_access', 'read_access', 'write_access', 'create_access',
            'edit_access', 'delete_access', 'execute_access', 
            'drop_access', 'view_access', 'insert_access', 'update_access'
        }
        
        if permission_type not in valid_permissions:
            raise ValueError(f"Invalid permission type: {permission_type}")
            
        setattr(self, permission_type, True)
    
    def revoke_permission(self, permission_type: str) -> None:
        """Revoke a specific permission from the user.
        
        Args:
            permission_type: The type of permission to revoke
            
        Raises:
            ValueError: If permission_type is not valid
        """
        valid_permissions = {
            'full_access', 'read_access', 'write_access', 'create_access',
            'edit_access', 'delete_access', 'execute_access', 
            'drop_access', 'view_access', 'insert_access', 'update_access'
        }
        
        if permission_type not in valid_permissions:
            raise ValueError(f"Invalid permission type: {permission_type}")
            
        setattr(self, permission_type, False)
    
    def get_all_permissions(self) -> dict:
        """Get all permissions as a dictionary.
        
        Returns:
            dict: Dictionary of all permission types and their boolean values
        """
        return {
            'full_access': self.full_access,
            'read_access': self.read_access,
            'write_access': self.write_access,
            'create_access': self.create_access,
            'edit_access': self.edit_access,
            'delete_access': self.delete_access,
            'execute_access': self.execute_access,
            'drop_access': self.drop_access,
            'view_access': self.view_access,
            'insert_access': self.insert_access,
            'update_access': self.update_access
        }