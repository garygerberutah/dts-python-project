---
applyTo: "frontend/components/**/*.js"
description: "Use when creating or editing Web Components. Covers Shadow DOM, private fields, event dispatch, WASM integration, and accessibility patterns."
---
# Web Component Standards

## Copyright
- Every JS file must contain `Copyright 2026 by GuidoGerb Publishing, LLC` in a comment at the top

## Structure
- Extend `HTMLElement`, attach Shadow DOM `mode: "open"` in constructor
- Private state via `#fields`, private logic via `#methods()`
- Render HTML in `connectedCallback()` via `this.#shadow.innerHTML`

## Events
- `new CustomEvent(name, { bubbles: true, composed: true, detail })` to cross shadow boundaries
- Listen with `{ once: true }` when expecting a single fire (e.g., `wasm-ready`)

## WASM Integration
- Only `app-root` loads WASM; children listen for `wasm-ready` on `window`
- Always `await wasm.default()` before using exports

## Accessibility
- Every interactive element needs `role` and `aria-label`
- Canvas elements need `role="img"`, `aria-label`, and fallback text content
- Navigation needs `aria-label="Main navigation"` and `aria-current="page"` on active links
- Status regions need `role="status"` and `aria-live="polite"`

## Forbidden
- No `document.querySelector()` to reach shadow children — use `shadowRoot.querySelector()`
- No `var`, no `==`, no `console.log` (use `info`/`warn`/`error`)
- No external resources — no CDN, no remote fonts/CSS/JS
- No 3rd-party imports — vanilla ES modules only
- No base64 data URIs or inline binary encodings in source files — reference assets by path
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding
- `application/octet-stream` and unidentifiable binary data are forbidden in git
