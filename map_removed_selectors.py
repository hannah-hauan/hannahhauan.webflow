import pathlib
import re
import json
import cssutils

root = pathlib.Path('.')
css_pairs = [
    (pathlib.Path('css/webflow.css.bak'), pathlib.Path('css/webflow.css')),
    (pathlib.Path('css/hannahhauan.webflow.css.bak'), pathlib.Path('css/hannahhauan.webflow.css')),
]

all_removed_selectors = set()

for bak, new in css_pairs:
    if not bak.exists():
        # try bak2 for webflow.css
        alt = bak.with_name(bak.name + '2')
        if alt.exists():
            bak = alt
        else:
            continue
    if not new.exists():
        continue
    try:
        bak_sheet = cssutils.parseString(bak.read_text())
        new_sheet = cssutils.parseString(new.read_text())
    except Exception as e:
        print('css parse error', bak, new, e)
        continue

    def collect_selectors(sheet):
        sels = set()
        for rule in sheet.cssRules:
            if rule.type == rule.STYLE_RULE:
                for s in rule.selectorText.split(','):
                    s = s.strip()
                    if s:
                        sels.add(s)
            elif rule.type == rule.MEDIA_RULE:
                for inner in rule.cssRules:
                    if inner.type == inner.STYLE_RULE:
                        for s in inner.selectorText.split(','):
                            s = s.strip()
                            if s:
                                sels.add(s)
        return sels

    bak_sels = collect_selectors(bak_sheet)
    new_sels = collect_selectors(new_sheet)
    removed = bak_sels - new_sels
    all_removed_selectors.update(removed)

# extract simple class/id tokens from selectors
removed_classes = set()
removed_ids = set()
for sel in all_removed_selectors:
    removed_classes.update(re.findall(r'\.([A-Za-z0-9_-]+)', sel))
    removed_ids.update(re.findall(r'#([A-Za-z0-9_-]+)', sel))

# find html files
html_files = sorted(root.glob('*.html')) + sorted(root.glob('**/*.html'))
report = {}
for html in html_files:
    if not html.is_file():
        continue
    text = html.read_text(errors='ignore')
    used_cls = set(re.findall(r'class=["\"][^"\"]*["\"]', text))
    used_ids_tokens = set(re.findall(r'id=["\"][^"\"]*["\"]', text))
    # flatten class attribute values
    classes_in_file = set()
    for c in used_cls:
        classes_in_file.update(re.findall(r'\b([A-Za-z0-9_-]+)\b', c))
    ids_in_file = set()
    for i in used_ids_tokens:
        ids_in_file.update(re.findall(r'\b([A-Za-z0-9_-]+)\b', i))

    intersect_classes = sorted(list(classes_in_file & removed_classes))
    intersect_ids = sorted(list(ids_in_file & removed_ids))
    if intersect_classes or intersect_ids:
        report[str(html)] = {
            'removed_classes_used': intersect_classes,
            'removed_ids_used': intersect_ids,
        }

out = {
    'summary':{
        'html_files_scanned': len(html_files),
        'removed_selectors_count': len(all_removed_selectors),
        'removed_classes_count': len(removed_classes),
        'removed_ids_count': len(removed_ids),
        'files_with_removed_usage': len(report)
    },
    'details': report
}

pathlib.Path('removed_selectors_report.json').write_text(json.dumps(out, indent=2))
print('Wrote removed_selectors_report.json')
print(json.dumps(out['summary'], indent=2))
