---
applyTo: "**/*.scss"
description: "Use when writing or editing SCSS files. Covers ITCSS architecture, libsass compilation, layer ordering, and naming conventions."
---
# SCSS / ITCSS Standards

## Architecture (ITCSS — Inverted Triangle CSS)
Layers ordered from broadest reach to most specific:

1. **Settings** — variables, config (`_settings.colors.scss`, `_settings.typography.scss`)
2. **Tools** — mixins, functions (`_tools.mixins.scss`, `_tools.responsive.scss`)
3. **Generic** — resets, normalize (`_generic.reset.scss`, `_generic.box-sizing.scss`)
4. **Elements** — bare HTML element styles (`_elements.page.scss`, `_elements.headings.scss`)
5. **Objects** — layout patterns, no cosmetics (`_objects.grid.scss`, `_objects.media.scss`)
6. **Components** — styled UI components (`_components.button.scss`, `_components.card.scss`)
7. **Utilities** — overrides, helpers (`_utilities.sr-only.scss`, `_utilities.spacing.scss`)

## Conventions
- One partial per concern: `_<layer>.<name>.scss`
- Main manifest imports layers in ITCSS order
- BEM naming: `.block__element--modifier`
- Variables: `$<category>-<name>` (e.g., `$color-primary`, `$spacing-md`)
- Compile with libsass — no dart-sass, no postcss, no autoprefixer

## Forbidden
- No `@use` / `@forward` (libsass uses `@import`)
- No nesting deeper than 3 levels
- No `!important` outside Utilities layer
- No external font imports — `system-ui` stack or self-hosted only
- No CSS frameworks (Bootstrap, Tailwind)
- No base64 data URIs or inline binary encodings in SCSS files — use `url()` with asset file paths
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding
- `application/octet-stream` and opaque binary blobs are forbidden in git
