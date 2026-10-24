# GlobalNuclearNews

An English-language public board that explains global nuclear news and core nuclear theory for general readers.

Live site: https://nuclearist-maker.github.io/GlobalNuclearNews/

## Adding a post

1. Put news articles in `posts/news/` and nuclear theory articles in `posts/theory/` (do not mix them directly under `posts/`).
2. Register the post in the `posts` array in `assets/app.js` (title, date, `section`: `"news"` or `"theory"`, category, one-sentence summary, thumbnail path and alt text, URL, keywords). The theory board builds its category buttons automatically from the posts' `category` values.
3. Push to `main`. The GitHub Actions workflow runs `tools/build_en_site.py`, which packages only the files the pages actually link to and aborts on any missing image or page, then deploys to GitHub Pages.

## Sources of the English posts

- Nuclear theory posts are English adaptations of the Korean public blog series (working files under `My_Claude/Blog-Nuclear/output-EN/`).
- Body figures keep every number of the original and render all text in English as a separate layer over text-free scene images.

## Korean edition

The previous Korean edition (theory lessons 001–060, four news articles, and its QA pipeline) is preserved in git history at tag `korean-site-2026-10-05`. The Korean-pipeline tools under `tools/`, `qa/`, `policies/` and `docs/` are kept in the repository but are not used by the English deployment.
