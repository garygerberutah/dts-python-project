<!-- Copyright 2026 by DTS, The State of Utah -->

# tests/ui/ — Web Component Source-Analysis Tests

Tests that verify the structure, accessibility, and coding patterns of the
project's Web Components by parsing JavaScript source files as text. No
browser, no DOM engine, no JS runtime — pure Python string analysis via pytest.

## Components Under Test

| Component        | Tag Name          | Source File                        | Test File               |
|------------------|-------------------|------------------------------------|-------------------------|
| `AppRoot`        | `<app-root>`      | `ui/src/components/app-root.js`    | `test_app_root.py`      |
| `AppHeader`      | `<app-header>`    | `ui/src/components/app-header.js`  | `test_app_header.py`    |
| `App3dViewer`    | `<app-3d-viewer>` | `ui/src/components/app-3d-viewer.js` | `test_app_3d_viewer.py` |

## Running

```bash
pytest tests/ui/ -v              # Web Component tests only
python run.py test               # All tests (includes ui/)
```

## Fixtures (`conftest.py`)

The `tests/ui/conftest.py` provides paired fixtures for each component — one
for the raw source text and one for the extracted Shadow DOM template:

| Fixture                | Returns                                            |
|------------------------|----------------------------------------------------|
| `app_root_source`      | Full source text of `app-root.js`                  |
| `app_root_template`    | Extracted `innerHTML` template string              |
| `app_header_source`    | Full source text of `app-header.js`                |
| `app_header_template`  | Extracted template string                          |
| `app_viewer_source`    | Full source text of `app-3d-viewer.js`             |
| `app_viewer_template`  | Extracted template string                          |

Template extraction uses regex to find the `innerHTML` assignment and pull out
the template literal content between backticks.

## Test Categories

Each component test file verifies the same structural patterns, plus
component-specific accessibility and behaviour checks.

### Common Structural Tests

Every component is tested for:

- **`test_extends_html_element`** — class extends `HTMLElement`
- **`test_shadow_dom_open_mode`** — `attachShadow({ mode: "open" })`
- **`test_registers_custom_element`** — `customElements.define("tag-name", …)`
- **`test_exports_class`** — `export { ClassName }` at module level

### test_app_root.py — `<app-root>`

The root component loads WASM and dispatches the `wasm-ready` event.

| Test                             | Verifies                                        |
|----------------------------------|-------------------------------------------------|
| `test_connected_callback`        | `connectedCallback()` method present            |
| `test_template_has_main_role`    | `role="main"` on content area                   |
| `test_template_has_status_bar`   | `id="wasm-status"` element for WASM status      |
| `test_template_has_status_aria_live` | `aria-live="polite"` on status bar          |
| `test_template_has_banner_role`  | `role="banner"` on header area                  |
| `test_wasm_ready_event_dispatch` | `CustomEvent("wasm-ready")` with `bubbles` + `composed` |
| `test_wasm_init_awaits_default`  | `await wasm.default()` to load WASM module      |
| `test_wasm_error_handling`       | `catch` block for WASM load failures            |

### test_app_header.py — `<app-header>`

The header component with reactive attributes and navigation.

| Test                                       | Verifies                                |
|--------------------------------------------|-----------------------------------------|
| `test_observed_attributes`                 | `observedAttributes` includes `app-title`|
| `test_attribute_changed_callback`          | `attributeChangedCallback()` present    |
| `test_template_has_header_element`         | `<header>` semantic element             |
| `test_template_nav_has_aria_label`         | `aria-label="Main navigation"` on `<nav>` |
| `test_template_has_nav_list`               | `role="list"` on navigation list        |
| `test_template_external_link_has_noopener` | `rel="noopener noreferrer"` on external links |
| `test_template_external_link_has_target_blank` | `target="_blank"` on external links |
| `test_template_active_link_has_aria_current` | `aria-current="page"` on active link  |
| `test_template_logo_has_aria_label`        | Logo element has `aria-label`           |

### test_app_3d_viewer.py — `<app-3d-viewer>`

The 3D WebGL viewer component with WASM integration.

| Test                                         | Verifies                                 |
|----------------------------------------------|------------------------------------------|
| `test_template_canvas_has_aria_label`        | `<canvas>` has `aria-label`              |
| `test_template_canvas_has_role_img`          | `role="img"` on canvas                   |
| `test_template_canvas_has_fallback_text`     | Browser support fallback text            |
| `test_template_info_panel_has_region_role`   | `role="region"` on info panel            |
| `test_template_info_panel_has_aria_label`    | `aria-label="3D scene information"`      |
| `test_template_rotation_element`             | `id="rotation-val"` display element      |
| `test_template_vertex_count_element`         | `id="vertex-count"` display element      |
| `test_wasm_ready_listener`                   | `addEventListener("wasm-ready")`         |
| `test_wasm_event_once`                       | `{ once: true }` option on listener      |
| `test_disconnected_callback`                 | `disconnectedCallback()` for cleanup     |
| `test_webgl_fallback`                        | 2D canvas fallback when WebGL unavailable|

## What These Tests Do NOT Cover

- **Private `#fields`** — inaccessible from outside the class; tested indirectly
  through source pattern matching.
- **Runtime rendering** — no DOM engine is available; template HTML is parsed as
  text only.
- **WebGL output** — no GPU in the test environment; shader and render logic is
  not tested.
- **User interaction** — click handlers and event propagation require a browser.

## Adding a New Component Test

1. Add the component's source fixture to `tests/ui/conftest.py`.
2. Create `tests/ui/test_<component_name>.py`.
3. Start with the four structural tests (extends, shadow DOM, define, export).
4. Extract the template and test ARIA attributes, roles, and labels.
5. Grep the source for event patterns, WASM integration, and lifecycle hooks.
