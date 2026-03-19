"""Tests for the app-3d-viewer Web Component (source analysis).

Copyright 2026 by DTS, The State of Utah
"""

import re


def test_extends_html_element(app_viewer_source):
    assert "extends HTMLElement" in app_viewer_source


def test_shadow_dom_open_mode(app_viewer_source):
    assert 'attachShadow({ mode: "open" })' in app_viewer_source


def test_registers_custom_element(app_viewer_source):
    assert 'customElements.define("app-3d-viewer"' in app_viewer_source


def test_exports_class(app_viewer_source):
    assert "export { App3dViewer }" in app_viewer_source


def test_template_canvas_has_aria_label(app_viewer_template):
    assert re.search(r"<canvas[^>]*aria-label=", app_viewer_template)


def test_template_canvas_has_role_img(app_viewer_template):
    assert re.search(r'<canvas[^>]*role="img"', app_viewer_template)


def test_template_canvas_has_fallback_text(app_viewer_template):
    assert "Your browser does not support" in app_viewer_template


def test_template_info_panel_has_region_role(app_viewer_template):
    assert 'role="region"' in app_viewer_template


def test_template_info_panel_has_aria_label(app_viewer_template):
    assert 'aria-label="3D scene information"' in app_viewer_template


def test_template_rotation_element(app_viewer_template):
    assert 'id="rotation-val"' in app_viewer_template


def test_template_vertex_count_element(app_viewer_template):
    assert 'id="vertex-count"' in app_viewer_template


def test_wasm_ready_listener(app_viewer_source):
    assert 'addEventListener("wasm-ready"' in app_viewer_source or \
           "addEventListener('wasm-ready'" in app_viewer_source


def test_wasm_event_once(app_viewer_source):
    assert "once: true" in app_viewer_source


def test_disconnected_callback(app_viewer_source):
    assert "disconnectedCallback()" in app_viewer_source


def test_webgl_fallback(app_viewer_source):
    assert "draw2dFallback" in app_viewer_source or "2d" in app_viewer_source
