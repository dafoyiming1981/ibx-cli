# Containerfile — Podman build for ibx-cli
# Build:  podman build -t artifactory.company.com/ibx-cli:0.1.0 -f Containerfile .
# Run:    podman run --rm -v ~/.infoblox/config:/home/ibx/.infoblox/config:Z <image> dns zones

FROM python:3.12-slim

# Create non-root user
RUN groupadd -g 1000 ibx && \
    useradd -u 1000 -g ibx -m -s /bin/sh ibx && \
    mkdir -p /home/ibx/.infoblox && \
    chown -R ibx:ibx /home/ibx

WORKDIR /app

# Copy and install wheel
COPY dist/ibx_cli-*.whl /tmp/
RUN pip install --no-cache-dir /tmp/ibx_cli-*.whl && \
    rm /tmp/ibx_cli-*.whl

# Switch to non-root user
USER ibx

ENTRYPOINT ["ibx"]
CMD ["--help"]
