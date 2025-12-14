FROM kong:latest

USER root

# Install custom plugins if needed
# RUN luarocks install <plugin>

USER kong

# Copy Kong configuration
COPY kong.yml /usr/local/kong/declarative/kong.yml

# Expose ports
EXPOSE 8000 8443 8001 8444

# Use declarative config
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/usr/local/kong/declarative/kong.yml
ENV KONG_PROXY_ACCESS_LOG=/dev/stdout
ENV KONG_ADMIN_ACCESS_LOG=/dev/stdout
ENV KONG_PROXY_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_ERROR_LOG=/dev/stderr

