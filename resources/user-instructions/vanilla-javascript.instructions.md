---
applyTo: "**/*.js"
description: "Use when writing or editing JavaScript. Enforces vanilla ES6+ modules, zero frameworks, browser-native APIs, and strict coding rules."
---
# JavaScript Standards

## Core Principle
Vanilla ES6+ modules only — zero framework dependencies, zero 3rd-party libraries.

## Module Pattern
- ES modules with `import`/`export` — no CommonJS, no AMD, no bundlers
- One class or concern per file
- kebab-case filenames (`app-3d-viewer.js`)

## Language Rules
- `===` not `==`, `!==` not `!=`
- `const` by default, `let` when reassignment needed, never `var`
- No `console.log` — use `console.info`, `console.warn`, `console.error`
- Arrow functions for callbacks, named functions for declarations
- Destructuring for object/array access where it improves clarity
- Template literals over string concatenation

## Browser APIs Only
- DOM: standard `querySelector`, `createElement`, `addEventListener`
- Web Components: `HTMLElement`, Shadow DOM, `CustomEvent`
- Fetch API for HTTP — no axios, no jQuery.ajax
- No polyfills, no shims, no compatibility layers

## Forbidden
- No npm packages in application code
- No transpilation (Babel, TypeScript compiler)
- No bundlers (Webpack, Vite, esbuild, Rollup)
- No external CDN scripts, fonts, or stylesheets
- No base64 data URIs or inline binary encodings in JS source files — reference assets by path
- Binary assets (`.png`, `.jpg`, `.svg`, etc.) may be versioned if they match their mime-type encoding
- `application/octet-stream` and opaque binary blobs are forbidden in git
