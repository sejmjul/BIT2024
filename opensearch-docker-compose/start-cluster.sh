#!/bin/bash

# Step 1: Start Docker Compose services in detached mode
docker compose up -d

# Step 2: Wait for services to start and stabilize
echo "Waiting for services to start..."
sleep 20

# Step 3: Initialize variables for loop
MAX_WAIT_TIME=120  # Maximum wait time in seconds
CHECK_INTERVAL=3  # Time between CPU usage checks
TIME_ELAPSED=0

# Step 4: Loop until CPU usage is below 10% or timeout is reached
while (( TIME_ELAPSED < MAX_WAIT_TIME )); do
  # Check CPU usage
  CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
  echo "Current CPU usage: $CPU_USAGE%"

  # Check if CPU usage is below 10%
  if (( $(echo "$CPU_USAGE < 18" | bc -l) )); then
    echo "CPU usage is below 18%, running the security configuration command..."
    docker compose exec os01 bash -c "chmod +x plugins/opensearch-security/tools/securityadmin.sh && \
      bash plugins/opensearch-security/tools/securityadmin.sh \
      -cd config/opensearch-security \
      -icl \
      -nhnv \
      -cacert config/certificates/ca/ca.pem \
      -cert config/certificates/ca/admin.pem \
      -key config/certificates/ca/admin.key \
      -h localhost"
    exit 0
  else
    echo "CPU usage is above 10%, waiting before retrying..."
  fi

  # Wait for the specified interval before the next check
  sleep $CHECK_INTERVAL
  ((TIME_ELAPSED+=CHECK_INTERVAL))
done

# If the loop exits without running the security command
echo "Timed out after 2 minutes. Security configuration command was not run due to high CPU usage."
exit 1

