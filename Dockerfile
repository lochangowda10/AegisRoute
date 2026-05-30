FROM python:3.11-alpine  # Use Alpine for smaller size

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY router.py .
COPY agent_instance.py .
COPY health_checker.py .

# Expose ports (router on 8000, agents on 8001-8003)
EXPOSE 8000 8001 8002 8003

# Create a startup script to run router and agents
RUN echo '#!/bin/sh\n\
python agent_instance.py --port 8001 &\n\
python agent_instance.py --port 8002 &\n\
python agent_instance.py --port 8003 &\n\
python router.py' > /app/start.sh
RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]
