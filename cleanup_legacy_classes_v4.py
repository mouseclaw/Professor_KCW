import re
from pathlib import Path

workspace = Path.cwd()
css_files = sorted(workspace.glob('*.css'))
html_files = sorted(workspace.glob('*.html'))

legacy_class_re = re.compile(r'(?<![A-Za-z0-9_-])([A-Za-z0-9_-]+-e-\d+)(?![A-Za-z0-9_-])')
class_attr_re = re.compile(r'(\bclass=["\'])([^"\']*)(["\'])')


def find_matching_brace(text, start_idx):
    depth = 0
    i = start_idx
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


def remove_legacy_classes_from_selector(selector, legacy_classes):
    parts = []
    for raw_part in selector.split(','):
        part = raw_part.strip()
        if not part:
            continue
        cleaned = part
        for cls in legacy_classes:
            cleaned = re.sub(rf'(?<![A-Za-z0-9_-])\.{re.escape(cls)}(?![A-Za-z0-9_-])', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        cleaned = re.sub(r'\s*([>+~])\s*', r'\1', cleaned)
        if cleaned and cleaned not in {'.', ':', '::'}:
            parts.append(cleaned)
    return ', '.join(parts)


def process_css(text, legacy_classes):
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
            cleaned_selectors = remove_legacy_classes_from_selector(stripped_prefix, legacy_classes)
            if cleaned_selectors:
                result.append(cleaned_selectors + ' {')
                result.append(body)
                result.append('}')
        else:
            result.append(prefix + '{')
            result.append(process_css(body, legacy_classes))
            result.append('}')
        i = close_idx + 1
    return ''.join(result)


# Collect legacy class names from all CSS files.
all_legacy_classes = []
for css_path in css_files:
    css_text = css_path.read_text(encoding='utf-8', errors='ignore')
    all_legacy_classes.extend(legacy_class_re.findall(css_text))
legacy_classes = sorted(set(all_legacy_classes))

removed_by_file = {}
for css_path in css_files:
    css_text = css_path.read_text(encoding='utf-8', errors='ignore')
    cleaned_css = process_css(css_text, legacy_classes)
    cleaned_css = re.sub(r'\n{3,}', '\n\n', cleaned_css).strip() + '\n'
    css_path.write_text(cleaned_css, encoding='utf-8')
    removed_by_file[css_path.name] = [cls for cls in legacy_classes if cls in css_text]

# Clean HTML class attributes and swap the member wrapper to a semantic shared class.
html_replacements = {
    'member-e-20': 'member-grid',
}
for html_path in html_files:
    text = html_path.read_text(encoding='utf-8', errors='ignore')

    def repl(match):
        prefix, value, suffix = match.group(1), match.group(2), match.group(3)
        tokens = []
        for token in value.split():
            if token in html_replacements:
                tokens.append(html_replacements[token])
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
    insert_point = member_css_text.index('.member-card {')
    member_css_text = member_css_text[:insert_point] + '.member-grid {\n    display: flex;\n    flex-wrap: wrap;\n    justify-content: center;\n    gap: 30px;\n    width: 100%;\n}\n\n' + member_css_text[insert_point:]
    member_css_path.write_text(member_css_text, encoding='utf-8')

# Write a summary report.
summary_lines = ['Legacy class cleanup summary', '===========================', '']
for css_name, classes in removed_by_file.items():
    summary_lines.append(f'[{css_name}]')
    for cls in classes:
        summary_lines.append(f'- removed CSS selectors for: {cls}')
    summary_lines.append('')
summary_lines.append('HTML cleanup: removed legacy -e- classes from class attributes and replaced member wrapper with member-grid.')
summary_path = workspace / 'legacy_class_cleanup_report.txt'
summary_path.write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')

print('cleanup complete')
print(summary_path)
