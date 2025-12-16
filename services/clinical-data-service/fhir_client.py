"""
FHIR client for clinical data integration
"""

import os
from typing import Optional, Dict, Any, List
import logging
from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation
from fhirclient.models.condition import Condition
from fhirclient.models.medicationstatement import MedicationStatement

logger = logging.getLogger(__name__)


class FHIRClient:
    """FHIR client for clinical data integration"""
    
    def __init__(self, server_url: Optional[str] = None):
        """Initialize FHIR client"""
        self.server_url = server_url or os.getenv("FHIR_SERVER_URL", "http://hapi.fhir.org/baseR4")
        self.settings = {
            'app_id': 'gennet-clinical-service',
            'api_base': self.server_url
        }
        self.fhir_client = client.FHIRClient(settings=self.settings)
    
    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patient from FHIR server
        
        Args:
            patient_id: FHIR patient ID
            
        Returns:
            Patient data dictionary
        """
        try:
            patient = Patient.read(patient_id, self.fhir_client.server)
            
            return {
                "id": patient.id,
                "name": self._extract_name(patient.name[0]) if patient.name else None,
                "gender": patient.gender,
                "birth_date": str(patient.birthDate) if patient.birthDate else None,
                "address": self._extract_address(patient.address[0]) if patient.address else None
            }
        except Exception as e:
            logger.error(f"Error fetching patient from FHIR: {e}")
            return None
    
    def get_observations(self, patient_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get observations (lab results, vital signs) for a patient
        
        Args:
            patient_id: FHIR patient ID
            category: Optional category filter (e.g., "laboratory", "vital-signs")
            
        Returns:
            List of observation dictionaries
        """
        try:
            search_params = {"subject": f"Patient/{patient_id}"}
            if category:
                search_params["category"] = category
            
            observations = Observation.where(search_params).perform(self.fhir_client.server)
            
            results = []
            for obs in observations.resource.entry or []:
                obs_resource = obs.resource
                results.append({
                    "id": obs_resource.id,
                    "code": self._extract_code(obs_resource.code),
                    "value": self._extract_value(obs_resource),
                    "unit": self._extract_unit(obs_resource),
                    "effective_date": str(obs_resource.effectiveDateTime) if obs_resource.effectiveDateTime else None,
                    "status": obs_resource.status
                })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching observations from FHIR: {e}")
            return []
    
    def get_conditions(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get conditions (diagnoses) for a patient"""
        try:
            search_params = {"subject": f"Patient/{patient_id}"}
            conditions = Condition.where(search_params).perform(self.fhir_client.server)
            
            results = []
            for cond in conditions.resource.entry or []:
                cond_resource = cond.resource
                results.append({
                    "id": cond_resource.id,
                    "code": self._extract_code(cond_resource.code),
                    "onset_date": str(cond_resource.onsetDateTime) if cond_resource.onsetDateTime else None,
                    "severity": self._extract_severity(cond_resource)
                })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching conditions from FHIR: {e}")
            return []
    
    def get_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get medications for a patient"""
        try:
            search_params = {"subject": f"Patient/{patient_id}"}
            medications = MedicationStatement.where(search_params).perform(self.fhir_client.server)
            
            results = []
            for med in medications.resource.entry or []:
                med_resource = med.resource
                results.append({
                    "id": med_resource.id,
                    "medication": self._extract_medication(med_resource.medicationCodeableConcept),
                    "status": med_resource.status,
                    "dosage": self._extract_dosage(med_resource)
                })
            
            return results
        except Exception as e:
            logger.error(f"Error fetching medications from FHIR: {e}")
            return []
    
    def _extract_name(self, name) -> str:
        """Extract name from FHIR HumanName"""
        if name:
            parts = []
            if name.given:
                parts.extend(name.given)
            if name.family:
                parts.append(name.family)
            return " ".join(parts)
        return ""
    
    def _extract_address(self, address) -> Dict[str, Any]:
        """Extract address from FHIR Address"""
        if address:
            return {
                "line": address.line[0] if address.line else "",
                "city": address.city or "",
                "state": address.state or "",
                "postal_code": address.postalCode or "",
                "country": address.country or ""
            }
        return {}
    
    def _extract_code(self, codeable_concept) -> Dict[str, Any]:
        """Extract code from FHIR CodeableConcept"""
        if codeable_concept and codeable_concept.coding:
            coding = codeable_concept.coding[0]
            return {
                "system": coding.system or "",
                "code": coding.code or "",
                "display": coding.display or ""
            }
        return {}
    
    def _extract_value(self, observation) -> Optional[float]:
        """Extract value from FHIR Observation"""
        if observation.valueQuantity:
            return float(observation.valueQuantity.value) if observation.valueQuantity.value else None
        return None
    
    def _extract_unit(self, observation) -> Optional[str]:
        """Extract unit from FHIR Observation"""
        if observation.valueQuantity:
            return observation.valueQuantity.unit or observation.valueQuantity.code
        return None
    
    def _extract_severity(self, condition) -> Optional[str]:
        """Extract severity from FHIR Condition"""
        if condition.severity and condition.severity.coding:
            return condition.severity.coding[0].display
        return None
    
    def _extract_medication(self, medication) -> Dict[str, Any]:
        """Extract medication from FHIR CodeableConcept"""
        return self._extract_code(medication) if medication else {}
    
    def _extract_dosage(self, medication_statement) -> Optional[str]:
        """Extract dosage from FHIR MedicationStatement"""
        if medication_statement.dosage and medication_statement.dosage[0]:
            dosage = medication_statement.dosage[0]
            if dosage.text:
                return dosage.text
        return None

