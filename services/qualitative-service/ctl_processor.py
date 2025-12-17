"""
CTL (Computation Tree Logic) Formula Processor
Handles CTL formula parsing, validation, and processing
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class CTLOperator(str, Enum):
    """CTL temporal operators"""
    AX = "AX"  # All next
    EX = "EX"  # Exists next
    AF = "AF"  # All future
    EF = "EF"  # Exists future
    AG = "AG"  # All globally
    EG = "EG"  # Exists globally
    AU = "AU"  # All until
    EU = "EU"  # Exists until


class CTLProcessor:
    """Process and validate CTL formulas"""
    
    # CTL operators pattern
    OPERATORS = [
        r'\bAX\b', r'\bEX\b', r'\bAF\b', r'\bEF\b',
        r'\bAG\b', r'\bEG\b', r'\bAU\b', r'\bEU\b'
    ]
    
    # Logical operators
    LOGICAL_OPS = [r'\bAND\b', r'\bOR\b', r'\bNOT\b', r'\b->\b', r'\b<->\b']
    
    def __init__(self):
        self.operator_pattern = re.compile('|'.join(self.OPERATORS + self.LOGICAL_OPS))
    
    def validate_syntax(self, formula: str) -> Tuple[bool, List[str]]:
        """
        Validate CTL formula syntax
        
        Args:
            formula: CTL formula string
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Basic checks
        if not formula or not formula.strip():
            errors.append("Formula cannot be empty")
            return False, errors
        
        # Check balanced parentheses
        if not self._check_balanced_parentheses(formula):
            errors.append("Unbalanced parentheses")
            return False, errors
        
        # Check for valid operators
        if not self._check_operators(formula):
            errors.append("Invalid or unrecognized operators")
            return False, errors
        
        # Check formula structure
        structure_errors = self._validate_structure(formula)
        if structure_errors:
            errors.extend(structure_errors)
            return False, errors
        
        return True, errors
    
    def _check_balanced_parentheses(self, formula: str) -> bool:
        """Check if parentheses are balanced"""
        count = 0
        for char in formula:
            if char == '(':
                count += 1
            elif char == ')':
                count -= 1
                if count < 0:
                    return False
        return count == 0
    
    def _check_operators(self, formula: str) -> bool:
        """Check if operators are valid"""
        # Extract all operators
        operators = self.operator_pattern.findall(formula)
        
        # Check if all operators are recognized
        valid_ops = [op for op in self.OPERATORS + self.LOGICAL_OPS]
        for op in operators:
            if not any(re.match(valid_op, op) for valid_op in valid_ops):
                return False
        
        return True
    
    def _validate_structure(self, formula: str) -> List[str]:
        """Validate CTL formula structure"""
        errors = []
        
        # Remove whitespace for analysis
        clean_formula = formula.replace(' ', '')
        
        # Check for basic structure patterns
        # CTL operators should be followed by parentheses
        for op in ['AX', 'EX', 'AF', 'EF', 'AG', 'EG']:
            pattern = rf'\b{op}\b\s*[^(]'
            if re.search(pattern, formula):
                errors.append(f"Operator {op} must be followed by parentheses")
        
        # Check for until operators (AU, EU) - should have two arguments
        for op in ['AU', 'EU']:
            pattern = rf'\b{op}\s*\([^)]*\)'
            matches = re.findall(pattern, formula)
            for match in matches:
                # Count commas to ensure two arguments
                if match.count(',') < 1:
                    errors.append(f"Operator {op} requires two arguments separated by comma")
        
        return errors
    
    def parse_formula(self, formula: str) -> Dict[str, Any]:
        """
        Parse CTL formula into structured representation
        
        Args:
            formula: CTL formula string
            
        Returns:
            Parsed formula structure
        """
        # Validate first
        is_valid, errors = self.validate_syntax(formula)
        if not is_valid:
            raise ValueError(f"Invalid CTL formula: {', '.join(errors)}")
        
        # Extract operators and operands
        operators = self.operator_pattern.findall(formula)
        
        # Build parse tree (simplified)
        structure = {
            "original": formula,
            "operators": operators,
            "complexity": len(operators),
            "has_temporal": any(op in ['AX', 'EX', 'AF', 'EF', 'AG', 'EG', 'AU', 'EU'] for op in operators),
            "has_path_quantifiers": any(op in ['A', 'E'] for op in ''.join(operators))
        }
        
        return structure
    
    def optimize_formula(self, formula: str) -> str:
        """
        Optimize CTL formula (remove redundant operators, simplify)
        
        Args:
            formula: CTL formula string
            
        Returns:
            Optimized formula
        """
        # Basic optimizations
        optimized = formula.strip()
        
        # Remove double negations
        optimized = re.sub(r'\bNOT\s+NOT\s+', '', optimized)
        
        # Simplify logical operators
        optimized = re.sub(r'\s+AND\s+', ' AND ', optimized)
        optimized = re.sub(r'\s+OR\s+', ' OR ', optimized)
        
        return optimized

