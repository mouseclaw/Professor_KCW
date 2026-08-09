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
    selectors = []
    for raw_part in selector_text.split(','):
        part = raw_part.strip()
        if not part:
            continue
        cleaned = legacy_class_re.sub('', part)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'\s*([>+~])\s*', r'\1', cleaned)
        if cleaned and cleaned not in {'.', ':', '::'}:
            selectors.append(cleaned)
    return ', '.join(selectors)


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
removed_by_file = {}
for css_path in css_files:
    css_text = css_path.read_text(encoding='utf-8', errors='ignore')
    classes_in_css = sorted(set(legacy_class_re.findall(css_text)))
    cleaned_css = process_css(css_text)
    cleaned_css = re.sub(r'\n{3,}', '\n\n', cleaned_css).strip() + '\n'
    css_path.write_text(cleaned_css, encoding='utf-8')
    removed_by_file[css_path.name] = classes_in_css

# Clean HTML class attributes and swap the member wrapper to a semantic shared class.
for html_path in html_files:
    text = html_path.read_text(encoding='utf-8', errors='ignore')
    def repl(match):
        prefix, value, suffix = match.group(1), match.group(2), match.group(3)
        tokens = []
        for token in value.split():
            if token == 'member-e-20':
                tokens.append('member-grid')
            elif legacy_class_re.fullmatch(token):
                continue
            else:
                tokens.append(token)
        return prefix + ' '.join(tokens) + suffix
    new_text = class_attr_re.sub(repl, text)
    html_path.write_text(new_text, encoding='utf-8')

# Add shared styles for the member wrapper replacement.
member_css_path = workspace / 'member.css'
member_css_text = member_css_path.read_text(encoding='utf-8', errors='ignore')
if '.member-grid' not in member_css_text:
    member_css_text = member_css_text.replace('.member-card {', '.member-grid {\n    display: flex;\n    flex-wrap: wrap;\n    justify-content: center;\n    gap: 30px;\n    width: 100%;\n}\n\n.member-card {')
    member_css_path.write_text(member_css_text, encoding='utf-8')

# Write a summary report.
summary_lines = ['Legacy class cleanup summary', '===========================', '']
for css_name, classes in removed_by_file.items():
    summary_lines.append(f'[{css_name}]')
    if classes:
        for cls in classes:
            summary_lines.append(f'- removed: {cls}')
    else:
        summary_lines.append('- no legacy -e- selectors found')
    summary_lines.append('')
summary_lines.append('HTML cleanup: removed legacy -e- class tokens from class attributes and replaced member-e-20 with member-grid.')
summary_path = workspace / 'legacy_class_cleanup_report.txt'
summary_path.write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')

print('legacy cleanup finished')
print(summary_path)
