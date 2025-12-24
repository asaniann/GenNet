# Real-Time Processing Guide

## Overview

The Real-Time Processing Service handles streaming data and real-time predictions using Apache Kafka and WebSocket support.

## Architecture

- **Kafka**: Event streaming infrastructure
- **Real-Time Service**: Processes events and generates predictions
- **WebSocket**: Live updates to clients
- **Alert Engine**: Real-time alert generation

## Setup

### Start Kafka Infrastructure

```bash
docker-compose -f docker-compose.yml -f docker-compose.kafka.yml up -d
```

### Start Real-Time Service

```bash
docker-compose -f docker-compose.services.yml up realtime-processing-service
```

## API Endpoints

### Publish Event

```bash
POST /api/v1/realtime/stream/publish
Content-Type: application/json

{
  "patient_id": "patient-123",
  "event_type": "data_upload",
  "event_data": {
    "data_type": "expression",
    "upload_id": "upload-456"
  }
}
```

### Get Alerts

```bash
GET /api/v1/realtime/alerts/{patient_id}
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8020/ws/patient-123');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## Event Types

- `data_upload`: New data uploaded
- `prediction`: New prediction generated
- `update`: Data updated
- `alert`: Alert generated

## Integration

Services publish events to Kafka topics:
- `patient-events`: Patient-related events
- `audit-logs`: Audit log events
- `security-events`: Security events

