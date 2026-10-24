# English post package (web/) and publishing

The English GlobalNuclearNews site is managed from this repository folder
(`G:\내 드라이브\MY_CODEX\Global Nuclear Daily Brief\GlobalNuclearNews`), but posts are
written elsewhere:

| Board | Writing folder | Site location |
|---|---|---|
| Nuclear Theory | `G:\내 드라이브\My_Claude\Blog-Nuclear\output-EN\<NNN_slug>\` | `posts/theory/<slug>.html` |
| Global Nuclear News | `G:\내 드라이브\My_Claude\Blog\output\drafts_EN\<YYYY-MM-DD-slug>\` | `posts/news/<slug>.html` |
| Concept Dictionary | `G:\내 드라이브\My_Claude\Blog-Nuclear\output-pe-EN\<C-XX-NNN_slug>\` | `posts/concepts/<slug>.html` |

A post folder may hold any working files (draft, fact sheet, figure sources, review notes).
It is published only through its `web/` subfolder:

```
<post folder>/web/
  post.json          metadata (below)
  article.html       the article body that follows the title header
  extra_head.html    optional: a <style> block for this page's <head>
  *.png / *.jpg      every image used in article.html, plus the thumbnail
```

## post.json

```json
{
  "status": "ready",
  "section": "theory",
  "slug": "001-mass-defect",
  "title": "Headline shown on the article page (H1)",
  "page_title": "Text for the browser tab (before ' | GlobalNuclearNews')",
  "description": "Meta description, one sentence",
  "eyebrow": "Nuclear & Radiation Basics · 001",
  "subtitle": "One-sentence standfirst under the headline",
  "date": "2026.10.24",
  "byline_note": "Basics series 001",
  "category": "Nuclear & Radiation Basics",
  "list_title": "Title shown in the board list",
  "summary": "One-sentence summary shown in the board list",
  "thumbnail": "thumbnail.png",
  "thumbnailAlt": "English alt text of the thumbnail",
  "keywords": "space separated search words"
}
```

- `status`: `"ready"` publishes; anything else (e.g. `"draft"`) is skipped.
- `section` must match the writing folder (`theory` for output-EN, `news` for drafts_EN, `concepts` for output-pe-EN).
- Concept Dictionary entries: category = engineering domain (e.g. "Reactor Physics & Kinetics"); the board lists them alphabetically with domain filters. Publish selectively with `--only concepts --match '^C-RX-'`.
- `slug`: lowercase letters, digits and hyphens; it becomes the file and image folder name.
- `date`: `YYYY.MM.DD`. Boards sort newest first.
- News categories (fixed filter buttons): Large Reactors, SMR, Fuel Cycle,
  Policy & Regulation, Advanced Reactors, Marine Nuclear, Space Nuclear, Non-power Uses.
  Theory categories are free text; the theory board builds its buttons from them.
- English only: the publisher refuses packages that contain Korean characters.

## article.html

The body after the title header — lead box, sections, figures, tables, references — using the
site's article markup (`div.lead`, `section > h2/p`, `figure.article-image > img + figcaption`,
`table.article-table`, citation links, a sources/references footer). Refer to images by bare
file name (`src="fig1.png"`); the publisher rewrites them to
`../../assets/images/<section>/<slug>/fig1.png`. Give every `<img>` width, height and English alt
text. See `posts/theory/001-mass-defect.html` and
`posts/news/2026-09-29-nrc-reform-safety-evidence.html` for complete examples.

## Publishing

From this repository folder:

```
python tools/publish_en_posts.py           # write site files, check links, report
python tools/publish_en_posts.py --push    # same, then commit and push to main
python tools/publish_en_posts.py --prune   # also delete site posts whose package is gone
```

The script renders each ready package into the site template, copies its images, rebuilds the
post list in `assets/app.js`, and runs `tools/build_en_site.py`, which aborts if any linked file
is missing. With `--push` it commits only `posts/` and `assets/`, rebases on `origin/main` and
pushes; the Pages workflow redeploys in about a minute. Re-running with no source changes is a
no-op, so revisions are published the same way: edit the package, run the script again.
