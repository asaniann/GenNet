"""
Stream processor for real-time data processing
"""

from typing import Dict, Any, List, Optional
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Process streaming data in real-time"""
    
    def __init__(self):
        """Initialize stream processor"""
        self.window_size = 100  # Number of events in window
        self.windows = {}  # patient_id -> window data
    
    def process_event(
        self,
        event: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single event
        
        Args:
            event: Event data dictionary
            
        Returns:
            Processed event or None
        """
        patient_id = event.get("patient_id")
        event_type = event.get("event_type")
        
        if not patient_id:
            logger.warning("Event missing patient_id")
            return None
        
        # Add to window
        if patient_id not in self.windows:
            self.windows[patient_id] = []
        
        self.windows[patient_id].append(event)
        
        # Maintain window size
        if len(self.windows[patient_id]) > self.window_size:
            self.windows[patient_id].pop(0)
        
        # Process based on event type
        if event_type == "data_upload":
            return self._process_data_upload(event)
        elif event_type == "prediction":
            return self._process_prediction(event)
        elif event_type == "update":
            return self._process_update(event)
        
        return event
    
    def _process_data_upload(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process data upload event"""
        # Extract relevant information
        processed = {
            **event,
            "processed": True,
            "processing_timestamp": pd.Timestamp.now().isoformat()
        }
        return processed
    
    def _process_prediction(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process prediction event"""
        # Add metadata
        processed = {
            **event,
            "processed": True,
            "prediction_timestamp": pd.Timestamp.now().isoformat()
        }
        return processed
    
    def _process_update(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process update event"""
        return event
    
    def get_window_statistics(self, patient_id: str) -> Dict[str, Any]:
        """Get statistics for patient's event window"""
        if patient_id not in self.windows:
            return {}
        
        window = self.windows[patient_id]
        
        if not window:
            return {}
        
        # Calculate statistics
        event_types = [e.get("event_type") for e in window]
        
        return {
            "window_size": len(window),
            "event_types": {et: event_types.count(et) for et in set(event_types)},
            "latest_event": window[-1] if window else None
        }

