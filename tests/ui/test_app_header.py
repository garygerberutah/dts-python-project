"""Tests for the app-header Web Component (source analysis).

Copyright 2026 by DTS, The State of Utah
"""


def test_extends_html_element(app_header_source):
    assert "extends HTMLElement" in app_header_source


def test_shadow_dom_open_mode(app_header_source):
    assert 'attachShadow({ mode: "open" })' in app_header_source


def test_registers_custom_element(app_header_source):
    assert 'customElements.define("app-header"' in app_header_source


def test_exports_class(app_header_source):
    assert "export { AppHeader }" in app_header_source


def test_observed_attributes(app_header_source):
    assert "observedAttributes" in app_header_source
    assert '"app-title"' in app_header_source


def test_attribute_changed_callback(app_header_source):
    assert "attributeChangedCallback" in app_header_source


def test_template_has_header_element(app_header_template):
    assert "<header" in app_header_template


def test_template_nav_has_aria_label(app_header_template):
    assert 'aria-label="Main navigation"' in app_header_template


def test_template_has_nav_list(app_header_template):
    assert 'role="list"' in app_header_template


def test_template_external_link_has_noopener(app_header_template):
    assert "noopener noreferrer" in app_header_template


def test_template_external_link_has_target_blank(app_header_template):
    assert 'target="_blank"' in app_header_template


def test_template_active_link_has_aria_current(app_header_template):
    assert 'aria-current="page"' in app_header_template


def test_template_logo_has_aria_label(app_header_template):
    assert "aria-label=" in app_header_template
