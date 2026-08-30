# bathypinto — personal site

Static HTML. No build step, no framework, no dependencies. Built to `SPEC.md`.
Deploy target: **Netlify free tier**.

```
site/
├── index.html            all sections
├── 404.html
├── netlify.toml          headers, caching, redirects
├── robots.txt
├── sitemap.xml
├── site.webmanifest
└── assets/
    ├── css/site.css
    ├── js/site.js        ~4 KB, vanilla
    └── img/              placeholders — replace all of these
```

---

## Deploying to Netlify

**Drag and drop — 60 seconds, no account setup beyond signup**

1. Go to <https://app.netlify.com/drop>
2. Drag the **`site` folder itself** onto the page.
3. You get a live URL like `random-name-123.netlify.app` immediately.

This is the fastest way to see it live, but every future update means dragging again.

**Git-connected — recommended for anything you'll keep editing**

1. Push this folder to a GitHub repo (the folder contents at the repo root).
2. Netlify → *Add new site* → *Import an existing project* → pick the repo.
3. Build settings: **build command empty**, **publish directory `.`** (or `site` if the
   folder sits inside the repo). `netlify.toml` already declares this.
4. Deploy. Every `git push` now redeploys automatically.

**After the first deploy**

- *Site configuration → Change site name* → set something like `bathypinto`.
- Custom domain: *Domain management → Add a domain*. Netlify issues the Let's Encrypt
  certificate automatically; allow a few minutes.
- Then do the domain find-and-replace below — six places still say `example.netlify.app`.

```bash
# from inside the site folder, after you know your real domain
grep -rl "example.netlify.app" . | xargs sed -i '' "s|example.netlify.app|YOURDOMAIN|g"   # macOS
grep -rl "example.netlify.app" . | xargs sed -i     "s|example.netlify.app|YOURDOMAIN|g"   # Linux
```

Also uncomment the canonical-host redirect at the bottom of `netlify.toml` so the
`.netlify.app` URL and your custom domain don't both get indexed.

**Previewing locally**

```bash
cd site && python3 -m http.server 8000
# then open http://localhost:8000
```

Use a server, not `file://` — the root-relative `/assets/…` paths won't resolve otherwise.

---

## Edit checklist

Every spot needing your content is marked `<!-- EDIT ... -->` in `index.html`.
Find them all with:

```bash
grep -n "EDIT" index.html
```

Fill them from `intro.md` — the placeholder names match.

| # | Where | What |
|---|---|---|
| 1 | `<head>` | Title, meta description, canonical + OG URLs, JSON-LD `Person` |
| 2 | Hero | Eyebrow (role · location), headline, subhead, both CTA labels |
| 3 | Proof strip | 3–5 stats. `data-count="42"` drives the count-up; use `—` or drop the attribute for non-numeric values |
| 4 | About | Three paragraphs: through-line, evidence, direction |
| 5 | Experience | One `<li>` per role, newest first. Extras go in the `<details>` block |
| 6 | Education | Degrees and certifications |
| 7 | Capabilities | 3–6 areas. Renumber `01`, `02`… by hand |
| 8 | Work | One `<article>` per project. Image side alternates automatically |
| 9 | Speaking | One `<li>` per talk or article |
| 10 | Testimonials | One `<figure>` per quote — the counter updates itself |
| 11 | Contact | Email, location, timezone, social links |
| 12 | Everywhere | `Bathy Pinto` → your exact preferred name |

**Before launch:** delete the `<div class="draft">` banner in `index.html` (and its
`.draft` rules in `site.css` if you want the file tidy).

Stray file: `assets/cv.pdf.README.txt` was left over from scaffolding — delete it manually,
it isn't referenced anywhere.

---

## Replacing the images

Placeholders exist at every path so nothing 404s. Sizes, ratios and the compression
pipeline are in **`SPEC.md` § 8** — the short version:

| Replace | Size | Notes |
|---|---|---|
| `assets/img/portrait-hero.jpg` | 720 × 900 | 4:5, eye line upper third |
| `assets/img/portrait-about.jpg` | 640 × 640 | different frame from the hero |
| `assets/img/og-card.jpg` | 1200 × 630 | the social preview — do not skip this one |
| `assets/img/work/*.jpg` | 1000 × 750 | one per project |
| `assets/img/logos/*.svg` | 24px tall | use `currentColor` so they invert in dark mode |
| `assets/img/people/*.jpg` | 160 × 160 | ask permission before publishing someone's face |
| `assets/img/speaking/*.jpg` | 400 × 400 | optional |
| `assets/img/favicon/*` | — | regenerate from your mark |

Each `.jpg` needs a matching `@2x.jpg`, `.webp` and `@2x.webp` — the `<picture>` elements
reference all four. To regenerate the WebP set after dropping in new photos:

```bash
cd assets/img
for f in $(find . -name "*.jpg" ! -name "og-card.jpg"); do
  cwebp -q 80 "$f" -o "${f%.jpg}.webp"
done
exiftool -all= -overwrite_original $(find . -name "*.jpg")   # strip EXIF, incl. GPS
```

If you'd rather not maintain WebP, delete the `<source>` lines and keep the `<img>` —
everything still works, just slightly heavier.

---

## What's implemented

- Minimal-editorial design system, all tokens in `:root` at the top of `site.css`
- Light/dark/system theming with a toggle, set pre-paint so there's no flash
- Sticky nav with scrolled state and an active-section indicator
- Scroll reveals, stat count-up, testimonial slider — all disabled under
  `prefers-reduced-motion`, and the page renders fully with JS off
- Semantic landmarks, skip link, visible focus rings, `aria-live` on the slider
- Responsive from 320px up; explicit `width`/`height` on every image
- OG/Twitter cards, JSON-LD `Person`, sitemap, robots
- CSP, HSTS and cache headers via `netlify.toml`

## Not yet done

- **Real content.** LinkedIn is login-walled, so nothing was scraped — every word is a placeholder.
- **Real photographs.**
- **Fonts.** Currently system serif + system sans, which look decent and cost 0 KB. To use
  Instrument Serif and Inter as specified: download the woff2 files, drop them in
  `assets/fonts/`, add `@font-face` blocks at the top of `site.css`, and add a
  `<link rel="preload" as="font" crossorigin>` for each in `<head>`.
- **Contact form.** Mailto only. To add one, use Netlify Forms: add `netlify` and
  `name="contact"` to a `<form>` and Netlify handles the backend on the free tier.
- **`about.html`** long-bio page — spec'd as v1.1.

## Before you call it done

- [ ] Lighthouse ≥ 95 on all four categories (DevTools → Lighthouse)
- [ ] Tab through the whole page — focus ring always visible, order sensible
- [ ] View at 320px wide with no horizontal scroll
- [ ] Toggle dark mode, check every section
- [ ] Network panel: zero 404s
- [ ] Paste the live URL into Slack or LinkedIn and confirm the OG card renders
