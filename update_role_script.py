#!/usr/bin/env python3
import re

def update_roles_in_file(file_path):
    print(f"Reading file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Define the patterns to match the role lists
    patterns = [
        r"roles = \['user', 'admin', 'super-admin'\]",
        r"roles = \[['\"](user)['\"], ['\"](admin)['\"], ['\"](super-admin)['\"]"
    ]
    
    replacement = "roles = ['user', 'admin', 'super-admin', 'partner']"
    
    # Apply the replacements
    modified_content = content
    for pattern in patterns:
        modified_content = re.sub(pattern, replacement, modified_content)
    
    # Check if any changes were made
    if content == modified_content:
        print("No changes were needed or pattern not found.")
        return False
    
    print(f"Writing changes to file: {file_path}")
    with open(file_path, 'w') as file:
        file.write(modified_content)
    
    return True

# Update the roles in start_ltfpqrr.sh
updated = update_roles_in_file('start_ltfpqrr.sh')
print(f"File updated: {updated}")
