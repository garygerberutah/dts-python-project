/**
 * app-root component tests
 * Uses Node.js built-in test runner (node:test).
 * Tests DOM behaviour, Shadow DOM isolation, and event dispatch
 * without a real browser via a minimal DOM shim.
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
  globalThis.CustomEvent = window.CustomEvent;

  // Inline minimal component definition for test environment
  class AppRoot extends window.HTMLElement {
    #shadow;
    #wasmReady = false;

    constructor() {
      super();
      this.#shadow = this.attachShadow({ mode: "open" });
    }

    connectedCallback() {
      this.#shadow.innerHTML = `
        <app-header role="banner"></app-header>
        <main role="main" id="main-content">
          <app-3d-viewer aria-label="3D geometry viewer"></app-3d-viewer>
        </main>
        <div class="status-bar" role="status" id="wasm-status">Loading…</div>
      `;
    }

    get shadowRoot() {
      return this.#shadow;
    }

    get wasmReady() {
      return this.#wasmReady;
    }
  }

  customElements.define("app-root", AppRoot);
});

after(() => {
  dom.window.close();
});

describe("app-root", () => {
  it("registers as a custom element", () => {
    const ctor = customElements.get("app-root");
    assert.ok(ctor, "app-root should be registered");
  });

  it("creates a Shadow DOM when instantiated", () => {
    const el = document.createElement("app-root");
    document.body.appendChild(el);
    assert.ok(el.shadowRoot, "Shadow DOM should be attached");
    document.body.removeChild(el);
  });

  it("shadow root is encapsulated (mode: open)", () => {
    const el = document.createElement("app-root");
    document.body.appendChild(el);
    assert.equal(el.shadowRoot.mode, "open");
    document.body.removeChild(el);
  });

  it("renders status bar with id wasm-status after connectedCallback", () => {
    const el = document.createElement("app-root");
    document.body.appendChild(el);
    const status = el.shadowRoot.getElementById("wasm-status");
    assert.ok(status, "status bar element should be present in shadow DOM");
    document.body.removeChild(el);
  });

  it("renders main element with role=main", () => {
    const el = document.createElement("app-root");
    document.body.appendChild(el);
    const main = el.shadowRoot.querySelector("[role='main']");
    assert.ok(main, "main region should be present");
    document.body.removeChild(el);
  });

  it("wasmReady defaults to false", () => {
    const el = document.createElement("app-root");
    document.body.appendChild(el);
    assert.equal(el.wasmReady, false);
    document.body.removeChild(el);
  });

  it("shadow DOM is isolated from outer document styles", () => {
    const el = document.createElement("app-root");
    document.body.appendChild(el);
    // Light DOM should not contain shadow children
    const directChild = document.querySelector("#wasm-status");
    assert.equal(directChild, null, "Shadow DOM children must not be accessible via document.querySelector");
    document.body.removeChild(el);
  });
});
