import os
import re
import shutil
from datetime import datetime

# Read the reference index.html
with open('index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

# Extract the nav block from index.html
nav_match = re.search(r'(<nav class="sitenavigation".*?</nav>)', index_content, re.DOTALL)
footer_match = re.search(r'(<footer>.*?</footer>)', index_content, re.DOTALL)

if not nav_match or not footer_match:
    print("Could not find nav or footer in index.html")
    exit(1)

reference_nav = nav_match.group(1)
reference_footer = footer_match.group(1)

# Create timestamped backup folder
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = f'backups/{timestamp}'
os.makedirs(backup_dir, exist_ok=True)

for filename in os.listdir('.'):
    if not filename.endswith('.html') or filename == 'index.html':
        continue

    # Backup before touching
    shutil.copy2(filename, os.path.join(backup_dir, filename))
    print(f"  Backed up {filename} → {backup_dir}/{filename}")

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    page_name = os.path.splitext(filename)[0].capitalize()

    def set_active(nav_html, current_file):
        nav_html = re.sub(r' class="active"', '', nav_html)
        nav_html = nav_html.replace(
            f'href="{current_file}"',
            f'href="{current_file}" class="active"'
        )
        return nav_html

    new_nav = set_active(reference_nav, filename)

    content = re.sub(r'<nav class="sitenavigation".*?</nav>', new_nav, content, flags=re.DOTALL)
    content = re.sub(r'<footer>.*?</footer>', reference_footer, content, flags=re.DOTALL)
    content = re.sub(r'<div class="content">', '<main class="content">', content)
    content = re.sub(r'</div>\s*\n(\s*<!-- Footer -->|\s*<footer)', r'</main>\n\1', content)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Updated {filename}")

print(f"\nDone. Backups saved to {backup_dir}/")
