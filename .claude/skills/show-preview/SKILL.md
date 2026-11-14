---
name: show-preview
description: Renders the profile README.md, or draft .md files, the way the GitHub profile page shows them, in the light and dark theme and at phone width, using GitHub's own markdown sanitizer and the stylesheets github.com serves today. Use when the user asks to preview, check or compare how the profile README or a draft of it will look on GitHub, and after changing README.md or assets/ before committing.
---

# Show preview

## Quick start

```bash
python3 .claude/skills/show-preview/scripts/render_preview.py --screenshot .preview/profile-preview.png
```

This writes `.preview/profile-preview.html` (gitignored) and a PNG of it, and prints both paths.
Each file gets three cards: desktop light, desktop dark, phone width.

## Workflow

1. Render. With no arguments the script takes `README.md`. To compare drafts, pass them
   all; each one becomes its own section:
   `python3 .claude/skills/show-preview/scripts/render_preview.py README.md drafts/a.md drafts/b.md --screenshot .preview/profile-preview.png`
2. Look at the PNG yourself before showing anything. Check that:
   - no image is broken (the script also warns about missing ones on stderr)
   - no raw markdown or HTML shows as text, which means the sanitizer dropped a tag
   - the dark card is readable: images made for a light page disappear on dark
   - nothing overflows or wraps badly in the phone-width card
3. Show the HTML page to the user. In the Claude desktop app send it with
   `SendUserFile` (`display: "render"`); elsewhere give its path.

## How close it is to github.com

Same as on GitHub:
- what the sanitizer keeps or strips: `gh api markdown` with this repo as context
- fonts, colours and spacing: the profile page's live stylesheets
- the 846px README column, and underlined links as signed-out visitors see them

Approximated:
- the dark card picks the dark `<source>` of each `<picture>` by hand, as GitHub's
  `<themed-picture>` does at page load. Live theme switching is not covered
- the phone card is a 343px column, not GitHub's mobile layout
- relative image paths resolve from the repo root, as for `README.md`. A draft in a
  subfolder may use the same paths it will have once it becomes `README.md`

Only the real site can confirm how GitHub serves files from the repo: after a push,
open the profile page itself.

## Requirements

`gh` signed in, network access, Python 3.9+ (standard library only).
`--screenshot` needs Chrome; set `CHROME` to its binary if it is not in the usual place.
