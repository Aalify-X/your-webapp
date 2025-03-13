import os

def print_tree(start_path, indent=""):
    """Recursively prints directory structure."""
    items = sorted(os.listdir(start_path))  # Sort to maintain order
    for index, item in enumerate(items):
        path = os.path.join(start_path, item)
        is_last = index == len(items) - 1  # Check if last item in folder
        connector = "└── " if is_last else "├── "
        print(indent + connector + item)
        if os.path.isdir(path):
            new_indent = indent + ("    " if is_last else "│   ")
            print_tree(path, new_indent)

# Run the script in the current directory
print_tree(".")
