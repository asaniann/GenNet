"""
Workflow templates for reusable workflow configurations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

# Try to import SQLAlchemy
try:
    from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Index
    from sqlalchemy.ext.declarative import declarative_base
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None


class TemplateCategory(str, Enum):
    """Template categories"""
    QUALITATIVE = "qualitative"
    HYBRID = "hybrid"
    ML = "ml"
    STANDARD = "standard"
    CUSTOM = "custom"


if SQLALCHEMY_AVAILABLE:
    class WorkflowTemplate(Base):
        """Workflow template model"""
        __tablename__ = "workflow_templates"
        __table_args__ = (
            Index('idx_template_category', 'category'),
            Index('idx_template_owner', 'owner_id'),
            Index('idx_template_public', 'is_public'),
        )
        
        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text)
        category = Column(String, nullable=False)
        workflow_type = Column(String, nullable=False)  # qualitative, hybrid, ml
        template_config = Column(JSON, nullable=False)  # Template configuration
        default_parameters = Column(JSON)  # Default parameters
        is_public = Column(Boolean, default=False)
        owner_id = Column(Integer, nullable=False, index=True)
        usage_count = Column(Integer, default=0)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
else:
    # Placeholder for when SQLAlchemy not available
    class WorkflowTemplate:
        pass


class TemplateManager:
    """
    Manages workflow templates
    
    Features:
    - Template creation and storage
    - Template discovery (public/private)
    - Template instantiation
    - Usage tracking
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self._in_memory_templates: Dict[str, Dict[str, Any]] = {}
    
    def create_template(
        self,
        name: str,
        workflow_type: str,
        template_config: Dict[str, Any],
        owner_id: int,
        description: Optional[str] = None,
        category: TemplateCategory = TemplateCategory.STANDARD,
        default_parameters: Optional[Dict[str, Any]] = None,
        is_public: bool = False
    ) -> str:
        """Create a new workflow template"""
        import uuid
        template_id = str(uuid.uuid4())
        
        if self.db_session and SQLALCHEMY_AVAILABLE:
            template = WorkflowTemplate(
                id=template_id,
                name=name,
                description=description,
                category=category.value,
                workflow_type=workflow_type,
                template_config=template_config,
                default_parameters=default_parameters or {},
                is_public=is_public,
                owner_id=owner_id,
                created_at=datetime.utcnow()
            )
            self.db_session.add(template)
            self.db_session.commit()
        else:
            # In-memory storage
            self._in_memory_templates[template_id] = {
                "id": template_id,
                "name": name,
                "description": description,
                "category": category.value,
                "workflow_type": workflow_type,
                "template_config": template_config,
                "default_parameters": default_parameters or {},
                "is_public": is_public,
                "owner_id": owner_id,
                "usage_count": 0,
                "created_at": datetime.utcnow()
            }
        
        logger.info(f"Workflow template created: {name} ({template_id})")
        return template_id
    
    def get_template(self, template_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a template by ID"""
        if self.db_session and SQLALCHEMY_AVAILABLE:
            query = self.db_session.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id)
            
            # Check access (public or owned by user)
            if user_id:
                query = query.filter(
                    (WorkflowTemplate.is_public == True) | (WorkflowTemplate.owner_id == user_id)
                )
            else:
                query = query.filter(WorkflowTemplate.is_public == True)
            
            template = query.first()
            if template:
                return {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "workflow_type": template.workflow_type,
                    "template_config": template.template_config,
                    "default_parameters": template.default_parameters,
                    "is_public": template.is_public,
                    "owner_id": template.owner_id,
                    "usage_count": template.usage_count,
                    "created_at": template.created_at.isoformat() if template.created_at else None
                }
        else:
            # Check in-memory
            if template_id in self._in_memory_templates:
                template = self._in_memory_templates[template_id]
                if user_id and not template["is_public"] and template["owner_id"] != user_id:
                    return None
                return template
        
        return None
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        workflow_type: Optional[str] = None,
        user_id: Optional[int] = None,
        public_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List available templates"""
        if self.db_session and SQLALCHEMY_AVAILABLE:
            query = self.db_session.query(WorkflowTemplate)
            
            if public_only or (user_id is None):
                query = query.filter(WorkflowTemplate.is_public == True)
            elif user_id:
                query = query.filter(
                    (WorkflowTemplate.is_public == True) | (WorkflowTemplate.owner_id == user_id)
                )
            
            if category:
                query = query.filter(WorkflowTemplate.category == category.value)
            if workflow_type:
                query = query.filter(WorkflowTemplate.workflow_type == workflow_type)
            
            templates = query.order_by(WorkflowTemplate.usage_count.desc()).all()
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "workflow_type": t.workflow_type,
                    "is_public": t.is_public,
                    "owner_id": t.owner_id,
                    "usage_count": t.usage_count,
                    "created_at": t.created_at.isoformat() if t.created_at else None
                }
                for t in templates
            ]
        else:
            # In-memory listing
            templates = list(self._in_memory_templates.values())
            
            if public_only or user_id is None:
                templates = [t for t in templates if t["is_public"]]
            elif user_id:
                templates = [t for t in templates if t["is_public"] or t["owner_id"] == user_id]
            
            if category:
                templates = [t for t in templates if t["category"] == category.value]
            if workflow_type:
                templates = [t for t in templates if t["workflow_type"] == workflow_type]
            
            templates.sort(key=lambda t: t["usage_count"], reverse=True)
            return templates
    
    def instantiate_template(
        self,
        template_id: str,
        network_id: str,
        user_id: int,
        override_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Instantiate a workflow from a template
        
        Returns:
            Dict with workflow creation data
        """
        template = self.get_template(template_id, user_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Merge default parameters with overrides
        parameters = template["default_parameters"].copy()
        if override_parameters:
            parameters.update(override_parameters)
        
        # Increment usage count
        if self.db_session and SQLALCHEMY_AVAILABLE:
            template_record = self.db_session.query(WorkflowTemplate).filter(
                WorkflowTemplate.id == template_id
            ).first()
            if template_record:
                template_record.usage_count += 1
                self.db_session.commit()
        else:
            if template_id in self._in_memory_templates:
                self._in_memory_templates[template_id]["usage_count"] += 1
        
        # Build workflow creation data
        workflow_data = {
            "name": template["template_config"].get("name", template["name"]),
            "description": template["description"],
            "workflow_type": template["workflow_type"],
            "network_id": network_id,
            "parameters": parameters
        }
        
        # Apply template configuration
        if "workflow_config" in template["template_config"]:
            workflow_data.update(template["template_config"]["workflow_config"])
        
        logger.info(f"Template {template_id} instantiated by user {user_id}")
        return workflow_data


# Global instance
_template_manager: Optional[TemplateManager] = None


def get_template_manager(db_session=None) -> TemplateManager:
    """Get or create global template manager"""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager(db_session=db_session)
    return _template_manager

