/**
 * Copyright 2026 by DTS, The State of Utah
 *
 * app-root — root shell Web Component.
 * Manages application-level layout and WASM lifecycle.
 */
class AppRoot extends HTMLElement {
  #shadow;
  #wasmReady = false;

  constructor() {
    super();
    this.#shadow = this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    this.#render();
    this.#loadWasm();
  }

  #render() {
    this.#shadow.innerHTML = `
      <style>
        :host {
          display: flex;
          flex-direction: column;
          min-height: 100vh;
          font-family: system-ui, sans-serif;
          background: #0d1117;
          color: #e6edf3;
        }
        main {
          flex: 1;
          display: flex;
          flex-direction: column;
          padding: 1rem;
        }
        .status-bar {
          font-size: 0.75rem;
          padding: 0.25rem 1rem;
          background: #161b22;
          color: #8b949e;
          text-align: right;
        }
        .status-bar.ready { color: #3fb950; }
        .status-bar.error { color: #f85149; }
      </style>
      <app-header role="banner"></app-header>
      <main role="main" id="main-content">
        <app-3d-viewer aria-label="3D geometry viewer"></app-3d-viewer>
      </main>
      <div
        class="status-bar"
        role="status"
        aria-live="polite"
        id="wasm-status">
        Loading WASM engine…
      </div>
    `;
  }

  async #loadWasm() {
    const statusEl = this.#shadow.getElementById("wasm-status");
    try {
      const wasm = await import("/wasm/${WASM_MODULE}.js");
      await wasm.default();
      this.#wasmReady = true;
      this.dispatchEvent(
        new CustomEvent("wasm-ready", { bubbles: true, composed: true, detail: { wasm } })
      );
      statusEl.textContent = "WASM engine ready";
      statusEl.className = "status-bar ready";
    } catch (err) {
      statusEl.textContent = `WASM load failed: ${err.message}`;
      statusEl.className = "status-bar error";
      console.error("[app-root] WASM load error:", err);
    }
  }

  get wasmReady() {
    return this.#wasmReady;
  }
}

customElements.define("app-root", AppRoot);
export { AppRoot };
