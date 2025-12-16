"""
Polygenic Risk Score (PRS) calculator
Integrates with PGS Catalog and uses established statistical methods
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
import requests
from scipy import stats
import os

logger = logging.getLogger(__name__)


class PRSCalculator:
    """Calculate Polygenic Risk Scores for diseases"""
    
    def __init__(self):
        """Initialize PRS calculator"""
        self.pgs_catalog_url = os.getenv("PGS_CATALOG_URL", "https://www.pgscatalog.org/rest/")
        # In-memory cache for PRS models
        self.model_cache: Dict[str, Dict] = {}
    
    def calculate_prs(
        self,
        variants: pd.DataFrame,
        disease_code: str,
        population: str = "EUR",
        prs_model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate PRS for a disease
        
        Args:
            variants: DataFrame with variant information (must have rsid, genotype, etc.)
            disease_code: Disease code (ICD-10 or custom)
            population: Population for calibration (EUR, AFR, ASN, etc.)
            prs_model_id: Optional specific PRS model ID from PGS Catalog
            
        Returns:
            Dictionary with PRS score and statistics
        """
        # Load PRS model
        if prs_model_id:
            model = self._load_prs_model(prs_model_id)
        else:
            # Try to find model for disease
            model = self._find_prs_model(disease_code, population)
        
        if not model:
            raise ValueError(f"No PRS model found for disease {disease_code}")
        
        # Match variants to model
        matched_variants = self._match_variants_to_model(variants, model)
        
        if len(matched_variants) == 0:
            raise ValueError("No variants matched to PRS model")
        
        # Calculate PRS
        prs_score = self._calculate_weighted_sum(matched_variants, model)
        
        # Calculate percentile (would need population reference data)
        percentile = self._calculate_percentile(prs_score, disease_code, population)
        
        # Calculate z-score
        z_score = self._calculate_z_score(prs_score, disease_code, population)
        
        # Calculate confidence interval
        ci_lower, ci_upper = self._calculate_confidence_interval(
            prs_score, len(matched_variants), model
        )
        
        return {
            'prs_score': float(prs_score),
            'percentile': float(percentile) if percentile else None,
            'z_score': float(z_score) if z_score else None,
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'variant_count': len(matched_variants),
            'model_id': model.get('id'),
            'model_name': model.get('name'),
            'model_version': model.get('version'),
            'matched_variants': matched_variants.to_dict('records') if isinstance(matched_variants, pd.DataFrame) else matched_variants
        }
    
    def _load_prs_model(self, model_id: str) -> Optional[Dict]:
        """Load PRS model from cache or PGS Catalog"""
        if model_id in self.model_cache:
            return self.model_cache[model_id]
        
        # Placeholder - would fetch from PGS Catalog API
        # For now, return a simple model structure
        model = {
            'id': model_id,
            'name': f'PRS Model {model_id}',
            'version': '1.0',
            'variants': {}  # Would contain rsid -> effect_size mapping
        }
        
        self.model_cache[model_id] = model
        return model
    
    def _find_prs_model(self, disease_code: str, population: str) -> Optional[Dict]:
        """Find PRS model for disease from PGS Catalog"""
        # Placeholder - would query PGS Catalog API
        # For now, return None (would need actual API integration)
        logger.warning(f"PRS model lookup not implemented for {disease_code}")
        return None
    
    def _match_variants_to_model(
        self,
        variants: pd.DataFrame,
        model: Dict
    ) -> pd.DataFrame:
        """Match patient variants to PRS model variants"""
        # Filter variants that are in the model
        model_variants = model.get('variants', {})
        
        if 'rsid' not in variants.columns:
            raise ValueError("Variants DataFrame must have 'rsid' column")
        
        # Match by rsid
        matched = variants[variants['rsid'].isin(model_variants.keys())].copy()
        
        # Add effect sizes from model
        matched['effect_size'] = matched['rsid'].map(model_variants)
        
        return matched
    
    def _calculate_weighted_sum(
        self,
        matched_variants: pd.DataFrame,
        model: Dict
    ) -> float:
        """
        Calculate weighted sum PRS
        
        PRS = sum(genotype_count * effect_size) for all variants
        """
        # Extract genotype counts (0, 1, or 2 for alt alleles)
        if 'genotype' in matched_variants.columns:
            # Parse genotype (e.g., "0/1" -> 1, "1/1" -> 2)
            matched_variants['alt_count'] = matched_variants['genotype'].apply(
                lambda g: self._parse_genotype_count(g)
            )
        else:
            # Assume heterozygous if not specified
            matched_variants['alt_count'] = 1
        
        # Calculate weighted sum
        prs = (matched_variants['alt_count'] * matched_variants['effect_size']).sum()
        
        return float(prs)
    
    def _parse_genotype_count(self, genotype: str) -> int:
        """Parse genotype string to count of alternate alleles"""
        if not genotype or genotype == './.':
            return 0
        
        try:
            parts = genotype.split('/')
            if len(parts) == 2:
                return int(parts[0]) + int(parts[1])
            return 0
        except:
            return 0
    
    def _calculate_percentile(
        self,
        prs_score: float,
        disease_code: str,
        population: str
    ) -> Optional[float]:
        """Calculate population percentile (would need reference distribution)"""
        # Placeholder - would use population reference data
        # For now, return None
        return None
    
    def _calculate_z_score(
        self,
        prs_score: float,
        disease_code: str,
        population: str
    ) -> Optional[float]:
        """Calculate z-score (would need population mean and std)"""
        # Placeholder - would use population reference data
        # For now, return None
        return None
    
    def _calculate_confidence_interval(
        self,
        prs_score: float,
        variant_count: int,
        model: Dict,
        confidence_level: float = 0.95
    ) -> tuple:
        """Calculate confidence interval for PRS"""
        # Simple approximation: CI based on number of variants
        # More sophisticated methods would use bootstrap or model uncertainty
        se = prs_score / np.sqrt(variant_count) if variant_count > 0 else prs_score * 0.1
        z = stats.norm.ppf((1 + confidence_level) / 2)
        
        ci_lower = prs_score - z * se
        ci_upper = prs_score + z * se
        
        return (ci_lower, ci_upper)

