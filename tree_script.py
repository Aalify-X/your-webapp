import os

def print_tree(startpath, max_depth=2):  # Change max_depth to control folder depth
    for root, dirs, files in os.walk(startpath):
        # Calculate the level of the current directory
        level = root.replace(startpath, '').count(os.sep)
        
        if level >= max_depth:  # Stop scanning deeper than max_depth
            del dirs[:]  # Prevent deeper traversal
            continue
        
        indent = '    ' * level
        print(f"{indent}├── {os.path.basename(root)}/")
        
        subindent = '    ' * (level + 1)
        for f in files:
            print(f"{subindent}└── {f}")

print_tree('C:/Users/Aliya/OneDrive/Desktop/Web App', max_depth=2)  # Adjust depth
