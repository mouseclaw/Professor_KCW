import re
from pathlib import Path

workspace = Path.cwd()
css_files = sorted(workspace.glob('*.css'))
html_files = sorted(workspace.glob('*.html'))

legacy_class_re = re.compile(r'(?<![A-Za-z0-9_-])([A-Za-z0-9_-]+-e-\d+)(?![A-Za-z0-9_-])')
html_attr_re = re.compile(r'(\bclass=["\'])([^"\']*)(["\'])')

html_text = '\n'.join(path.read_text(encoding='utf-8', errors='ignore') for path in html_files)
used_in_html = set(legacy_class_re.findall(html_text))


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


def remove_unused_legacy_classes_from_selector(selector, unused_classes):
    cleaned_parts = []
    for raw_part in selector.split(','):
        part = raw_part.strip()
        if not part:
            continue
        for cls in unused_classes:
            pattern = re.compile(rf'(?<![A-Za-z0-9_-])\.{re.escape(cls)}(?![A-Za-z0-9_-])')
            part = pattern.sub('', part)
        part = re.sub(r'\s+', ' ', part).strip()
        part = re.sub(r'\s*([>+~])\s*', r'\1', part)
        if part and part not in {'.', ':', '::'}:
            cleaned_parts.append(part)
    return ', '.join(cleaned_parts)


def process_css(text, unused_classes):
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
            cleaned_selectors = remove_unused_legacy_classes_from_selector(stripped_prefix, unused_classes)
            if cleaned_selectors:
                result.append(cleaned_selectors + ' {')
                result.append(body)
                result.append('}')
        else:
            result.append(prefix + '{')
            result.append(process_css(body, unused_classes))
            result.append('}')
        i = close_idx + 1
    return ''.join(result)


removed_report = []
for css_path in css_files:
    css_text = css_path.read_text(encoding='utf-8', errors='ignore')
    classes_in_css = sorted(set(legacy_class_re.findall(css_text)))
    unused_classes = [cls for cls in classes_in_css if cls not in used_in_html]
    if not unused_classes:
        continue
    cleaned_css = process_css(css_text, unused_classes)
    cleaned_css = re.sub(r'\n{3,}', '\n\n', cleaned_css).strip() + '\n'
    css_path.write_text(cleaned_css, encoding='utf-8')
    removed_report.append((css_path.name, unused_classes))

# Strip legacy classes from HTML class attrs.
for html_path in html_files:
    text = html_path.read_text(encoding='utf-8', errors='ignore')
    def repl(match):
        prefix, value, suffix = match.group(1), match.group(2), match.group(3)
        tokens = [token for token in value.split() if not legacy_class_re.fullmatch(token)]
        return prefix + ' '.join(tokens) + suffix
    new_text = html_attr_re.sub(repl, text)
    html_path.write_text(new_text, encoding='utf-8')

summary_lines = ['Legacy class cleanup summary', '===========================', '']
for css_name, classes in removed_report:
    summary_lines.append(f'[{css_name}]')
    for cls in classes:
        summary_lines.append(f'- removed: {cls}')
    summary_lines.append('')
summary_lines.append('HTML cleanup: removed legacy -e- class tokens from class attributes.')
summary_path = workspace / 'legacy_class_cleanup_report.txt'
summary_path.write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')
print('cleanup complete')
print(summary_path)
