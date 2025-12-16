"""
VCF file parser using cyvcf2 (established genomics library)
Integrates with existing S3 client from shared utilities
"""

import cyvcf2
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
import os
import tempfile
import boto3
from io import BytesIO

logger = logging.getLogger(__name__)


class VCFParser:
    """Parse VCF files using cyvcf2 library"""
    
    def __init__(self, s3_client=None):
        """
        Initialize VCF parser
        
        Args:
            s3_client: Optional boto3 S3 client for reading from S3
        """
        self.s3_client = s3_client
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "gennet-patient-data")
    
    def parse_from_s3(self, s3_key: str) -> pd.DataFrame:
        """
        Parse VCF file from S3
        
        Args:
            s3_key: S3 key for VCF file
            
        Returns:
            DataFrame with variant information
        """
        if not self.s3_client:
            raise ValueError("S3 client not configured")
        
        # Download VCF file to temporary location
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.vcf', delete=False) as tmp_file:
            try:
                self.s3_client.download_fileobj(self.bucket_name, s3_key, tmp_file)
                tmp_path = tmp_file.name
                
                # Parse VCF
                return self.parse_from_file(tmp_path)
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def parse_from_file(self, file_path: str) -> pd.DataFrame:
        """
        Parse VCF file from local path
        
        Args:
            file_path: Path to VCF file
            
        Returns:
            DataFrame with variant information
        """
        variants = []
        
        try:
            vcf = cyvcf2.VCF(file_path)
            
            # Extract header information
            samples = vcf.samples
            
            for variant in vcf:
                variant_data = {
                    'chromosome': variant.CHROM,
                    'position': variant.POS,
                    'ref_allele': variant.REF,
                    'alt_allele': ','.join(variant.ALT) if variant.ALT else '',
                    'rsid': variant.ID if variant.ID and variant.ID != '.' else None,
                    'quality': variant.QUAL,
                    'filter': ';'.join(variant.FILTERS) if variant.FILTERS else 'PASS',
                }
                
                # Extract genotype information (for first sample if available)
                if samples:
                    sample = variant.genotypes[0] if variant.genotypes else None
                    if sample:
                        variant_data['genotype'] = f"{sample[0]}/{sample[1]}"
                        variant_data['is_het'] = sample[0] != sample[1]
                        variant_data['is_hom_alt'] = sample[0] == sample[1] and sample[0] > 0
                
                # Extract INFO fields
                if variant.INFO:
                    variant_data['info'] = dict(variant.INFO)
                
                # Extract FORMAT fields (if available)
                if variant.FORMAT:
                    variant_data['format'] = variant.FORMAT.split(':')
                
                variants.append(variant_data)
            
            vcf.close()
            
            # Convert to DataFrame
            df = pd.DataFrame(variants)
            
            logger.info(f"Parsed {len(df)} variants from VCF file")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing VCF file: {e}")
            raise
    
    def extract_variant_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Extract summary statistics from VCF file
        
        Args:
            file_path: Path to VCF file
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            vcf = cyvcf2.VCF(file_path)
            
            variant_count = 0
            snp_count = 0
            indel_count = 0
            chromosomes = set()
            quality_scores = []
            
            for variant in vcf:
                variant_count += 1
                chromosomes.add(variant.CHROM)
                
                if variant.QUAL:
                    quality_scores.append(variant.QUAL)
                
                # Classify variant type
                if len(variant.REF) == 1 and all(len(alt) == 1 for alt in variant.ALT):
                    snp_count += 1
                else:
                    indel_count += 1
            
            vcf.close()
            
            summary = {
                'total_variants': variant_count,
                'snp_count': snp_count,
                'indel_count': indel_count,
                'chromosomes': sorted(list(chromosomes)),
                'quality_mean': float(pd.Series(quality_scores).mean()) if quality_scores else None,
                'quality_median': float(pd.Series(quality_scores).median()) if quality_scores else None,
                'samples': vcf.samples
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error extracting VCF summary: {e}")
            raise

