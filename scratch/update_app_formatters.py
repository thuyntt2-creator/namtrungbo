import re, os

root = r'C:\Users\lap4all\Desktop\New folder'
app_js_path = os.path.join(root, 'app.js')

with open(app_js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update formatters: fPct, fDiffPct, renderDeltaBadge
# Search for fPct and fDiffPct definition
old_fpct = """  const fPct = (v, d = 1) => (v === null || v === undefined || isNaN(v)) ? '–' : (Number(v) * 100).toFixed(d) + '%';
  const fDiffPct = (v, d = 1) => {
    if (v === null || v === undefined || isNaN(v)) return '–';
    const s = Number(v) > 0 ? '+' : '';
    return s + (Number(v) * 100).toFixed(d) + '%';
  };"""

new_fpct = """  const fPct = (v, d = 1) => (v === null || v === undefined || isNaN(v)) ? '–' : (Number(v) * 100).toFixed(d).replace('.', ',') + '%';
  const fDiffPct = (v, d = 1, unit = '%p') => {
    if (v === null || v === undefined || isNaN(v)) return '–';
    const s = Number(v) > 0 ? '+' : '';
    return s + (Number(v) * 100).toFixed(d).replace('.', ',') + unit;
  };"""

if old_fpct in js:
    js = js.replace(old_fpct, new_fpct)
    print("Replaced fPct and fDiffPct.")
else:
    print("old_fpct not found, doing regex replacement...")
    js = re.sub(
        r'const fPct = \(v, d = 1\) =>[^;]+;',
        "const fPct = (v, d = 1) => (v === null || v === undefined || isNaN(v)) ? '–' : (Number(v) * 100).toFixed(d).replace('.', ',') + '%';",
        js
    )
    js = re.sub(
        r'const fDiffPct = \(v, d = 1\) =>\s*\{[\s\S]*?return s \+ \(Number\(v\) \* 100\)\.toFixed\(d\) \+ \'%\';\s*\};',
        "const fDiffPct = (v, d = 1, unit = '%p') => {\n    if (v === null || v === undefined || isNaN(v)) return '–';\n    const s = Number(v) > 0 ? '+' : '';\n    return s + (Number(v) * 100).toFixed(d).replace('.', ',') + unit;\n  };",
        js
    )

# Replace renderDeltaBadge
old_badge_pat = r'function renderDeltaBadge\(diff, isHigherBetter = true, isPercent = true, unit = \'%p\'\) \{[\s\S]*?return `<span class="diff-tag \$\{cls\}">\$\{arrow\} \$\{formatted\}</span>`;\s*\}'
new_badge = """function renderDeltaBadge(diff, isHigherBetter = true, isPercent = true, unit = '%p') {
    if (diff === null || diff === undefined || isNaN(diff)) {
      return '<span class="diff-tag diff-neutral">–</span>';
    }
    const d = Number(diff);
    if (d === 0) return `<span class="diff-tag diff-neutral">${isPercent ? ('0,0' + unit) : '0 đơn'}</span>`;

    const isGood = isHigherBetter ? d > 0 : d < 0;
    const arrow = d > 0 ? '▲' : '▼';
    const numStr = (d > 0 ? '+' : '') + (d * 100).toFixed(1).replace('.', ',') + unit;
    const formatted = isPercent ? numStr : `${fDiffNum(d)} đơn`;
    const cls = isGood ? 'diff-up-good' : 'diff-down-bad';

    return `<span class="diff-tag ${cls}">${arrow} ${formatted}</span>`;
  }"""

if re.search(old_badge_pat, js):
    js = re.sub(old_badge_pat, lambda m: new_badge, js)
    print("Replaced renderDeltaBadge.")
else:
    print("renderDeltaBadge regex not matched.")

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("app.js formatters updated.")

