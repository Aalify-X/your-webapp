import os

EXCLUDED_DIRS = {'__pycache__', 'node_modules', '.git', '.venv', 'venv'}
EXCLUDED_FILES = {'.DS_Store'}

def print_tree_with_code(path='.', prefix=''):
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return

    for item in items:
        if item in EXCLUDED_FILES or item.startswith('.'):
            continue

        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            if item in EXCLUDED_DIRS:
                continue
            print(f'{prefix}📁 {item}/')
            print_tree_with_code(full_path, prefix + '    ')
        else:
            print(f'{prefix}📄 {item}')
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        print(prefix + '    ' + line.rstrip())
            except Exception as e:
                print(prefix + f'    ⚠️ Could not read file: {e}')

if __name__ == '__main__':
    print(f'\n📦 Full Web App Structure + Code:\n')
    print_tree_with_code('.')
