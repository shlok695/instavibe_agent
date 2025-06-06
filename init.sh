#!/bin/bash


PROJECT_FILE="$HOME/project_id.txt"

echo "--- Setting Google Cloud Project ID File ---"
# Prompt the user for input
read -p "Please enter your Google Cloud project ID: " user_project_id

# Check if the user entered anything
if [[ -z "$user_project_id" ]]; then
  echo "Error: No project ID was entered."
  exit 1 # Exit the script with an error code
fi

echo "You entered: $user_project_id"

# Write the project ID to the file
# Using > will overwrite the file if it exists
echo "$user_project_id" > "$PROJECT_FILE"

# Check if the write operation was successful
if [[ $? -eq 0 ]]; then
  echo "Successfully saved project ID."
else
  echo "Error: Failed saving your project ID:  $user_project_id."
  exit 1 
fi

echo "--- Setup complete ---"
exit 0
