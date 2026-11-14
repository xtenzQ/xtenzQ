"""Render profile README markdown the way the GitHub profile page shows it.

    python3 render_preview.py [FILE.md ...] [--out PAGE.html] [--screenshot PAGE.png]

FILE.md defaults to README.md at the repo root. Each file becomes one section with
three cards: desktop light, desktop dark, and phone width (light).

- Markdown goes through GitHub's own renderer (`gh api markdown` with this repo as
  context): the same sanitizer as the profile README.
- Stylesheets are the ones the live profile page loads, so fonts, colours and spacing
  match github.com today.
- Relative image paths resolve from the repo root (where README.md lives) and are
  embedded as data URIs: the Claude desktop app opens HTML without its neighbouring
  files, so a page that links ./assets would show broken images there.
- For the dark card, <picture> is resolved to its dark <source>, which is what GitHub's
  <themed-picture> does at page load when the GitHub theme is dark.
"""
import argparse
import base64
import html
import mimetypes
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(
    subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True,
                   cwd=pathlib.Path(__file__).parent).stdout.strip()
)
DESKTOP_WIDTH = 878  # 846px README column + 2 x 16px around the card
PHONE_WIDTH = 375    # 343px card + 2 x 16px page gutter


def repo_slug() -> str:
    url = subprocess.run(["git", "remote", "get-url", "origin"], check=True, capture_output=True,
                         text=True, cwd=ROOT).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if not m:
        sys.exit(f"origin is not a GitHub repo: {url}")
    return f"{m.group(1)}/{m.group(2)}"


def stylesheets(owner: str) -> list[str]:
    req = urllib.request.Request(f"https://github.com/{owner}", headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=30).read().decode()
    hrefs = re.findall(r'<link[^>]*rel="stylesheet"[^>]*\shref="([^"]+\.css)"', page)
    if not hrefs:
        sys.exit("found no stylesheets on the profile page; GitHub markup may have changed")
    return list(dict.fromkeys(hrefs))


def render(md: str, slug: str) -> str:
    return subprocess.run(
        ["gh", "api", "markdown", "-f", "mode=gfm", "-f", f"context={slug}", "-f", f"text={md}"],
        check=True, capture_output=True, text=True,
    ).stdout


def inline_assets(body: str) -> str:
    def data_uri(m: re.Match) -> str:
        attr, ref = m.group(1), m.group(2)
        if re.match(r"^(https?:|data:|//|#|mailto:)", ref):
            return m.group(0)
        path = (ROOT / ref.lstrip("/")).resolve()
        if not path.is_file():
            print(f"warning: missing image {ref}", file=sys.stderr)
            return m.group(0)
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return f'{attr}="data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"'
    return re.sub(r'\b(src|srcset)="([^"]+)"', data_uri, body)


def dark(body: str) -> str:
    return re.sub(
        r'(<source media="\(prefers-color-scheme: dark\)" srcset="([^"]+)">\s*<img[^>]*?)src="[^"]+"',
        r'\1src="\2"',
        body,
    )


def card(body: str, slug: str, theme: str, label: str, width: int) -> str:
    owner = slug.split("/")[0]
    attrs = f'data-color-mode="{theme}" data-light-theme="light" data-dark-theme="dark"'
    return f"""
  <figure style="width:{width}px">
    <figcaption>{label}</figcaption>
    <div class="theme color-bg-default color-fg-default" {attrs}>
      <div class="Box profile-readme">
        <div class="Box-body p-4">
          <div class="text-mono text-small mb-3">{owner}<span class="color-fg-muted" style="padding:0 2px">/</span>README<span class="color-fg-muted">.md</span></div>
          <article class="markdown-body entry-content container-lg f5">{body}</article>
        </div>
      </div>
    </div>
  </figure>"""


def screenshot(page: pathlib.Path, png: pathlib.Path, sections: int) -> None:
    chrome = os.environ.get("CHROME") or next(
        (p for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                     shutil.which("google-chrome"), shutil.which("chromium")] if p and os.path.exists(p)),
        None,
    )
    if not chrome:
        sys.exit("no Chrome found for --screenshot; set CHROME to its binary")
    subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
         # three cards in one row; roughly one section per 480px, cropped empty space is cheap
         f"--window-size={2 * DESKTOP_WIDTH + PHONE_WIDTH + 2 * 12 + 2 * 24},{80 + 480 * sections}",
         "--virtual-time-budget=5000", f"--screenshot={png}", page.as_uri()],
        check=True, capture_output=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=pathlib.Path, help="markdown files (default: README.md)")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / ".preview" / "profile-preview.html")
    ap.add_argument("--screenshot", type=pathlib.Path, help="also save a PNG of the page")
    args = ap.parse_args()

    slug = repo_slug()
    files = args.files or [ROOT / "README.md"]
    sections = []
    for f in files:
        body = inline_assets(render(f.read_text(), slug))
        sections.append(f"""
<section>
  <h2>{html.escape(str(f.resolve().relative_to(ROOT)) if f.resolve().is_relative_to(ROOT) else f.name)}</h2>
  <div class="row">{card(body, slug, "light", "light", DESKTOP_WIDTH)}{card(dark(body), slug, "dark", "dark", DESKTOP_WIDTH)}{card(body, slug, "light", "phone width", PHONE_WIDTH)}</div>
</section>""")

    links = "\n".join(f'<link rel="stylesheet" crossorigin="anonymous" href="{h}">'
                      for h in stylesheets(slug.split("/")[0]))
    page = f"""<!doctype html>
<html lang="en" data-color-mode="light" data-light-theme="light" data-dark-theme="dark" data-a11y-link-underlines="true">
<head>
<meta charset="utf-8">
<title>Profile README preview</title>
{links}
<style>
  body {{ padding: 24px; background: #8c959f; }}
  section {{ margin-bottom: 32px; }}
  h2, figcaption {{ color: #fff; font: 600 13px ui-monospace, monospace; margin: 0 0 8px; }}
  .row {{ display: flex; flex-wrap: wrap; align-items: flex-start; gap: 12px; }}
  figure {{ margin: 0; max-width: 100%; }}
  .theme {{ padding: 16px; border-radius: 8px; }}
</style>
</head>
<body>
{"".join(sections)}
</body>
</html>
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page)
    print(args.out)
    if args.screenshot:
        screenshot(args.out.resolve(), args.screenshot, len(files))
        print(args.screenshot)


if __name__ == "__main__":
    main()
