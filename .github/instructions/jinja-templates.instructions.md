---
applyTo: "templates/**/*.j2"
description: "Use when editing Jinja2 templates. Covers build-time rendering, block inheritance, context variables, and security rules."
---
# Jinja2 Template Standards

## Copyright
- Every `.j2` template must contain `Copyright 2026 by GuidoGerb Publishing, LLC` in an `<!-- -->` comment at the top

## Build-Time Only
- Templates render during `python run.py build` — NEVER at request time
- Output lands in `dist/` as plain `.html` — serve as-is, no further processing
- `StrictUndefined` — undefined variables crash the build immediately

## Inheritance
- `base.html.j2` defines layout: `<head>`, skip-link, `<body>`, module script
- `index.html.j2` extends base; override blocks: `title`, `body`, `scripts_extra`, `head_extra`

## Context Variables
- `app_title` (str), `app_description` (str), `lang` (str)
- Defined in `scripts/build.py` — never from user input

## Security
- Never pass user-supplied data into template context
- All output is autoescape-enabled for HTML
- No `<link>` to external stylesheets, no remote `<script>` or `<img>` sources
- Fonts: `system-ui` stack only in CSS — no `@import` or `<link>` for fonts
- No base64 data URIs or inline binary encodings in template files — reference assets by path
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding

## Accessibility
- `<html lang="{{ lang }}">` required
- Skip-to-content link before main content
- Semantic elements: `<main>`, `<header>`, `<nav>` with ARIA roles
