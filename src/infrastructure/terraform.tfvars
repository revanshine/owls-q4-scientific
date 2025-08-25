# OWLS Archive Q4 - LocalStack Development Configuration
# Frozen Control-Plane Design (Config disabled for LocalStack)

# Config mode: "off" for LocalStack (doesn't support Config service)
config_mode = "off"

# Environment settings
environment  = "development"
project_name = "owls-q4"

# Note: In production AWS, use config_mode = "minimal" for frozen control-plane compliance
# LocalStack doesn't support AWS Config service, so we disable it for local testing
