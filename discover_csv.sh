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
SSH_TIMEOUT=2 # Timeout for SSH commands
TOTAL_CHECK_TIMEOUT=3 # Total timeout for each host check (ping + SSH)

echo "Starting discovery of pcunix nodes from $START_NUM to $END_NUM..."
echo "Results will be saved to $OUTPUT_CSV_FILE"
echo "--------------------------------------------------"

# Add CSV header with new columns
echo "Node_ID,Reachable,CPU_Name,Cores_Per_Socket,Total_CPUs,Total_RAM_GiB,Available_RAM_GiB" > "$OUTPUT_CSV_FILE"

# Iterate through numbers without padding
for i in $(seq $START_NUM $END_NUM); do
    HOSTNAME="${BASE_HOSTNAME}${i}.${DOMAIN}"
    NODE_ID="$i" # Store the unpadded number for the CSV

    # Initialize defaults
    REACHABLE_STATUS=0
    CPU_NAME=""
    CORES_PER_SOCKET=""
    TOTAL_CPUS=""
    TOTAL_RAM_GIB=""
    AVAILABLE_RAM_GIB=""

    # Use 'timeout' for the entire block that checks the host
    timeout $TOTAL_CHECK_TIMEOUT bash -c "
        # --- Ping Check for Reachability ---
        if ping -c 1 -W $PING_TIMEOUT '$HOSTNAME' &>/dev/null; then
            exit 0 # Ping successful
        else
            exit 1 # Ping failed
        fi
    "
    TIMEOUT_EXIT_CODE=$?

    if [ $TIMEOUT_EXIT_CODE -eq 0 ]; then
        REACHABLE_STATUS=1
        echo "Checking $HOSTNAME... REACHABLE"

        # --- SSH to gather system info ---
        # Use StrictHostKeyChecking=no and UserKnownHostsFile=/dev/null to bypass host key verification
        SSH_OUTPUT=$(timeout $SSH_TIMEOUT ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=1 -o BatchMode=yes "$HOSTNAME" "
            # Gather CPU info using lscpu
            LSCPU_OUTPUT=\$(lscpu)
            CPU_NAME=\$(echo \"\$LSCPU_OUTPUT\" | grep 'Model name' | awk -F': ' '{print \$2}' | tr -d ',' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*\$//')
            CORES_PER_SOCKET=\$(echo \"\$LSCPU_OUTPUT\" | grep 'Core(s) per socket' | awk '{print \$4}')
            TOTAL_CPUS=\$(echo \"\$LSCPU_OUTPUT\" | grep '^CPU(s):' | awk '{print \$2}')

            # Gather RAM info using free -h
            FREE_OUTPUT=\$(free -h | grep Mem:)
            TOTAL_RAM=\$(echo \"\$FREE_OUTPUT\" | awk '{print \$2}' | tr -d 'Gi')
            AVAILABLE_RAM=\$(echo \"\$FREE_OUTPUT\" | awk '{print \$7}' | tr -d 'Gi')

            # Output in a format that's easy to parse
            echo \"CPU_NAME:\$CPU_NAME\"
            echo \"CORES_PER_SOCKET:\$CORES_PER_SOCKET\"
            echo \"TOTAL_CPUS:\$TOTAL_CPUS\"
            echo \"TOTAL_RAM_GIB:\$TOTAL_RAM\"
            echo \"AVAILABLE_RAM_GIB:\$AVAILABLE_RAM\"
        " 2>/dev/null)

        SSH_EXIT_CODE=$?

        if [ $SSH_EXIT_CODE -eq 0 ]; then
            # Parse SSH output
            CPU_NAME=$(echo "$SSH_OUTPUT" | grep '^CPU_NAME:' | cut -d':' -f2- | tr -d '\n')
            CORES_PER_SOCKET=$(echo "$SSH_OUTPUT" | grep '^CORES_PER_SOCKET:' | cut -d':' -f2- | tr -d '\n')
            TOTAL_CPUS=$(echo "$SSH_OUTPUT" | grep '^TOTAL_CPUS:' | cut -d':' -f2- | tr -d '\n')
            TOTAL_RAM_GIB=$(echo "$SSH_OUTPUT" | grep '^TOTAL_RAM_GIB:' | cut -d':' -f2- | tr -d '\n')
            AVAILABLE_RAM_GIB=$(echo "$SSH_OUTPUT" | grep '^AVAILABLE_RAM_GIB:' | cut -d':' -f2- | tr -d '\n')
        else
            echo "  Warning: SSH to $HOSTNAME failed or timed out"
        fi
    elif [ $TIMEOUT_EXIT_CODE -eq 124 ]; then
        echo "Checking $HOSTNAME... TIMEOUT (total check exceeded $TOTAL_CHECK_TIMEOUT seconds)"
    else
        echo "Checking $HOSTNAME... UNREACHABLE (ping failed)"
    fi

    # Escape commas in CPU_NAME to prevent CSV parsing issues
    CPU_NAME=$(echo "$CPU_NAME" | sed 's/,/\\,/g')

    # Write the result to the CSV file
    echo "$NODE_ID,$REACHABLE_STATUS,$CPU_NAME,$CORES_PER_SOCKET,$TOTAL_CPUS,$TOTAL_RAM_GIB,$AVAILABLE_RAM_GIB" >> "$OUTPUT_CSV_FILE"

    # Introduce a small delay between each host check
    sleep 0.05
done

echo "--------------------------------------------------"
echo "Discovery complete. Check '$OUTPUT_CSV_FILE' for the reachability and system info report."