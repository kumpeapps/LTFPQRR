#!/usr/bin/env python3

def fix_roles_in_file(file_path):
    print(f"Reading file: {file_path}")
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    modified_lines = []
    for line in lines:
        if "roles = ['user', 'admin', 'super-admin', 'partner'], 'partner']" in line:
            # Fix the duplicate entry
            fixed_line = line.replace("['user', 'admin', 'super-admin', 'partner'], 'partner']", 
                                     "['user', 'admin', 'super-admin', 'partner']")
            modified_lines.append(fixed_line)
        else:
            modified_lines.append(line)
    
    print(f"Writing fixed content to file: {file_path}")
    with open(file_path, 'w') as file:
        file.writelines(modified_lines)
    
    return True

# Fix the roles in start_ltfpqrr.sh
updated = fix_roles_in_file('start_ltfpqrr.sh')
print(f"File fixed: {updated}")
