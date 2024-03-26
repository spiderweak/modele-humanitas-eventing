#!/bin/bash

#SBATCH --job-name=Simulations.py
#SBATCH --output=job_output_%A_%a.txt
#SBATCH --error=job_error_%A_%a.txt
#SBATCH --array=1-10  # Number of batches, 1-$(awk 'END {print int(NR/100) + 1}'
#SBATCH --time=00:10:00

# Calculate start and end line numbers based on SLURM_ARRAY_TASK_ID
LINES_PER_JOB=100
start_line=$(( ($SLURM_ARRAY_TASK_ID - 1) * $LINES_PER_JOB + 1 ))
end_line=$(( $SLURM_ARRAY_TASK_ID * $LINES_PER_JOB ))

# Loop through lines in the calculated range and process each line
for (( i=$start_line; i<=$end_line; i++ )); do
    read placement_file application_file device_file <<< $(awk "NR==$i" all_combinations.txt)

    if [ -z "$placement_file" ]; then
        echo "Reached end of file, exiting."
        exit 0
    fi

    # Extracting IDs from the file paths
    placement_id=${placement_file##*/}
    placement_id=${placement_id%%-*}

    application_id=${application_file##*/}
    application_id=${application_id%%-*}

    # Extract device_id from parent directory of device.json
    device_id=$(dirname $device_file)
    device_id=${device_id##*/}
    device_id=${device_id%%-*}

    # Building a unique ID
    unique_id="d${device_id}a${application_id}p${placement_id}"

    # Process files
    echo "Working on $unique_id"
    mkdir -p "output/$unique_id"
    python3 Processing.py --devices="$device_file" --applications="$application_file" --arrivals="$placement_file" --output="output/$unique_id/results.json"
done
