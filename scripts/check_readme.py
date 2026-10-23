"""Offline README structure/link checks, not a factual or visual quality score."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.problems, self.links = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style', 'iframe') or 'style' in attrs or any(k.startswith('on') for k in attrs):
            self.problems.append('unsupported_or_active_html')
        for attr in ('src', 'href'):
            if attr in attrs:
                self.links.append(attrs[attr])
        if tag == 'img' and not attrs.get('alt'):
            self.problems.append('image_missing_alt')


def check(root):
    root = Path(root).resolve()
    text = (root / 'README.md').read_text(encoding='utf-8-sig')
    problems = []
    if re.search(r'\{\{[A-Z_]+\}\}', text):
        problems.append('unfilled_template')
    # Check rendered prose/links, not illustrative code snippets.
    prose = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M | re.S)
    elements = Elements()
    elements.feed(prose)
    problems.extend(elements.problems)
    links = re.findall(r'\]\(([^)]+)\)', prose) + elements.links
    for link in links:
        parsed = urlsplit(link)
        if parsed.scheme in ('http', 'https', 'mailto') or link.startswith('#'):
            continue
        if parsed.scheme or link.startswith('//'):
            problems.append('unsupported_link_scheme')
            continue
        path = (root / unquote(parsed.path)).resolve()
        if not path.is_relative_to(root) or not path.exists():
            problems.append('missing_or_outside_local_link')
    if re.search(r'license[-/]MIT', text, flags=re.I):
        license_file = root / 'LICENSE'
        if not license_file.exists() or 'MIT License' not in license_file.read_text(encoding='utf-8'):
            problems.append('license_badge_without_matching_license')
    return sorted(set(problems))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        problems = check(args.root)
    except (OSError, ValueError):
        problems = ['readme_unreadable_or_invalid']
    print('README checks passed' if not problems else '\n'.join(problems))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
