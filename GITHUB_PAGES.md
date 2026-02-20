# GitHub Pages (`gh-pages`) setup for update checks

Yes — this repo can use an orphan `gh-pages` branch exactly like PixelTyper.

## What is expected on `gh-pages`

At minimum, publish `latest.json` at the root of the branch.

Example:

```json
{
  "version": "1.0.1",
  "url": "https://github.com/govindgrover/ImageUtils/releases/download/v1.0.1/ImageUtils.zip",
  "notes": "Bug fixes and improvements"
}
```

The crop app reads this via `config.json -> apps.crop.update_url`.

## One-time branch creation (already done locally)

```bash
git checkout --orphan gh-pages
git rm -rf .
# add latest.json (and optional index.html)
git add latest.json index.html
git commit -m "Initialize gh-pages metadata endpoint"
```

## Publishing steps

1. Push app branch as usual (`work` / `main`).
2. Checkout `gh-pages`, update `latest.json` for each release.
3. Push: `git push -u origin gh-pages`.
4. Enable Pages in GitHub repo settings (Branch: `gh-pages`, folder: `/`).
5. Your endpoint becomes:
   - `https://govindgrover.github.io/ImageUtils/latest.json` (after Pages is enabled)

## Optional helper

Use `scripts/write_latest_json.py` to generate `latest.json` safely.
