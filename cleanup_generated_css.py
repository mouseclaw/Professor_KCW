import re
from pathlib import Path

files = ['index.css', 'activities.css', 'form.css', 'biography.css', 'member.css', 'researchs.css']
pattern = re.compile(r'(?<![A-Za-z0-9_-])\.(?:home|activities|form|biography|member|research)-e-[A-Za-z0-9_-]+')

for name in files:
    path = Path(name)
    text = path.read_text(encoding='utf-8', errors='ignore')

    def remove_generated_block(match):
        selector_text = match.group(1)
        if pattern.search(selector_text):
            return ''
        return match.group(0)

    new_text = re.sub(r'([^{}]+)\{([^{}]*)\}', remove_generated_block, text, flags=re.S)
    path.write_text(new_text, encoding='utf-8')

print('updated', len(files), 'stylesheets')
