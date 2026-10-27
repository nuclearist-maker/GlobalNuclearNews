"""Accessible, repeatable support navigation for every published content page."""
import re

PAGES = (("about.html", "About"), ("contact.html", "Contact"),
         ("privacy.html", "Privacy Policy"), ("editorial-policy.html", "Editorial Policy"))


def add_support_navigation(text, base, relative):
    text = re.sub(r'<!-- site-information:start -->.*?<!-- site-information:end -->', '', text, flags=re.S)
    links = []
    for path, label in PAGES:
        current = ' aria-current="page"' if path == relative else ''
        links.append(f'<a href="{base}{path}"{current}>{label}</a>')
    block = ('<!-- site-information:start --><nav aria-label="Site information" '
             'style="display:flex;flex-wrap:wrap;justify-content:center;text-align:center;gap:12px 24px;padding:20px 24px;'
             'background:#061827;color:#fff;font:16px/1.6 Arial,sans-serif">'
             + ''.join(links) + '</nav><!-- site-information:end -->')
    if '</body>' not in text:
        raise ValueError('Missing body close: ' + relative)
    return text.replace('</body>', block + '</body>', 1)
