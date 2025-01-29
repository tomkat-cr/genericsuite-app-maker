FROM ottomator/base-python:latest

# Build argument for port with default value
ARG PORT=8001
ENV PORT=${PORT}

WORKDIR /app

# Copy the application code
# COPY . .

# Map the application code
VOLUME /app

# Expose the port from build argument
EXPOSE ${PORT}

# Command to run the application
# Feel free to change gsam_supabase_agent to gsam_postgres_agent
# CMD ["sh", "-c", "uvicorn gsam_postgres_agent:app --host 0.0.0.0 --port ${PORT} --reload"]
# CMD ["sh", "-c", "uvicorn gsam_supabase_agent:app --host 0.0.0.0 --port ${PORT} --reload"]
CMD ["bash", "-c", "bash ./gsam_ottomator_agent/run_agent.sh run_uvicorn_server"]
