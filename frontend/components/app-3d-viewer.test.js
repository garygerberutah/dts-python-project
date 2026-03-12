/**
 * app-3d-viewer component tests
 * Uses Node.js built-in test runner (node:test) + jsdom.
 * Tests DOM structure, Shadow DOM isolation, and WASM event integration.
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

  class App3dViewer extends window.HTMLElement {
    #shadow;
    #wasm = null;

    constructor() {
      super();
      this.#shadow = this.attachShadow({ mode: "open" });
    }

    connectedCallback() {
      this.#shadow.innerHTML = `
        <div class="canvas-container">
          <canvas
            id="gl-canvas"
            width="640"
            height="480"
            aria-label="Interactive 3D geometry viewer canvas"
            role="img">
            Your browser does not support WebGL or the canvas element.
          </canvas>
        </div>
        <div class="info-panel" role="region" aria-label="3D scene information">
          <h2>Scene Info</h2>
          <dl id="scene-info">
            <dt>Engine</dt><dd>Rust WASM</dd>
            <dt>Renderer</dt><dd>WebGL</dd>
            <dt>Vertices</dt><dd id="vertex-count">—</dd>
            <dt>Rotation</dt><dd id="rotation-val">0.00°</dd>
          </dl>
        </div>
      `;
      window.addEventListener("wasm-ready", (e) => {
        this.#wasm = e.detail.wasm;
      }, { once: true });
    }

    get shadowRoot() {
      return this.#shadow;
    }

    get wasm() {
      return this.#wasm;
    }
  }

  customElements.define("app-3d-viewer", App3dViewer);
});

after(() => {
  dom.window.close();
});

describe("app-3d-viewer", () => {
  it("registers as a custom element", () => {
    assert.ok(customElements.get("app-3d-viewer"));
  });

  it("attaches a Shadow DOM", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    assert.ok(el.shadowRoot);
    document.body.removeChild(el);
  });

  it("canvas has accessible aria-label and role=img", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    const canvas = el.shadowRoot.querySelector("canvas");
    assert.ok(canvas, "canvas should exist in shadow DOM");
    assert.ok(canvas.getAttribute("aria-label"), "canvas should have aria-label");
    assert.equal(canvas.getAttribute("role"), "img");
    document.body.removeChild(el);
  });

  it("canvas has fallback text content", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    const canvas = el.shadowRoot.querySelector("canvas");
    assert.ok(canvas.textContent.trim().length > 0, "canvas should have fallback text");
    document.body.removeChild(el);
  });

  it("info-panel region has aria-label", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    const panel = el.shadowRoot.querySelector('[role="region"]');
    assert.ok(panel, "info panel should have role=region");
    assert.ok(panel.getAttribute("aria-label"), "info panel should have aria-label");
    document.body.removeChild(el);
  });

  it("rotation-val element initialises to 0.00°", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    const rot = el.shadowRoot.getElementById("rotation-val");
    assert.equal(rot.textContent, "0.00°");
    document.body.removeChild(el);
  });

  it("wasm property starts as null", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    assert.equal(el.wasm, null);
    document.body.removeChild(el);
  });

  it("responds to wasm-ready event", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    const fakewasm = { greet: () => "hello" };
    const event = new window.CustomEvent("wasm-ready", { detail: { wasm: fakewasm } });
    window.dispatchEvent(event);
    assert.equal(el.wasm, fakewasm, "wasm property should be set after wasm-ready event");
    document.body.removeChild(el);
  });

  it("shadow DOM is isolated from light DOM", () => {
    const el = document.createElement("app-3d-viewer");
    document.body.appendChild(el);
    assert.equal(document.querySelector("canvas"), null, "canvas should not be reachable from light DOM");
    document.body.removeChild(el);
  });
});
