"""
Data models for GRN service
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

Base = declarative_base()


class GRNNetwork(Base):
    """GRN Network database model"""
    __tablename__ = "grn_networks"
    __table_args__ = (
        Index('idx_grn_owner_id', 'owner_id'),
        Index('idx_grn_created_at', 'created_at'),
        Index('idx_grn_name', 'name'),
        Index('idx_grn_owner_created', 'owner_id', 'created_at'),
    )
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    owner_id = Column(Integer, nullable=False)  # User ID from auth service (no FK constraint)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Non-database fields (loaded from Neo4j)
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []


class Node(BaseModel):
    """Network node model"""
    id: str
    label: str
    node_type: str = "gene"  # gene, protein, regulatory_element
    properties: Optional[Dict[str, Any]] = None


class Edge(BaseModel):
    """Network edge model"""
    source: str
    target: str
    edge_type: str = "regulates"  # activates, inhibits, regulates
    weight: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None


class GRNNetworkCreate(BaseModel):
    """GRN Network creation model"""
    name: str
    description: Optional[str] = None
    nodes: List[Node]
    edges: List[Edge]


class GRNNetworkResponse(BaseModel):
    """GRN Network response model"""
    id: str
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True


class PatientGRN(Base):
    """Patient-specific GRN database model"""
    __tablename__ = "patient_grns"
    __table_args__ = (
        Index('idx_patient_grn_patient_id', 'patient_id'),
        Index('idx_patient_grn_network_id', 'network_id'),
        Index('idx_patient_grn_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, index=True)
    patient_id = Column(String, nullable=False, index=True)
    network_id = Column(String, ForeignKey("grn_networks.id"), nullable=False, index=True)
    method = Column(String, nullable=False)  # "reference", "de_novo", "hybrid"
    reference_grn_id = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    network = relationship("GRNNetwork", backref="patient_grns")


class PatientGRNCreate(BaseModel):
    """Patient GRN creation model"""
    patient_id: str
    method: str = "hybrid"  # "reference", "de_novo", "hybrid"
    reference_grn_id: Optional[str] = None


class PatientGRNResponse(BaseModel):
    """Patient GRN response model"""
    id: str
    patient_id: str
    network_id: str
    method: str
    reference_grn_id: Optional[str]
    created_at: datetime
    network: Optional[GRNNetworkResponse] = None
    
    class Config:
        from_attributes = True

