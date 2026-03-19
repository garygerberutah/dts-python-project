/**
 * Copyright 2026 by DTS, The State of Utah
 *
 * app-header — navigation header Web Component.
 * Provides accessible site navigation with Shadow DOM encapsulation.
 */
class AppHeader extends HTMLElement {
  #shadow;

  constructor() {
    super();
    this.#shadow = this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    this.#render();
  }

  #render() {
    const title = this.getAttribute("app-title") || "${PROJECT_NAME}";
    this.#shadow.innerHTML = `
      <style>
        :host {
          display: block;
          background: #161b22;
          border-bottom: 1px solid #30363d;
        }
        header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.75rem 1.5rem;
          max-width: 1200px;
          margin: 0 auto;
          width: 100%;
          box-sizing: border-box;
        }
        .logo {
          font-size: 1.25rem;
          font-weight: 700;
          color: #58a6ff;
          text-decoration: none;
          letter-spacing: 0.05em;
        }
        nav ul {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          gap: 1rem;
        }
        nav a {
          color: #e6edf3;
          text-decoration: none;
          font-size: 0.875rem;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          transition: background 0.15s;
        }
        nav a:hover,
        nav a:focus {
          background: #21262d;
          outline: 2px solid #58a6ff;
          outline-offset: 2px;
        }
        nav a[aria-current="page"] {
          color: #58a6ff;
          font-weight: 600;
        }
      </style>
      <header>
        <a class="logo" href="/" aria-label="${title} home">${title}</a>
        <nav aria-label="Main navigation">
          <ul role="list">
            <li><a href="/" aria-current="page">Viewer</a></li>
            <li><a href="/about">About</a></li>
            <li>
              <a
                href="${REPO_URL}"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="View source on GitHub (opens in new tab)">
                GitHub
              </a>
            </li>
          </ul>
        </nav>
      </header>
    `;
  }

  static get observedAttributes() {
    return ["app-title"];
  }

  attributeChangedCallback() {
    if (this.#shadow.innerHTML) {
      this.#render();
    }
  }
}

customElements.define("app-header", AppHeader);
export { AppHeader };
