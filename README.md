# GlobalNuclearNews

An English-language public board that explains global nuclear news and core nuclear theory for general readers.

Live site: https://nuclearist-maker.github.io/GlobalNuclearNews/

## Adding or revising a post

Posts are written outside this repository and published from here:

- Nuclear theory: `G:\내 드라이브\My_Claude\Blog-Nuclear\output-EN\<NNN_slug>\web\`
- Concept Dictionary: `G:\내 드라이브\My_Claude\Blog-Nuclear\output-pe-EN\<C-XX-NNN_slug>\web\`
- Nuclear History: `G:\내 드라이브\My_Claude\Blog-Nuclear\output-history\<NNN_slug>\web\`
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

## Search discovery

Every Pages build enriches the public `_site/` output using `tools/search_discovery.py`:

- Canonical URLs, Open Graph metadata and factual WebSite/Article structured data.
- A complete `sitemap.xml` and `feed.xml` containing the latest 50 entries.
- HTML cards before JavaScript runs (home five; section boards ten), and an ordinary linked `archive/` with ten articles per page. News, theory and concept entries are all discoverable without JavaScript.
- An IndexNow verification file scoped to this GitHub Pages project path.

Source article bodies are untouched. Re-running the publisher or deploying new posts automatically updates discovery files. CI runs `python tools/check_search_discovery.py` before deploying and fails on missing canonical URLs, sitemap coverage, local links, or articles unreachable through HTML links.

The site is hosted under `/GlobalNuclearNews/`. A robots.txt in this directory would not control crawlers: robots.txt must be at `https://nuclearist-maker.github.io/robots.txt`. The host-root file currently returns 404 (no crawl restriction). No ineffective project-level robots.txt is generated. Submit the sitemap directly to webmaster tools.

### Webmaster registration

Site URL: `https://nuclearist-maker.github.io/GlobalNuclearNews/`

Sitemap: `https://nuclearist-maker.github.io/GlobalNuclearNews/sitemap.xml`

RSS: `https://nuclearist-maker.github.io/GlobalNuclearNews/feed.xml`

- Google: add this exact URL-prefix property in [Search Console](https://search.google.com/search-console), verify ownership, then submit `sitemap.xml`.
- Bing/Yahoo: add the site in [Bing Webmaster Tools](https://www.bing.com/webmasters/), verify it, and submit the sitemap. [Yahoo uses Bing submissions](https://sg.help.yahoo.com/kb/SLN2217.html).
- Naver: use [Search Advisor](https://searchadvisor.naver.com/), complete site ownership verification, then submit sitemap/RSS under Requests. If the interface rejects a project subdirectory, host-root ownership or a custom domain needs a separate setup; never verify a different host by assumption.
- Daum: use [Search Registration](https://register.search.daum.net/index.daum). Applicant details and service consent must be supplied by the owner; submission is subject to Daum review.

Real verification values may be added to `tools/search_config.json` under `verification` using keys `google-site-verification`, `naver-site-verification`, or `msvalidate.01`. The build injects these into the homepage HTML. Leave this map empty until the service issues a value. These are public verification tags, not account passwords.

### IndexNow

After deployment, dry-run with `python tools/submit_indexnow.py`. Use `--submit` to verify the live project-scoped key and notify participating search engines about the sitemap URLs. The generated key is a public ownership-verification value, not an account credential. Do not continuously resend unchanged URLs. IndexNow does not replace Google/Naver/Daum registration and an HTTP 200/202 response does not guarantee indexing or ranking.

Official protocol: https://www.indexnow.org/documentation
