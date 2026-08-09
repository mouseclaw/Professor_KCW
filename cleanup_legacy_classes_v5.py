import re
from pathlib import Path

workspace = Path.cwd()
css_files = sorted(workspace.glob('*.css'))
html_files = sorted(workspace.glob('*.html'))
legacy_class_re = re.compile(r'(?<![A-Za-z0-9_-])([A-Za-z0-9_-]+-e-\d+)(?![A-Za-z0-9_-])')
class_attr_re = re.compile(r'(\bclass=["\'])([^"\']*)(["\'])')


def find_matching_brace(text, open_idx):
    depth = 0
    i = open_idx
    in_single = False
    in_double = False
    in_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if in_comment:
            if ch == '*' and nxt == '/':
                in_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_single:
            if ch == '\\':
                i += 2
            elif ch == "'":
                in_single = False
                i += 1
            else:
                i += 1
            continue
        if in_double:
            if ch == '\\':
                i += 2
            elif ch == '"':
                in_double = False
                i += 1
            else:
                i += 1
            continue
        if ch == '/' and nxt == '*':
            in_comment = True
            i += 2
            continue
        if ch == "'":
            in_single = True
            i += 1
            continue
        if ch == '"':
            in_double = True
            i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def strip_legacy_selectors(selector_text):
    cleaned_parts = []
    for raw_part in selector_text.split(','):
        part = raw_part.strip()
        if not part:
            continue
        # Remove any legacy class token from the selector text.
        cleaned = legacy_class_re.sub('', part)
        # remove any stray dot from removed class names and whitespace artifacts
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'\s*([>+~])\s*', r'\1', cleaned)
        if cleaned and cleaned not in {'.', ':', '::'}:
            cleaned_parts.append(cleaned)
    return ', '.join(cleaned_parts)


def process_css(text):
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
        if stripped_prefix and not stripped_prefix.startswith('@'):
            cleaned_selectors = strip_legacy_selectors(stripped_prefix)
            if cleaned_selectors:
                result.append(cleaned_selectors + ' {')
                result.append(body)
                result.append('}')
        else:
            result.append(prefix + '{')
            result.append(process_css(body))
            result.append('}')
        i = close_idx + 1
    return ''.join(result)


# Clean CSS files.
for css_path in css_files:
    css_text = css_path.read_text(encoding='utf-8', errors='ignore')
    cleaned_css = process_css(css_text)
    cleaned_css = re.sub(r'\n{3,}', '\n\n', cleaned_css).strip() + '\n'
    css_path.write_text(cleaned_css, encoding='utf-8')

# Clean HTML class attributes.
for html_path in html_files:
    text = html_path.read_text(encoding='utf-8', errors='ignore')
    new_text = class_attr_re.sub(lambda m: f"{m.group(1)}{' '.join([token for token in m.group(2).split() if not legacy_class_re.fullmatch(token)])}{m.group(3)}", text)
    html_path.write_text(new_text, encoding='utf-8')

# Add a semantic shared wrapper for member cards if missing.
member_css_path = workspace / 'member.css'
member_css_text = member_css_path.read_text(encoding='utf-8', errors='ignore')
if '.member-grid' not in member_css_text:
    member_css_text = member_css_text.replace('.member-card {', '.member-grid {\n    display: flex;\n    flex-wrap: wrap;\n    justify-content: center;\n    gap: 30px;\n    width: 100%;\n}\n\n.member-card {')
    member_css_path.write_text(member_css_text, encoding='utf-8')

# Rewrite the member wrapper class in HTML.
member_html_path = workspace / 'member.html'
member_html_text = member_html_path.read_text(encoding='utf-8', errors='ignore')
member_html_text = member_html_text.replace('class="member-e-20"', 'class="member-grid"')
member_html_path.write_text(member_html_text, encoding='utf-8')

print('legacy cleanup finished')
