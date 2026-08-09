from pathlib import Path
import re

root = Path('.')
html_files = [root / 'index.html', root / 'activities.html', root / 'biography.html', root / 'form.html', root / 'member.html', root / 'researchs.html']
css_files = [root / 'index.css', root / 'activities.css', root / 'biography.css', root / 'form.css', root / 'member.css', root / 'researchs.css', root / 'site.css']
legacy_class_re = re.compile(r'\b[a-zA-Z0-9_-]+-e-\d+\b')
html_class_re = re.compile(r'(\bclass=["\'])([^"\']*)(["\'])')

for html_path in html_files:
    text = html_path.read_text(encoding='utf-8', errors='ignore')

    def repl(match):
        prefix, value, suffix = match.group(1), match.group(2), match.group(3)
        tokens = [token for token in value.split() if not legacy_class_re.fullmatch(token)]
        return f'{prefix}{" ".join(tokens)}{suffix}'

    new_text = html_class_re.sub(repl, text)
    new_text = new_text.replace('class=""', '')
    new_text = new_text.replace("class=''", '')
    html_path.write_text(new_text, encoding='utf-8')


def find_matching_brace(text, open_idx):
    depth = 0
    in_single = False
    in_double = False
    i = open_idx
    while i < len(text):
        ch = text[i]
        if ch == "'" and not in_double and (i == 0 or text[i - 1] != '\\'):
            in_single = not in_single
        elif ch == '"' and not in_single and (i == 0 or text[i - 1] != '\\'):
            in_double = not in_double
        elif not in_single and not in_double:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def strip_legacy_css_blocks(text):
    result = []
    i = 0
    while i < len(text):
        open_idx = text.find('{', i)
        if open_idx == -1:
            result.append(text[i:])
            break
        prefix = text[i:open_idx]
        close_idx = find_matching_brace(text, open_idx)
        if close_idx == -1:
            result.append(text[i:])
            break
        body = text[open_idx + 1:close_idx]
        stripped_prefix = prefix.strip()
        if stripped_prefix and not stripped_prefix.startswith('@') and legacy_class_re.search(stripped_prefix):
            # Drop legacy-generated class rules entirely.
            pass
        else:
            result.append(prefix + '{')
            result.append(strip_legacy_css_blocks(body))
            result.append('}')
        i = close_idx + 1
    return ''.join(result)

for css_path in css_files:
    text = css_path.read_text(encoding='utf-8', errors='ignore')
    new_text = strip_legacy_css_blocks(text)
    new_text = re.sub(r'\n{3,}', '\n\n', new_text).strip() + '\n'
    css_path.write_text(new_text, encoding='utf-8')

print('Legacy class cleanup complete.')
