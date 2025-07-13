#!/usr/bin/env python3

def update_instructions(file_path):
    print(f"Reading file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Add "partner" to the roles list in the role-based access control section
    modified_content = content.replace(
        'Users must have appropriate roles: "user", "admin", "super-admin", etc.',
        'Users must have appropriate roles: "user", "admin", "super-admin", "partner", etc.'
    )
    
    # Add the new section about reliable file modifications
    if "## Code Change Reliability Guidelines" not in content:
        # Find the position to insert the new section - after the Version Control Hygiene section
        insert_pos = content.find("### Version Control Hygiene")
        if insert_pos != -1:
            # Find the end of the section
            insert_pos = content.find("```", insert_pos)
            if insert_pos != -1:
                insert_pos = content.find("```", insert_pos + 3)
                if insert_pos != -1:
                    # Move past the closing code block
                    insert_pos = content.find("\n", insert_pos) + 1
                    
                    # Add our new section
                    new_section = """
## Code Change Reliability Guidelines

### Ensuring Changes Are Applied Correctly
- **Always verify changes** after making them by reading the file back
- After modifying files, use `grep` or `cat` to confirm changes were saved
- For critical configuration files, create a backup before making changes

### Fallback Strategies for File Modifications
1. **Primary Method**: Use editor tools like `replace_string_in_file` or `insert_edit_into_file`
2. **Fallback Method 1**: If primary method fails, use Python scripts for precise replacements:
   ```python
   with open(file_path, 'r') as file:
       content = file.read()
   modified_content = content.replace('old_string', 'new_string')
   with open(file_path, 'w') as file:
       file.write(modified_content)
   ```
3. **Fallback Method 2**: For complex edits, use dedicated tools like `sed` or `awk`
4. **Validation Step**: Always read back the file after modification to verify changes

### Handling Multi-Line Replacements
- Use Python with regex module for complex multi-line replacements
- Test regex patterns carefully before applying them
- Consider creating a temporary file and swapping it on success

### Verifying Configuration Changes
- After modifying configuration files, always restart affected services
- Verify changes using logs or application behavior
- Use `./dev.sh rebuild-dev` to ensure all containers pick up the changes
"""
                    modified_content = modified_content[:insert_pos] + new_section + modified_content[insert_pos:]
    
    # Always ensure partner role is mentioned
    if "Always ensure partner role is included in role initialization arrays" not in modified_content:
        modified_content = modified_content.replace(
            "All permissions are managed through the role system",
            "All permissions are managed through the role system\n   - Always ensure partner role is included in role initialization arrays"
        )
    
    print(f"Writing updated content to file: {file_path}")
    with open(file_path, 'w') as file:
        file.write(modified_content)
    
    return True

# Update the instructions
updated = update_instructions('/Users/justinkumpe/Documents/LTFPQRR/.github/copilot-instructions.md')
print(f"Instructions updated: {updated}")
