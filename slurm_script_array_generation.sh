#!/bin/bash

placement_dir="input/placements"
application_dir="input/applications"
devices_base_dir="input/devices"

# Clear the existing all_combinations.txt file
> all_combinations.txt

for placement_file in "$placement_dir"/*-placements.json; do
  for application_file in "$application_dir"/*-applications.json; do
    for device_dir in "$devices_base_dir"/*; do
      if [[ -d $device_dir ]]; then
        device_file="$device_dir/devices.json"
        if [[ -f $device_file ]]; then
          echo "$placement_file $application_file $device_file" >> slurm_parameters/all_combinations.txt
        fi
      fi
    done
  done
done

