#!/bin/bash
# Script to fix Redis port conflict
# Either kills existing process or changes to alternative port

set -e

REDIS_PORT=6379
ALT_PORT=6380

echo "🔍 Checking port $REDIS_PORT..."

# Check if it's a Docker container using port 6379
CONTAINERS_USING_PORT=$(docker ps --format '{{.Names}} {{.Ports}}' | grep ":${REDIS_PORT}->" | awk '{print $1}' 2>/dev/null || echo "")
if [ ! -z "$CONTAINERS_USING_PORT" ]; then
    echo "⚠️  Found Docker containers using port $REDIS_PORT:"
    echo "$CONTAINERS_USING_PORT" | while read container; do
        [ ! -z "$container" ] && echo "   • $container"
    done
    echo "   Stopping these containers..."
    
    echo "$CONTAINERS_USING_PORT" | while read container; do
        [ ! -z "$container" ] && docker stop "$container" 2>/dev/null || true
        [ ! -z "$container" ] && docker rm "$container" 2>/dev/null || true
    done
    sleep 1
    echo "✅ Docker containers stopped"
fi

# Check if port is still in use
if lsof -i :${REDIS_PORT} >/dev/null 2>&1 || ss -tulpn | grep -q ":${REDIS_PORT}"; then
    echo "⚠️  Port $REDIS_PORT still in use, attempting to kill process..."
    
    # Try to find and kill the process
    PID=$(lsof -ti :${REDIS_PORT} 2>/dev/null || fuser ${REDIS_PORT}/tcp 2>/dev/null | awk '{print $NF}' || echo "")
    
    if [ ! -z "$PID" ]; then
        echo "🔪 Killing process $PID on port $REDIS_PORT..."
        sudo kill -9 $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    
    # Check again
    if lsof -i :${REDIS_PORT} >/dev/null 2>&1 || ss -tulpn | grep -q ":${REDIS_PORT}"; then
        echo "⚠️  Could not free port $REDIS_PORT, will use alternative port $ALT_PORT"
        USE_ALT_PORT=true
    else
        echo "✅ Port $REDIS_PORT is now free"
        USE_ALT_PORT=false
    fi
else
    echo "✅ Port $REDIS_PORT is available"
    USE_ALT_PORT=false
fi

# Update docker-compose.yml if needed
if [ "$USE_ALT_PORT" = true ]; then
    echo "📝 Updating docker-compose.yml to use port $ALT_PORT..."
    if [ -f docker-compose.yml ]; then
        # Backup original
        cp docker-compose.yml docker-compose.yml.bak
        
        # Replace port mapping
        sed -i "s/- \"6379:6379\"/- \"${ALT_PORT}:6379\"/g" docker-compose.yml
        
        echo "✅ Updated docker-compose.yml: Redis now exposed on host port $ALT_PORT"
        echo "ℹ️  Services will still connect to Redis on internal port 6379"
        echo "ℹ️  To connect from host, use: redis-cli -p $ALT_PORT"
    fi
fi

echo "✅ Redis port conflict resolved!"

