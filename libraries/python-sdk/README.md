# GenNet Python SDK

Python SDK for interacting with the GenNet Cloud Platform API.

## Installation

```bash
pip install -e .
```

## Usage

```python
from gennet import GenNetClient

client = GenNetClient(base_url="http://localhost:8000", api_key="your-key")

# List networks
networks = client.list_networks()

# Create workflow
workflow = client.create_workflow(
    name="My Analysis",
    workflow_type="qualitative",
    network_id="network-123"
)
```

