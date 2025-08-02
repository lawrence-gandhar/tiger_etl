from sqlalchemy import Column, Integer, String, Text, DateTime, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Resource(Base):
    __tablename__ = 'resources'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    resource_uuid = Column(String(50), unique=True, nullable=False, index=True)
    resource_name = Column(String(200), unique=True, nullable=False)
    created_on = Column(DateTime, nullable=False, default=func.now())
    updated_on = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional indexes for better performance
    __table_args__ = (
        Index('idx_resource_uuid', 'resource_uuid'),
        Index('idx_resource_name', 'resource_name'),
        Index('idx_created_on', 'created_on'),
        Index('idx_updated_on', 'updated_on'),
    )
    
    def __repr__(self):
        return f"<Resource(id={self.id}, resource_uuid='{self.resource_uuid}', resource_name='{self.resource_name}')>"
    
    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            'id': self.id,
            'resource_uuid': self.resource_uuid,
            'resource_name': self.resource_name,
            'created_on': self.created_on.isoformat() if self.created_on else None,
            'updated_on': self.updated_on.isoformat() if self.updated_on else None,
            'description': self.description,
            'is_active': self.is_active
        }
    
