# UI

Copyright 2026 by GuidoGerb Publishing, LLC

Web application — HTML5 Web Components + Rust WebAssembly.

## Structure

```
ui/
├── scss/           # ITCSS SCSS stylesheets
├── config/         # UI configuration
├── util/           # Utility modules
└── src/
    ├── templates/  # Jinja2 build-time templates
    ├── static/     # Static assets
    ├── auth/       # Authentication (OIDC+PKCE)
    ├── menus/      # Menu components
    ├── routes/     # Route definitions
    ├── pages/      # Page components
    ├── components/ # Web Components
    ├── wasm/       # Rust → WASM crate
    └── main.js     # ES module entry point
```
