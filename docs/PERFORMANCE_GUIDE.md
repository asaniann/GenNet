# Performance Optimization Guide

This guide provides best practices and techniques for optimizing GenNet performance.

## Database Optimization

### Query Optimization

1. **Use Indexes**
   ```python
   # Indexes are already defined in models
   # Ensure indexes are created:
   # CREATE INDEX idx_grn_owner_id ON grn_networks(owner_id);
   ```

2. **Avoid N+1 Queries**
   ```python
   # Bad: N+1 queries
   networks = db.query(GRNNetwork).all()
   for network in networks:
       user = db.query(User).filter_by(id=network.owner_id).first()
   
   # Good: Eager loading
   from sqlalchemy.orm import joinedload
   networks = db.query(GRNNetwork).options(
       joinedload(GRNNetwork.owner)
   ).all()
   ```

3. **Use Pagination**
   ```python
   from shared.db_optimization import paginate_query
   
   query = db.query(GRNNetwork).filter_by(owner_id=user_id)
   result = paginate_query(query, page=1, limit=20)
   ```

4. **Cache Query Results**
   ```python
   from shared.db_optimization import cached_query
   
   @cached_query(ttl=3600)
   def get_network(network_id: str, db: Session):
       return db.query(GRNNetwork).filter_by(id=network_id).first()
   ```

### Connection Pooling

Connection pool settings are configured in `database.py`:
- `pool_size=10`: Base pool size
- `max_overflow=20`: Maximum overflow connections
- `pool_recycle=3600`: Recycle connections after 1 hour
- `pool_pre_ping=True`: Verify connections before use

## Caching Strategy

### Redis Caching

1. **Cache Frequently Accessed Data**
   ```python
   from shared.cache import cached
   
   @cached(ttl=3600, key_func=lambda network_id: f"network:{network_id}")
   def get_network(network_id: str):
       # Expensive database query
       return db.query(GRNNetwork).filter_by(id=network_id).first()
   ```

2. **Cache Invalidation**
   ```python
   from shared.cache import get_cache_manager
   
   cache_manager = get_cache_manager()
   cache_manager.delete(f"network:{network_id}")
   # Or invalidate by pattern
   cache_manager.invalidate_pattern("network:*")
   ```

3. **Cache Warming**
   - Pre-load frequently accessed data on service startup
   - Warm cache after deployments

### Cache TTL Guidelines

- **Stable Data**: 24 hours (user profiles, network metadata)
- **Semi-Stable Data**: 1 hour (network lists, search results)
- **Dynamic Data**: 5-15 minutes (workflow status, real-time metrics)

## API Performance

### Response Compression

Compression is automatically enabled for responses > 512 bytes:
```python
from shared.compression import setup_compression
setup_compression(app, minimum_size=512, prefer_brotli=True)
```

### Async Operations

Use async/await for I/O operations:
```python
async def get_network(network_id: str):
    # Async database query
    result = await db.execute(query)
    return result
```

### Background Tasks

Use background tasks for long-running operations:
```python
from fastapi import BackgroundTasks

@app.post("/networks/{network_id}/analyze")
async def analyze_network(
    network_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(perform_analysis, network_id)
    return {"status": "analysis_started"}
```

## Service-to-Service Communication

### Circuit Breakers

Use circuit breakers to prevent cascading failures:
```python
from shared.circuit_breaker import circuit_breaker

@circuit_breaker("ml-service", CircuitBreakerConfig(failure_threshold=5))
async def call_ml_service(data):
    # Service call
    pass
```

### Retry Logic

Use retry logic for transient failures:
```python
from shared.retry import retry, STANDARD_RETRY

@retry(STANDARD_RETRY)
async def unreliable_operation():
    # Operation that may fail
    pass
```

### Timeouts

Configure appropriate timeouts:
```python
from shared.http_client import ServiceClient

client = ServiceClient(
    base_url="http://service:8000",
    timeout=30.0,
    retry_config=STANDARD_RETRY
)
```

## Monitoring Performance

### Metrics

Key metrics to monitor:
- **Response Time**: p50, p95, p99
- **Request Rate**: Requests per second
- **Error Rate**: Percentage of failed requests
- **Database Query Time**: Average query duration
- **Cache Hit Rate**: Percentage of cache hits

### Profiling

Use profiling to identify bottlenecks:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

## Scaling Strategies

### Horizontal Scaling

- Scale stateless services horizontally
- Use Kubernetes HPA for automatic scaling
- Configure resource requests and limits

### Vertical Scaling

- Scale databases vertically when needed
- Monitor CPU and memory usage
- Plan for 2x peak capacity

### Database Scaling

- Use read replicas for read-heavy workloads
- Partition large tables if needed
- Consider sharding for very large datasets

## Performance Testing

### Load Testing

Use tools like Locust or k6:
```python
# locustfile.py
from locust import HttpUser, task

class GenNetUser(HttpUser):
    @task
    def get_networks(self):
        self.client.get("/api/v1/networks")
```

### Benchmarking

Establish performance baselines:
- Response time targets: p95 < 500ms
- Throughput targets: 1000 req/s per service
- Database query time: < 100ms for simple queries

## Best Practices

1. **Minimize Database Queries**
   - Use eager loading
   - Batch operations
   - Cache results

2. **Optimize Data Transfer**
   - Use compression
   - Paginate large results
   - Filter data at source

3. **Monitor and Alert**
   - Set up performance alerts
   - Monitor slow queries
   - Track resource usage

4. **Regular Optimization**
   - Review slow queries weekly
   - Optimize indexes monthly
   - Review cache hit rates

---

**Last Updated**: 2025-12-16

