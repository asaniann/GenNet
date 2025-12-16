"""
Biomarker identification from expression data
Integrates with existing ML Service for classification
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from scipy import stats
from sklearn.feature_selection import f_classif, mutual_info_classif
import logging

logger = logging.getLogger(__name__)


class BiomarkerFinder:
    """Identify biomarkers from expression data"""
    
    def find_differential_biomarkers(
        self,
        expression_data: pd.DataFrame,
        labels: Optional[pd.Series] = None,
        method: str = "fold_change",
        top_n: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find differentially expressed genes as biomarkers
        
        Args:
            expression_data: Expression data (genes as columns)
            labels: Optional class labels for comparison
            method: Method for biomarker identification
            top_n: Number of top biomarkers to return
            
        Returns:
            List of biomarker dictionaries
        """
        if labels is not None and len(labels) == len(expression_data):
            # Supervised: compare between classes
            return self._find_supervised_biomarkers(expression_data, labels, top_n)
        else:
            # Unsupervised: find highly variable or expressed genes
            return self._find_unsupervised_biomarkers(expression_data, top_n)
    
    def _find_supervised_biomarkers(
        self,
        expression_data: pd.DataFrame,
        labels: pd.Series,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Find biomarkers using class labels"""
        biomarkers = []
        
        # Get unique classes
        classes = labels.unique()
        if len(classes) < 2:
            logger.warning("Need at least 2 classes for supervised biomarker finding")
            return self._find_unsupervised_biomarkers(expression_data, top_n)
        
        # For each gene, calculate statistics
        for gene in expression_data.columns:
            gene_expr = expression_data[gene]
            
            # Group by class
            class_expr = [gene_expr[labels == cls].values for cls in classes]
            
            # Calculate fold change
            mean_expr = [np.mean(cls) for cls in class_expr]
            fold_change = mean_expr[1] / mean_expr[0] if mean_expr[0] > 0 else float('inf')
            log2_fc = np.log2(fold_change) if fold_change > 0 and not np.isinf(fold_change) else 0
            
            # Statistical test (t-test)
            try:
                t_stat, p_value = stats.ttest_ind(class_expr[0], class_expr[1])
            except:
                p_value = 1.0
            
            biomarkers.append({
                "gene": gene,
                "fold_change": float(fold_change),
                "log2_fold_change": float(log2_fc),
                "p_value": float(p_value),
                "mean_class_0": float(mean_expr[0]),
                "mean_class_1": float(mean_expr[1])
            })
        
        # Sort by absolute log2 fold change and p-value
        biomarkers_df = pd.DataFrame(biomarkers)
        biomarkers_df['abs_log2_fc'] = biomarkers_df['log2_fold_change'].abs()
        biomarkers_df = biomarkers_df.sort_values(['abs_log2_fc', 'p_value'], ascending=[False, True])
        
        # Apply FDR correction
        from statsmodels.stats.multitest import multipletests
        p_values = biomarkers_df['p_value'].values
        _, p_adjusted, _, _ = multipletests(p_values, method='fdr_bh', alpha=0.05)
        biomarkers_df['adjusted_p_value'] = p_adjusted
        
        # Filter significant and return top N
        significant = biomarkers_df[biomarkers_df['adjusted_p_value'] < 0.05]
        top_biomarkers = significant.head(top_n)
        
        return top_biomarkers.to_dict('records')
    
    def _find_unsupervised_biomarkers(
        self,
        expression_data: pd.DataFrame,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Find biomarkers using variance and expression level"""
        biomarkers = []
        
        for gene in expression_data.columns:
            gene_expr = expression_data[gene].values
            
            # Calculate statistics
            mean_expr = np.mean(gene_expr)
            std_expr = np.std(gene_expr)
            cv = std_expr / mean_expr if mean_expr > 0 else 0  # Coefficient of variation
            
            biomarkers.append({
                "gene": gene,
                "mean_expression": float(mean_expr),
                "std_expression": float(std_expr),
                "coefficient_of_variation": float(cv),
                "fold_change": None,
                "log2_fold_change": None,
                "p_value": None
            })
        
        # Sort by coefficient of variation (highly variable genes)
        biomarkers_df = pd.DataFrame(biomarkers)
        biomarkers_df = biomarkers_df.sort_values('coefficient_of_variation', ascending=False)
        
        return biomarkers_df.head(top_n).to_dict('records')
    
    def find_disease_biomarkers(
        self,
        expression_data: pd.DataFrame,
        disease_signature: Dict[str, Any],
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find biomarkers based on disease signature
        
        Args:
            expression_data: Patient expression data
            disease_signature: Disease signature dictionary
            threshold: Expression threshold for biomarker identification
            
        Returns:
            List of biomarker dictionaries
        """
        signature_genes = disease_signature.get('genes', [])
        biomarkers = []
        
        for gene in signature_genes:
            if gene not in expression_data.columns:
                continue
            
            gene_expr = expression_data[gene].values
            mean_expr = np.mean(gene_expr)
            
            if mean_expr >= threshold:
                biomarkers.append({
                    "gene": gene,
                    "expression_value": float(mean_expr),
                    "biomarker_type": "diagnostic",
                    "disease_code": disease_signature.get('disease_code'),
                    "disease_name": disease_signature.get('disease_name')
                })
        
        return biomarkers

