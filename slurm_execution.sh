#!/bin/bash

#SBATCH --job-name=Simulations.py
#SBATCH --output=job_output_%A_%a.txt
#SBATCH --error=job_error_%A_%a.txt
#SBATCH --array=1-100 # Defaults to 100 for tests, actual value is obtained by running : $(wc -l < all_combinations.txt)
#SBATCH --time=00:10:00

# Read the $SLURM_ARRAY_TASK_ID-th line from the file containing all combinations
read placement_file application_file device_file <<< $(awk "NR==$SLURM_ARRAY_TASK_ID" all_combinations.txt)

# Extracting IDs from the file paths
placement_id=${placement_file##*/}
placement_id=${placement_id%%-*}

application_id=${application_file##*/}
application_id=${application_id%%-*}

device_id=${device_file##*/}
device_id=${device_id%%-*}

# Building a unique ID
unique_id="d${device_id}a${application_id}p${placement_id}"

# Process files
echo "Working on $unique_id"
mkdir -p "output/$unique_id"
python3 Processing.py --devices="$device_file" --applications="$application_file" --arrivals="$placement_file" --output="output/$unique_id/results.json"
