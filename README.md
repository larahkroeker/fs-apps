# fs-apps

Small static tools and client-facing pages, published with GitHub Pages.

**Base URL:** https://larahkroeker.github.io/fs-apps/

Everything is plain HTML — no build step, no dependencies, no framework. `.nojekyll` is present, so
files are served exactly as committed. Push to `main` and it's live in under a minute.

## What's here

| Page | URL | Notes |
| --- | --- | --- |
| FS Time Tracker | [`index.html`](https://larahkroeker.github.io/fs-apps/) | Time tracking tool |
| AI Creative Workflows | [`ai-creative-workflows.html`](https://larahkroeker.github.io/fs-apps/ai-creative-workflows.html) | |
| Website Updates | [`website-updates.html`](https://larahkroeker.github.io/fs-apps/website-updates.html) | |
| Oliver — Content Board | [`clients/OLIVER-content-board.html`](https://larahkroeker.github.io/fs-apps/clients/OLIVER-content-board.html) | Generated — see [`_src/oliver-board`](_src/oliver-board/README.md). `noindex`. |
| Oliver — Form Prototype | [`clients/OLIVER-form-prototype.html`](https://larahkroeker.github.io/fs-apps/clients/OLIVER-form-prototype.html) | Proposed rework of the Request a Demo form |

## Generated pages

Most pages here are hand-written and edited in place. The Oliver content board is different — it's
generated from data by a script. Its source lives in `_src/oliver-board/`, and **editing
`clients/OLIVER-content-board.html` by hand will be overwritten** on the next build. Edit the source
instead: see [`_src/oliver-board/README.md`](_src/oliver-board/README.md).

`_src/` holds build sources, not published pages.

## Publishing

```bash
cd ~/Sites/fs-apps
git add -A && git commit -m "..." && git push
```

## Anything in this repo is public

GitHub Pages has no access control — no password, no login. `noindex` keeps a page out of search
results, but anyone with the URL can read it. Don't commit credentials, client data you wouldn't
want forwarded, or anything under NDA. Where a generated page needs data that shouldn't be public,
keep the data gitignored and local (see the Oliver board's `sheet.json`).
