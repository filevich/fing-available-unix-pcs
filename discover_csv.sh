#!/bin/bash

# Define the base hostname
BASE_HOSTNAME="pcunix"
DOMAIN="fing.edu.uy" # Assuming all nodes are within this domain

# Define the exact range from the manual
START_NUM=16
END_NUM=144

# Output CSV file
OUTPUT_CSV_FILE="pcunix_nodes_reachability_$(date +%Y%m%d_%H%M%S).csv" # Add timestamp to filename

# Timeouts in seconds
PING_TIMEOUT=0.5 # Timeout for ping command
TOTAL_CHECK_TIMEOUT=2 # Total timeout for each host check (ping only for reachability)

echo "Starting discovery of pcunix nodes from $START_NUM to $END_NUM..."
echo "Results will be saved to $OUTPUT_CSV_FILE"
echo "--------------------------------------------------"

# Add CSV header
echo "Node_ID,Reachable" > "$OUTPUT_CSV_FILE"

# Iterate through numbers without padding
for i in $(seq $START_NUM $END_NUM); do
    HOSTNAME="${BASE_HOSTNAME}${i}.${DOMAIN}"
    NODE_ID="$i" # Store the unpadded number for the CSV

    # Assume unreachable by default
    REACHABLE_STATUS=0

    # Use 'timeout' for the entire block that checks the host
    timeout $TOTAL_CHECK_TIMEOUT bash -c "
        # --- Ping Check for Reachability ---
        # -c 1: send 1 packet
        # -W $PING_TIMEOUT: wait $PING_TIMEOUT seconds for response (timeout)
        if ping -c 1 -W $PING_TIMEOUT '$HOSTNAME' &>/dev/null; then
            exit 0 # Ping successful, exit with success code
        else
            exit 1 # Ping failed
        fi
    "
    # Capture the exit code of the timeout command
    # 0 means ping was successful
    # 124 means the command timed out
    # 1 means ping failed (host unreachable, etc.)
    TIMEOUT_EXIT_CODE=$?

    if [ $TIMEOUT_EXIT_CODE -eq 0 ]; then
        REACHABLE_STATUS=1 # Set status to 1 if ping was successful
        echo "Checking $HOSTNAME... REACHABLE"
    elif [ $TIMEOUT_EXIT_CODE -eq 124 ]; then
        echo "Checking $HOSTNAME... TIMEOUT (total check exceeded $TOTAL_CHECK_TIMEOUT seconds)"
    else
        echo "Checking $HOSTNAME... UNREACHABLE (ping failed)"
    fi

    # Write the result to the CSV file
    echo "$NODE_ID,$REACHABLE_STATUS" >> "$OUTPUT_CSV_FILE"

    # Introduce a small delay between each host check
    sleep 0.05
done

echo "--------------------------------------------------"
echo "Discovery complete. Check '$OUTPUT_CSV_FILE' for the reachability report."

