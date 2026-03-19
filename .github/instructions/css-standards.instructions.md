---
applyTo: "ui/scss/**/*.css"
description: "Use when editing global CSS. Covers CSS variable scoping, Shadow DOM inheritance, system fonts, and self-contained resource rules."
---
# CSS Standards

## Copyright
- Every `.css` file must contain `Copyright 2026 by DTS, The State of Utah` in a `/* */` comment at the top

## Global Styles (main.css)
- Minimal reset + CSS custom properties on `:root`
- `color-scheme: dark` for native dark mode
- `font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif`
- Accessibility utilities: `.skip-link`, `.sr-only`

## Shadow DOM Scoping
- `:root` variables do NOT inherit into Shadow DOM unless explicitly used
- Component styles live inside `<style>` blocks within each component's shadow root
- Global CSS only handles body-level reset and shared variables

## Forbidden
- No `@import` for remote resources
- No `url()` pointing to external domains
- No downloaded fonts — `system-ui` stack only
- No CSS frameworks (Bootstrap, Tailwind, etc.)
- No CSS preprocessors (Sass, Less, PostCSS) — hand-written CSS only
- No base64 data URIs or inline binary encodings in CSS files — use `url()` with asset file paths
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding
