# UI

Copyright 2026 by GuidoGerb Publishing, LLC

Web application — HTML5 Web Components + Rust WebAssembly.

## Structure

```
ui/
├── scss/                   # ITCSS SCSS stylesheets
│   ├── index.scss          # Main stylesheet entry point
│   ├── 1-settings/         # Design tokens, CSS variables, color palettes
│   ├── 2-tools/            # Mixins, functions
│   ├── 3-generic/          # Reset, normalize
│   ├── 4-elements/         # Bare element styles
│   ├── 5-objects/          # Layout patterns
│   ├── 6-components/       # Component-specific styles
│   ├── 7-utilities/        # Utility classes, animations
│   ├── 8-super/            # Print styles
│   └── 9-tip/              # Tooltip styles
└── src/
    ├── main.js             # ES module entry point
    ├── components/         # Web Components (Shadow DOM, private #fields)
    │   ├── app-root.js     # Root component — loads WASM, dispatches wasm-ready
    │   ├── app-header.js   # Header component
    │   └── app-3d-viewer.js # WebGL 3D viewer component
    ├── templates/          # Jinja2 build-time templates (rendered to dist/)
    │   ├── base.html.j2    # Base layout template
    │   └── index.html.j2   # Main page template
    └── wasm/               # Rust → WASM crate (3D math engine)
        ├── Cargo.toml
        └── src/lib.rs      # Vec3, Mat4, wasm-bindgen exports
```
