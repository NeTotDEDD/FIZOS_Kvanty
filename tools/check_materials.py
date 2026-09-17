"""Check local links, anchors, images and math delimiters without dependencies."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

ROOT = Path(__file__).resolve().parents[1]
errors = []
links = images = tasks = formulas = 0
for path in sorted(ROOT.rglob('*.md')):
    if '.git' in path.parts:
        continue
    text = path.read_text(encoding='utf-8')
    anchors = re.findall(r'<a (?:name|id)="([^"]+)"', text)
    if len(anchors) != len(set(anchors)):
        errors.append(f'{path.name}: duplicate anchors')
    if path.parent.name == 'weeks':
        n = text.count('**Условие.**')
        tasks += n
        if n != 9:
            errors.append(f'{path.name}: expected 9 tasks, found {n}')
    if re.search(r'[A-Z]:[\\/]|file://', text):
        errors.append(f'{path.name}: local absolute path')
    blocks = re.findall(r'^```math\n[\s\S]*?\n```', text, re.M)
    stripped = re.sub(r'^```math\n[\s\S]*?\n```', '', text, flags=re.M)
    if '```math' in stripped or '$$' in stripped:
        errors.append(f'{path.name}: unmatched math block')
    inline = re.findall(r'\$`[^\n]*?`\$', stripped)
    formulas += len(blocks) + len(inline)
    stripped = re.sub(r'\$`[^\n]*?`\$', '', stripped)
    if '$' in stripped:
        errors.append(f'{path.name}: unprotected inline math')
    for match in re.finditer(r'(!?)\[[^\]]*\]\(([^)]+)\)', stripped):
        is_image, url = match.groups()
        parts = urlsplit(unquote(url))
        if parts.scheme or parts.netloc:
            continue
        target = (path.parent / parts.path).resolve() if parts.path else path
        if not target.is_relative_to(ROOT) or not target.is_file():
            errors.append(f'{path.name}: missing {url}')
            continue
        if parts.fragment:
            anchors_at_target = re.findall(r'<a (?:name|id)="([^"]+)"', target.read_text(encoding='utf-8'))
            if parts.fragment not in anchors_at_target:
                errors.append(f'{path.name}: missing anchor {url}')
        if is_image:
            images += 1
            if target.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
                errors.append(f'{target.name}: invalid PNG')
        links += 1
assert not errors, '\n'.join(errors)
print(f'OK: {tasks} tasks, {formulas} formulas, {images} images, {links} local links')
