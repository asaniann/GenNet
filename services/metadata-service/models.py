"""Metadata models"""

from sqlalchemy import Column, String, Text, JSON, DateTime, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class MetadataEntry(Base):
    __tablename__ = "metadata_entries"
    __table_args__ = (
        Index('idx_metadata_resource_type', 'resource_type'),
        Index('idx_metadata_resource_id', 'resource_id'),
        Index('idx_metadata_created_at', 'created_at'),
        Index('idx_metadata_resource', 'resource_type', 'resource_id'),
    )
    
    id = Column(String, primary_key=True)
    resource_type = Column(String)
    resource_id = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

