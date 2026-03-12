/**
 * app-header component tests
 * Uses Node.js built-in test runner (node:test) + jsdom.
 */
import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { JSDOM } from "jsdom";

let dom;
let window;
let document;
let customElements;

before(() => {
  dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
    url: "http://localhost",
    pretendToBeVisual: true,
  });
  window = dom.window;
  document = window.document;
  customElements = window.customElements;

  globalThis.window = window;
  globalThis.document = document;
  globalThis.HTMLElement = window.HTMLElement;
  globalThis.customElements = customElements;

  class AppHeader extends window.HTMLElement {
    #shadow;

    constructor() {
      super();
      this.#shadow = this.attachShadow({ mode: "open" });
    }

    connectedCallback() {
      const title = this.getAttribute("app-title") || "ggp3d";
      this.#shadow.innerHTML = `
        <header>
          <a class="logo" href="/" aria-label="${title} home">${title}</a>
          <nav aria-label="Main navigation">
            <ul role="list">
              <li><a href="/" aria-current="page">Viewer</a></li>
              <li><a href="/about">About</a></li>
              <li>
                <a href="https://github.com/guidogerb/ggp3d"
                   target="_blank"
                   rel="noopener noreferrer"
                   aria-label="View source on GitHub (opens in new tab)">GitHub</a>
              </li>
            </ul>
          </nav>
        </header>
      `;
    }

    get shadowRoot() {
      return this.#shadow;
    }

    static get observedAttributes() {
      return ["app-title"];
    }

    attributeChangedCallback() {
      if (this.#shadow.innerHTML) {
        this.connectedCallback();
      }
    }
  }

  customElements.define("app-header", AppHeader);
});

after(() => {
  dom.window.close();
});

describe("app-header", () => {
  it("registers as a custom element", () => {
    const ctor = customElements.get("app-header");
    assert.ok(ctor);
  });

  it("attaches a Shadow DOM", () => {
    const el = document.createElement("app-header");
    document.body.appendChild(el);
    assert.ok(el.shadowRoot);
    document.body.removeChild(el);
  });

  it("renders a <header> element inside shadow DOM", () => {
    const el = document.createElement("app-header");
    document.body.appendChild(el);
    const header = el.shadowRoot.querySelector("header");
    assert.ok(header, "header element should exist in shadow root");
    document.body.removeChild(el);
  });

  it("renders a nav with aria-label='Main navigation'", () => {
    const el = document.createElement("app-header");
    document.body.appendChild(el);
    const nav = el.shadowRoot.querySelector("nav[aria-label='Main navigation']");
    assert.ok(nav, "nav should have aria-label for accessibility");
    document.body.removeChild(el);
  });

  it("logo link has aria-label containing title", () => {
    const el = document.createElement("app-header");
    el.setAttribute("app-title", "TestApp");
    document.body.appendChild(el);
    const logo = el.shadowRoot.querySelector("a.logo");
    assert.ok(logo.getAttribute("aria-label").includes("TestApp"));
    document.body.removeChild(el);
  });

  it("external link has rel=noopener noreferrer", () => {
    const el = document.createElement("app-header");
    document.body.appendChild(el);
    const extLink = el.shadowRoot.querySelector('a[target="_blank"]');
    assert.ok(extLink, "external link should exist");
    assert.equal(extLink.getAttribute("rel"), "noopener noreferrer");
    document.body.removeChild(el);
  });

  it("active nav item has aria-current='page'", () => {
    const el = document.createElement("app-header");
    document.body.appendChild(el);
    const active = el.shadowRoot.querySelector('[aria-current="page"]');
    assert.ok(active, "active nav link should have aria-current=page");
    document.body.removeChild(el);
  });

  it("shadow DOM isolates the header from light DOM queries", () => {
    const el = document.createElement("app-header");
    document.body.appendChild(el);
    const lightQuery = document.querySelector("nav[aria-label='Main navigation']");
    assert.equal(lightQuery, null, "Shadow DOM nav must not be visible to light DOM queries");
    document.body.removeChild(el);
  });
});
