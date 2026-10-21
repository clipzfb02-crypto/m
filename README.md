# m

A personal website, written in plain HTML, CSS and JavaScript. There's no build step, framework or dependencies.

It has:

- A hero, an About section (bio, skills, experience), a grid of selected work, and a Contact section
- Light and dark themes. It follows the visitor's system setting until they pick one with the toggle, then remembers that choice
- A responsive layout with a mobile menu
- Fade-in on scroll, turned off for visitors who prefer reduced motion
- Accessibility basics: a skip link, focus styles, semantic landmarks and contrast-checked colors

## Structure

```
index.html            All of the page content
assets/css/style.css  Styles. The colors and fonts are tokens at the top of the file
assets/js/main.js     Theme toggle, mobile menu, scroll effects, copy-email button
assets/favicon.svg    Browser tab icon
```

## Make it yours

1. **Text.** Open `index.html` and replace the placeholder content: `Your Name`, `Your City`, the bio, the job titles, the projects, the email address and the social links. Each section starts with an HTML comment that says what goes in it.
2. **Projects.** Each project is one `<article class="project">`. Its cover art is generated from the `--hue` value (0–360). To use a real screenshot, put an `<img>` inside `.project-thumb` and set its `href`.
3. **Colors and fonts.** Change the variables at the top of `assets/css/style.css`. `--accent` sets the highlight color. The dark theme's values are in the two blocks right after it.

## Preview locally

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Opening `index.html` directly in a browser also works.

## Publish it

**GitHub Pages:** go to the repo's **Settings → Pages**, set **Source** to *Deploy from a branch*, choose `main` and `/ (root)`, and save. The site will be published at `https://<username>.github.io/m/`.

Netlify, Vercel and Cloudflare Pages also work. The site is static, so you can point any of them at the repo with no build command.
