# GenNet API Documentation

## Authentication

All API requests require authentication via JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Networks

- `GET /api/v1/networks` - List networks
- `POST /api/v1/networks` - Create network
- `GET /api/v1/networks/{id}` - Get network
- `PUT /api/v1/networks/{id}` - Update network
- `DELETE /api/v1/networks/{id}` - Delete network

### Workflows

- `GET /api/v1/workflows` - List workflows
- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows/{id}` - Get workflow
- `GET /api/v1/workflows/{id}/status` - Get workflow status
- `GET /api/v1/workflows/{id}/results` - Get workflow results

## GraphQL API

GraphQL endpoint available at `/graphql` with introspection enabled.

