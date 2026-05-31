import pathlib
import re
import cssutils

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

print('HTML files count', len(html_files))
print('Used classes', len(used_classes))
print('Used ids', len(used_ids))

for css_path in [pathlib.Path('css/webflow.css'), pathlib.Path('css/hannahhauan.webflow.css')]:
    if not css_path.exists():
        continue
    sheet = cssutils.parseString(css_path.read_text())
    total_sel = 0
    remove_sel = 0
    remove_rules = 0
    for rule in sheet.cssRules:
        if rule.type == rule.STYLE_RULE:
            selectors = [s.strip() for s in rule.selectorText.split(',') if s.strip()]
            keep = []
            for sel in selectors:
                total_sel += 1
                classes = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
                ids = re.findall(r'#([A-Za-z0-9_-]+)', sel)
                if not classes and not ids:
                    keep.append(sel)
                    continue
                if any(cls in used_classes for cls in classes) or any(i in used_ids for i in ids):
                    keep.append(sel)
                else:
                    remove_sel += 1
            if not keep:
                remove_rules += 1
        elif rule.type == rule.MEDIA_RULE:
            for inner in rule.cssRules:
                if inner.type == inner.STYLE_RULE:
                    selectors = [s.strip() for s in inner.selectorText.split(',') if s.strip()]
                    for sel in selectors:
                        total_sel += 1
                        classes = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
                        ids = re.findall(r'#([A-Za-z0-9_-]+)', sel)
                        if not classes and not ids:
                            continue
                        if any(cls in used_classes for cls in classes) or any(i in used_ids for i in ids):
                            continue
                        remove_sel += 1
    print(css_path.name, 'total selectors', total_sel, 'unused selectors', remove_sel, 'possible whole rules', remove_rules)
