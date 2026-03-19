"""Tests for the app-root Web Component (source analysis).

Copyright 2026 by DTS, The State of Utah
"""


def test_extends_html_element(app_root_source):
    assert "extends HTMLElement" in app_root_source


def test_shadow_dom_open_mode(app_root_source):
    assert 'attachShadow({ mode: "open" })' in app_root_source


def test_registers_custom_element(app_root_source):
    assert 'customElements.define("app-root"' in app_root_source


def test_exports_class(app_root_source):
    assert "export { AppRoot }" in app_root_source


def test_connected_callback(app_root_source):
    assert "connectedCallback()" in app_root_source


def test_template_has_main_role(app_root_template):
    assert 'role="main"' in app_root_template


def test_template_has_status_bar(app_root_template):
    assert 'id="wasm-status"' in app_root_template


def test_template_has_status_aria_live(app_root_template):
    assert 'aria-live="polite"' in app_root_template


def test_template_has_banner_role(app_root_template):
    assert 'role="banner"' in app_root_template


def test_wasm_ready_event_dispatch(app_root_source):
    assert 'new CustomEvent("wasm-ready"' in app_root_source
    assert "bubbles: true" in app_root_source
    assert "composed: true" in app_root_source


def test_wasm_init_awaits_default(app_root_source):
    assert "await wasm.default()" in app_root_source


def test_wasm_error_handling(app_root_source):
    assert "catch" in app_root_source
