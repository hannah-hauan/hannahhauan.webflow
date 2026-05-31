import pathlib
import re
import shutil
import cssutils
import logging

cssutils.log.setLevel(logging.FATAL)
root = pathlib.Path('.')
html_files = sorted(root.glob('*.html')) + sorted(root.glob('**/*.html'))
html_text = ''
for html in html_files:
    if html.is_file():
        html_text += html.read_text(errors='ignore')

used_classes = set()
for m in re.finditer(r'class=["\"][^"\"]*["\"]', html_text):
    used_classes.update(re.findall(r'\b([A-Za-z0-9_-]+)\b', m.group(0)))

used_ids = set()
for m in re.finditer(r'id=["\"][^"\"]*["\"]', html_text):
    used_ids.update(re.findall(r'\b([A-Za-z0-9_-]+)\b', m.group(0)))

print('HTML files scanned:', len(html_files))
print('Detected classes:', len(used_classes))
print('Detected ids:', len(used_ids))

css_paths = [pathlib.Path('css/webflow.css'), pathlib.Path('css/hannahhauan.webflow.css')]
for css_path in css_paths:
    if not css_path.exists():
        print(f'Skipping missing file: {css_path}')
        continue

    bak_path = css_path.with_name(css_path.name + '.bak')
    if bak_path.exists():
        counter = 2
        while True:
            candidate = css_path.with_name(f'{css_path.name}.bak{counter}')
            if not candidate.exists():
                bak_path = candidate
                break
            counter += 1
    shutil.copy2(css_path, bak_path)
    original_size = css_path.stat().st_size

    sheet = cssutils.parseString(css_path.read_text())
    removed_selectors = 0
    removed_rules = 0
    removed_media_rules = 0

    def selector_is_used(selector: str) -> bool:
        classes = re.findall(r'\.([A-Za-z0-9_-]+)', selector)
        ids = re.findall(r'#([A-Za-z0-9_-]+)', selector)
        if not classes and not ids:
            return True
        return any(c in used_classes for c in classes) or any(i in used_ids for i in ids)

    def clean_style_rule(rule):
        global removed_selectors, removed_rules
        selectors = [s.strip() for s in rule.selectorText.split(',') if s.strip()]
        keep = []
        for sel in selectors:
            if selector_is_used(sel):
                keep.append(sel)
            else:
                removed_selectors += 1
        if keep:
            rule.selectorText = ', '.join(keep)
            return False
        removed_rules += 1
        return True

    for rule in list(sheet.cssRules):
        if rule.type == rule.STYLE_RULE:
            if clean_style_rule(rule):
                sheet.deleteRule(rule)
        elif rule.type == rule.MEDIA_RULE:
            for inner in list(rule.cssRules):
                if inner.type == inner.STYLE_RULE and clean_style_rule(inner):
                    rule.deleteRule(inner)
            if not rule.cssRules:
                sheet.deleteRule(rule)
                removed_media_rules += 1

    new_css = sheet.cssText.decode('utf-8') if isinstance(sheet.cssText, bytes) else str(sheet.cssText)
    css_path.write_text(new_css)
    new_size = css_path.stat().st_size

    print(f'Processed {css_path.name}:')
    print(f'  backup created: {bak_path.name}')
    print(f'  original size: {original_size} bytes')
    print(f'  new size:      {new_size} bytes')
    print(f'  removed selectors: {removed_selectors}')
    print(f'  removed rules: {removed_rules}')
    print(f'  removed empty @media rules: {removed_media_rules}')
