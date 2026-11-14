# xtenzQ profile

README.md is the github.com/xtenzQ profile. Whatever lands on master is live.

## Content
- Short and factual. Nothing a reader could not check.
- Don't repeat nikitar.dev (bio, PhD, hackathons, the PR list); link to it.
- Open source: only "occasional open source fixes" linking to nikitar.dev/oss.
  Don't name projects or describe fixes.
- The "Open to new roles" badge is temporary. When the job search ends, remove it
  and assets/open-to-roles-*.svg.

## Rendering on GitHub
- The sanitizer drops CSS and scripts. Layout is only HTML attributes
  (width, height, align) and entities such as &emsp;.
- Images are static SVGs in assets/, with paths relative to the repo root.
  An SVG shown as <img> can't load web fonts, so its text uses system fonts.
- Theme: either one colour that reads on both backgrounds (icons use #737b85,
  about 4.3:1 on both light and dark),
  or <picture> with a prefers-color-scheme: dark <source>. GitHub's <themed-picture>
  then follows the GitHub theme at page load.
- Icons and text on one line don't align with GitHub's CSS; keep icon rows icon-only.

## Git
- Commit straight to master; no branches or PRs here. Push only when asked.
