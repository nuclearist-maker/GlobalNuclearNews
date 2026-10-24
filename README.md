# GlobalNuclearNews

An English-language public board that explains global nuclear news and core nuclear theory for general readers.

Live site: https://nuclearist-maker.github.io/GlobalNuclearNews/

## Adding or revising a post

Posts are written outside this repository and published from here:

- Nuclear theory: `G:\내 드라이브\My_Claude\Blog-Nuclear\output-EN\<NNN_slug>\web\`
- Concept Dictionary: `G:\내 드라이브\My_Claude\Blog-Nuclear\output-pe-EN\<C-XX-NNN_slug>\web\`
- Global nuclear news: `G:\내 드라이브\My_Claude\Blog\output\drafts_EN\<YYYY-MM-DD-slug>\web\`

Each `web/` package holds `post.json` (metadata, `"status": "ready"` to publish), `article.html` and its images. The format is specified in [docs/english-post-package.md](docs/english-post-package.md).

To update the website after a post is created or revised:

```
python tools/publish_en_posts.py --push
```

The script renders every ready package into `posts/`, copies images into `assets/images/`, rebuilds the post list in `assets/app.js`, checks that every linked file exists, then commits and pushes to `main`. The GitHub Actions workflow (`tools/build_en_site.py` + Pages deploy) publishes the site in about a minute. Run it without `--push` to preview the changes in the working tree first.

## Sources of the English posts

- Nuclear theory posts are English adaptations of the Korean public blog series (working files under `My_Claude/Blog-Nuclear/output-EN/`).
- Concept Dictionary entries are English adaptations of the Korean nuclear power engineering concept notes (working files under `My_Claude/Blog-Nuclear/output-pe-EN/`).
- Body figures keep every number of the original and render all text in English as a separate layer over text-free scene images.

## Korean edition

The previous Korean edition (theory lessons 001–060, four news articles, and its QA pipeline) is preserved in git history at tag `korean-site-2026-10-05`. The Korean-pipeline tools under `tools/`, `qa/`, `policies/` and `docs/` are kept in the repository but are not used by the English deployment.
