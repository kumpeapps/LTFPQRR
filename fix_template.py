#!/usr/bin/env python3

def fix_template(file_path):
    print(f"Reading file: {file_path}")
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix the double else issue
    fixed_content = content.replace("{% else %}{% else %}", "{% else %}")
    
    print(f"Writing fixed content to file: {file_path}")
    with open(file_path, 'w') as file:
        file.write(fixed_content)
    
    return True

# Fix the template
updated = fix_template('/Users/justinkumpe/Documents/LTFPQRR/templates/partner/dashboard.html')
print(f"Template fixed: {updated}")
