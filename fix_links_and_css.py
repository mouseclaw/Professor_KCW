from pathlib import Path

root = Path(__file__).resolve().parent
html_files = [root / 'index.html', root / 'researchs.html', root / 'member.html', root / 'activities.html', root / 'biography.html', root / 'form.html']
css_files = [root / 'researchs.css', root / 'member.css', root / 'activities.css', root / 'biography.css', root / 'form.css']

replacements = {
    'href="home"': 'href="index.html"',
    'href="home#about"': 'href="index.html"',
    'href="home#portfolio"': 'href="index.html"',
    'href="home#blog"': 'href="index.html"',
    'href="home#home"': 'href="index.html"',
    'href="404"': 'href="researchs.html"',
    'href="member"': 'href="member.html"',
    'href="member#students"': 'href="member.html"',
    'href="biography"': 'href="biography.html"',
    'href="activities"': 'href="activities.html"',
    'href="form"': 'href="form.html"',
    'href="researchs"': 'href="researchs.html"',
}

css_block = '''.page-shell,
.page-shell__inner,
.page-header,
.page-hero,
.page-section,
.hero-section,
.hero-copy,
.hero-media,
.research-grid,
.research-copy,
.research-visual,
.section-heading,
.section-card,
.site-footer,
.footer-grid,
.footer-column {
    position: relative;
}

.page-shell {
    width: 100%;
    margin-left: auto;
    margin-right: auto;
}

.page-shell__inner,
.page-header {
    width: 100%;
    margin-left: auto;
    margin-right: auto;
}

.page-shell__inner,
.page-header {
    max-width: 1170px;
}

.page-section,
.hero-section,
.research-grid,
.highlight-grid,
.footer-grid {
    width: 100%;
}

.btn {
    border: 0;
    border-radius: 10px;
    font-family: var(--font-heading);
    font-weight: 700;
    cursor: pointer;
    transition: background-color .2s ease, color .2s ease, transform .2s ease;
}

.btn-outline {
    background-color: transparent;
    color: #fff;
    border: 1px solid rgba(255,255,255,0.3);
}

.site-nav__link {
    font-family: var(--font-body);
    font-size: 16px;
    font-weight: 400;
    line-height: 32px;
    color: #fff;
}

'''

for path in html_files:
    text = path.read_text(encoding='utf-8')
    original = text
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding='utf-8')
        print(f'updated {path.name}')

for path in css_files:
    text = path.read_text(encoding='utf-8')
    if '.page-shell,' not in text:
        if text.startswith('\ufeff'):
            text = text.lstrip('\ufeff')
        text = css_block + text
        path.write_text(text, encoding='utf-8')
        print(f'updated css {path.name}')
