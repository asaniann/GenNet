"""
Tests for data ingestion parser
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from parser import GRNParser


@pytest.mark.unit
def test_parse_json():
    """Test parsing JSON format"""
    parser = GRNParser()
    
    test_data = {
        "nodes": [
            {"id": "gene1", "label": "Gene 1"}
        ],
        "edges": [
            {"source": "gene1", "target": "gene2", "type": "activates"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_path = f.name
    
    try:
        result = parser.parse(temp_path)
        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) == 1
    finally:
        os.unlink(temp_path)


@pytest.mark.unit
def test_parse_csv():
    """Test parsing CSV format"""
    parser = GRNParser()
    
    csv_content = "source,target,type\ngene1,gene2,activates\ngene2,gene3,inhibits\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_path = f.name
    
    try:
        result = parser.parse(temp_path)
        assert "nodes" in result
        assert "edges" in result
        assert len(result["edges"]) == 2
    finally:
        os.unlink(temp_path)


@pytest.mark.unit
def test_validate_data():
    """Test data validation"""
    parser = GRNParser()
    
    valid_data = {
        "nodes": [{"id": "gene1", "label": "Gene 1"}],
        "edges": [{"source": "gene1", "target": "gene2"}]
    }
    
    is_valid, errors = parser.validate(valid_data)
    assert is_valid
    assert len(errors) == 0
    
    invalid_data = {
        "nodes": [{"label": "Gene 1"}]  # Missing id
    }
    
    is_valid, errors = parser.validate(invalid_data)
    assert not is_valid
    assert len(errors) > 0

