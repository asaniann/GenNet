"""
Enhanced request validation utilities
"""
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import re


class NetworkCreateValidator(BaseModel):
    """Enhanced validation for network creation"""
    name: str = Field(..., min_length=1, max_length=200, description="Network name")
    description: Optional[str] = Field(None, max_length=1000, description="Network description")
    nodes: List[Dict[str, Any]] = Field(..., min_items=1, description="Network nodes")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Network edges")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate network name"""
        if not v or not v.strip():
            raise ValueError('Network name cannot be empty')
        if len(v) > 200:
            raise ValueError('Network name too long (max 200 characters)')
        # Check for potentially dangerous characters
        if re.search(r'[<>"\'\\]', v):
            raise ValueError('Network name contains invalid characters')
        return v.strip()
    
    @validator('nodes')
    def validate_nodes(cls, v):
        """Validate nodes"""
        if not v:
            raise ValueError('Network must have at least one node')
        if len(v) > 10000:
            raise ValueError('Network too large (>10,000 nodes). Consider splitting into smaller networks.')
        
        # Validate node structure
        node_ids = set()
        for node in v:
            if 'id' not in node:
                raise ValueError('All nodes must have an id field')
            node_id = node['id']
            if node_id in node_ids:
                raise ValueError(f'Duplicate node ID: {node_id}')
            node_ids.add(node_id)
        
        return v
    
    @validator('edges')
    def validate_edges(cls, v, values):
        """Validate edges reference valid nodes"""
        if not v:
            return v
        
        # Get node IDs if available
        node_ids = set()
        if 'nodes' in values:
            node_ids = {node.get('id') for node in values['nodes'] if 'id' in node}
        
        for edge in v:
            if 'source' not in edge or 'target' not in edge:
                raise ValueError('All edges must have source and target fields')
            
            if node_ids:
                if edge['source'] not in node_ids:
                    raise ValueError(f'Edge source node {edge["source"]} not found in nodes')
                if edge['target'] not in node_ids:
                    raise ValueError(f'Edge target node {edge["target"]} not found in nodes')
        
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_network_structure(cls, values):
        """Validate overall network structure"""
        nodes = values.get('nodes', [])
        edges = values.get('edges', [])
        
        if len(edges) > len(nodes) * (len(nodes) - 1):
            raise ValueError('Too many edges (more than maximum possible connections)')
        
        return values


class PaginationParams(BaseModel):
    """Pagination parameters with validation"""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(50, ge=1, le=100, description="Number of items to return")
    
    @validator('skip')
    def validate_skip(cls, v):
        if v < 0:
            raise ValueError('skip must be >= 0')
        if v > 10000:
            raise ValueError('skip too large (max 10,000). Use cursor-based pagination for large datasets.')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1:
            raise ValueError('limit must be >= 1')
        if v > 100:
            raise ValueError('limit too large (max 100). Use batch operations for larger datasets.')
        return v


class WorkflowCreateValidator(BaseModel):
    """Enhanced validation for workflow creation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    workflow_type: str = Field(..., pattern='^(qualitative|hybrid|ml)$')
    network_id: str = Field(..., min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('workflow_type')
    def validate_workflow_type(cls, v):
        allowed_types = ['qualitative', 'hybrid', 'ml']
        if v not in allowed_types:
            raise ValueError(f'workflow_type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate parameters based on workflow type"""
        workflow_type = values.get('workflow_type')
        
        if workflow_type == 'qualitative':
            if 'ctl_formula' not in v:
                raise ValueError('qualitative workflows require ctl_formula in parameters')
        elif workflow_type == 'ml':
            if 'expression_data_path' not in v:
                raise ValueError('ml workflows require expression_data_path in parameters')
            if 'method' not in v:
                raise ValueError('ml workflows require method in parameters')
        
        return v


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters (except newline and tab)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()


