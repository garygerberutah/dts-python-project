**State of Utah \- Division of Technology Services (DTS)**

**AI Security & Software Strategy Document**

**Status:** DRAFT / Active Collaboration

**Audience:** State of Utah Developers & Engineering Leadership

Author: Gary Gerber \- [ggerber@utah.gov](mailto:ggerber@utah.gov)
Mar 19, 2026

**1\. Executive Summary: AI Safety in Government Systems**

As the State of Utah accelerates its adoption of AI-assisted development tools (e.g., GitHub Copilot, ChatGPT), the risk of introducing vulnerabilities, hallucinated dependencies, and non-compliant code into government systems increases exponentially. Government applications handle sensitive citizen data and critical infrastructure operations, making supply chain security and code provenance paramount.

This repository (https://github.com/garygerberutah/dts-python-project) framework presents a robust, paranoid, and highly deterministic strategy to minimize these risks. By enforcing rigid guardrails, establishing a **zero-dependency** philosophy implementing well established HTML5, pure javascript, web components with direct browser api calls and maintaining an immutable blockchain-based Software Bill of Materials (SBOM).  This architecture ensures that all code—whether authored by a human or an AI—is mathematically verified, audited, and strictly compliant before it can ever reach production.

### **2\. Architectural Strategies & Risk Minimization**

The overarching architecture significantly reduces the attack surface typically exploited by AI hallucinations or supply chain attacks.

* **Zero-Dependency Web Ecosystem:** The repository entirely eliminates Node.js, npm, and heavy JavaScript build tools. By relying on native HTML5 Web Components, vanilla JavaScript, and native browser performant Rust-compiled WebAssembly WASM (if needed), it removes the risk of an AI agent hallucinating or importing malicious, deep-tree dependencies (the "node\_modules" problem).
* **Isolated Toolchain:** Build and deployment scripts are managed purely via Python, ensuring that the toolchain is strictly separated from the application runtime. Jinja2 templates are used for build-time rendering only and are never served at runtime, closing off entire classes of injection vulnerabilities.
* **Memory-Safe Computation:** By offloading any computational heavy logic to Rust (via wasm-bindgen), the system leverages Rust's strict memory safety guarantees. AI-generated Rust code is forced to comply with the borrow checker, neutralizing memory-leak and buffer-overflow risks before the code can compile.

### **3\. Guardrails, Instructions, and Rules**

To prevent AI-generated flaws from infiltrating the codebase, the framework implements a highly restrictive "fail-fast" pipeline.

* **Strict Pre-Commit Enforcement:** The framework uses the pre-commit tool to run the entire master pipeline locally before a commit can be created. Crucially, the \--no-verify flag is strictly forbidden. This ensures AI-generated code cannot even be committed to local version control without passing all tests.
* **Exhaustive Validation Layers:** The master pipeline enforces a rigorous 12-step validation process. A failure at any step immediately aborts the pipeline.
    * **Static Analysis & Linting:** Enforces auto-formatting (rustfmt, ruff) and strict linting (cargo clippy with \-D warnings, ruff check). This prevents an AI from introducing non-standard or deprecated syntaxes.
    * **Asset & Mime-Type Validation:** Binary files must match their declared mime-type, and assets are validated against naming conventions and SHA-256 hashes. This prevents AI tools from silently corrupting binaries or embedding malicious payloads disguised as standard web assets.
    * **Automated Accessibility (WCAG 2.1 Level AA):** Government systems must be accessible to all citizens. The pipeline statically analyzes compiled HTML to ensure AI-generated UIs do not violate federal and state accessibility laws.
* **Static Component Testing:** Web components are tested via Python (pytest) using source-analysis rather than a full browser DOM engine. This limits the testing environment's exposure and speeds up the validation loop, quickly catching AI-generated logic errors.

### **4\. Audit Trails & Blockchain SBOM Histories**

In government systems, knowing *what* is in a build and *who* (or what) put it there is just as critical as the code itself.

* **Cryptographic Provenance:** The build pipeline includes an automated SBOM generator that creates a SHA-256 manifest of the entire project state.
* **Local Blockchain Integration:** To ensure immutability, this manifest is appended to a local blockchain via a proof-of-work mechanism (chain.json). This ensures that if AI-generated code introduces a vulnerability, the exact state of the repository at the time of integration is permanently frozen and cryptographically verifiable.
* **PostgreSQL Storage:** The blockchain data is mirrored to a PostgreSQL database (sbom\_version table), allowing state security auditors to query the history of the repository and track the lineage of every deployed file.

**5\. Identified Weaknesses & Path to Improvement**

While the evaluated repository establishes an exceptionally strong foundation for AI safety, several weaknesses exist in its current implementation that require ongoing remediation.

#### **Weakness 1: Localized Blockchain Vulnerability**

**Issue:** The blockchain SBOM relies on a local implementation (chain.json and a local PostgreSQL DB). If a developer's machine or the CI server is compromised by an advanced AI-generated payload, the local blockchain history could theoretically be rewritten or dropped before synchronization.

**Path to Improvement:**

* **Auditing Pathway:** Transition the proof-of-work blockchain ledger from a localized file to a centralized, state-controlled immutable ledger (e.g., an enterprise blockchain or an append-only AWS Quantum Ledger Database).
* **Ongoing Effort:** Develop a cryptographic signing step where commits and SBOM blocks are signed by the developer’s hardware key (YubiKey) and countersigned by the State of Utah's centralized PKI infrastructure before deployment.

#### **Weakness 2: Custom Python-Based JavaScript Linting**

**Issue:** The architecture uses a custom Python script (lint\_js.py) to lint JavaScript (checking for eqeqeq, no-var, etc.). While this avoids Node.js dependencies, basic string-matching linters lack Abstract Syntax Tree (AST) awareness. An AI model could easily generate obfuscated or functionally insecure JavaScript that bypasses these simple regex-style checks.

**Path to Improvement:**

* **Auditing Pathway:** Implement a robust AST-parsing mechanism written in Python or Rust (e.g., using a Rust-based JS parser like SWC integrated via WASM) to accurately analyze the semantic structure of AI-generated JavaScript.
* **Ongoing Effort:** Expand the custom linter to detect AI-specific coding hallucinations, such as dangling promise chains or DOM-clobbering vulnerabilities, without compromising the zero-dependency rule.

#### **Weakness 3: Single Point of Failure in Pre-Commit Dependency**

**Issue:** The local guardrails rely entirely on developers keeping the pre-commit hooks installed. An AI agent running a script, or a developer rushing a patch, could bypass local hooks by altering the .git/hooks directory directly.

**Path to Improvement:**

* **Auditing Pathway:** Shift the ultimate source of truth to the GitHub Actions CI/CD pipeline. Ensure that branch protection rules strictly require the pipeline to succeed on the remote server, regardless of local bypasses.
* **Ongoing Effort:** Implement automated audits of branch protection rules via state-wide infrastructure-as-code (IaC) to ensure no developer or AI tool can grant administrative overrides to the dev or main branches.

**Editorial Note:**

***It is all on us**\!*

Moving away from frameworks like React is a critical effort \- the State of Utah agencies must not, it can not delegate security to the immense developer pools in the ‘colossal stacks of third party libraries’ that produce popular frameworks.  AI coding safety will open up a wonderful, productive future.  While we are involving AIs to reverse engineer complex frameworks,  we gracefully accept our responsibility (and will always) to produce safe and performant software that serves the great State of Utah.  Breaking complexity into small modular views must be paramount.  It can reduce the stress of a quickly changing world and restore an enjoyable and creative experience, if framed within this type of enforceable safety pipeline. Outside of restrictive technology IP and industry secrecy,  the roles of developers will continue to move away from writing code towards managing project scope, reviewing the AI generated features and tests.  As developers, we are shifting towards becoming full time reviewers and managers of increasingly powerful tools.  We have a new coding partner that requires our constant effort, both to contain and control \- ***AI***.

**Zero-dependency 3D geometry processor** — native HTML5 Web Components + Rust WebAssembly.
**Python-only toolchain** — no Node.js, npm, or any JS build tools.

## Architecture

| Layer | Technology |
|---|---|
| UI | HTML5 Web Components (Shadow DOM), vanilla JS — **zero runtime dependencies** |
| Rendering | WebGL via vanilla JS |
| Math engine | Rust → WASM via wasm-bindgen (`ggp3d-wasm` crate) |
| Styles | SCSS (ITCSS architecture) + Shadow DOM `<style>` blocks |
| Templates | Jinja2 (build-time rendering only — never served at runtime) |
| Toolchain | Python scripts (`run.py`) — no Node.js |
| Tests | pytest (source-analysis, no browser or DOM engine) |
| SBOM | SHA-256 manifests + local blockchain + PostgreSQL |
| CI/CD | GitHub Actions → AWS S3 + CloudFront |

## Quick Start

### Prerequisites

| Tool | Version |
|---|---|
| Python | ≥ 3.12 |
| Rust (stable) | ≥ 1.75 |
| wasm-pack | latest |
| PostgreSQL | ≥ 14 *(optional, for SBOM storage)* |

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Rust toolchain (Linux / WSL2)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Add WASM compile target and install wasm-pack
rustup target add wasm32-unknown-unknown
cargo install wasm-pack

# Configure git hooks (run once after clone)
python run.py setup
```

---

## Toolchain Commands

All commands are driven by a single entry point:

```bash
python run.py <command> [options]
```

| Command | Description |
|---|---|
| `setup` | Configure git hooks via pre-commit (run once after clone) |
| `clean` | Remove `dist/` and `wasm/pkg/` |
| `build` | Compile WASM → render Jinja2 templates → copy assets to `dist/` |
| `serve [port]` | Serve `dist/` locally (default port 8080) |
| `format` | Auto-format Rust (rustfmt), Python (ruff) |
| `lint` | Static analysis — Python JS linter, cargo clippy, ruff check |
| `validate` | WCAG 2.1 compliance check on compiled HTML |
| `validate-copyright` | Verify copyright notices in all source files (`--fix` to auto-repair) |
| `validate-mime` | Verify binary files match their declared mime-type encoding |
| `test` | Run all component test suites (pytest) |
| `sbom` | Generate SBOM manifest + append to local blockchain |
| `sbom-db` | Create/verify the PostgreSQL `sbom_version` table |
| `pipeline` | Full automation: test → format → lint → validate → clean → build → validate → test → sbom → deploy |
| `pipeline --skip-deploy` | As above but skip the git commit/push stage |

---

## Master Pipeline

```bash
python run.py pipeline --skip-deploy
```

Stages (fail-fast — first failure aborts all subsequent stages):

1. **Test** — pytest on `tests/`
2. **Format** — auto-format Rust (rustfmt), Python (ruff)
3. **Lint** — Python JS linter, cargo clippy (`-D warnings`), ruff check
4. **Validate (copyright)** — copyright notices in all source files
5. **Validate (assets)** — asset naming conventions + SHA-256 hashing
6. **Validate (mime-type)** — binary files match their declared mime-type
7. **Clean** — purge prior build artefacts
8. **Build** — compile WASM, render Jinja2 templates, copy assets to `dist/`
9. **Validate (WCAG 2.1)** — Level AA accessibility checks on rendered HTML
10. **Test (components)** — pytest Web Component source-analysis suites
11. **SBOM** — generate manifest, mine blockchain block, store in PostgreSQL
12. **Deploy** — `git commit` + `git push` *(gated behind 100% success)*

---

## Project Structure

```
ggp-python-project/
├── run.py                          # Single CLI entry point
├── requirements.txt                # Python deps (jinja2, pytest, ruff, pre-commit, psycopg2)
├── COPYRIGHT                       # Copyright notice (included in every source file)
├── LICENSE                         # Apache License 2.0
│
├── ui/                             # Application source (ships to dist/)
│   ├── src/
│   │   ├── main.js                 # ES module entry point — imports all Web Components
│   │   ├── components/
│   │   │   ├── app-root.js         # Root shell — loads WASM, dispatches wasm-ready
│   │   │   ├── app-header.js       # Navigation header (Shadow DOM, app-title attr)
│   │   │   └── app-3d-viewer.js    # WebGL 3D canvas (listens for wasm-ready)
│   │   ├── templates/
│   │   │   ├── base.html.j2        # Base template (blocks: title, body, scripts_extra)
│   │   │   └── index.html.j2       # Main page (extends base, renders <app-root>)
│   │   └── wasm/
│   │       ├── Cargo.toml          # ggp3d-wasm crate (cdylib, opt-level="z", LTO)
│   │       ├── src/lib.rs          # Vec3: new, length, normalize, dot, cross, add
│   │       └── pkg/                # Auto-generated by wasm-pack (JS + .wasm bindings)
│   └── scss/                       # ITCSS architecture
│       ├── index.scss              # Master import file
│       ├── 1-settings/             # Variables, tokens, colors, fonts, grid, spacing
│       ├── 2-tools/                # Mixins, functions
│       ├── 3-generic/              # CSS resets
│       ├── 4-elements/             # Base HTML element styles
│       ├── 5-objects/              # Layout patterns (grid, flex)
│       ├── 6-components/           # Component styles (BEM naming)
│       ├── 7-utilities/            # Utility classes
│       ├── 8-super/                # High-specificity overrides
│       └── 9-tip/                  # Last-resort hacks
│
├── scripts/                        # Python toolchain (never ships)
│   ├── build_all.py                # Master pipeline orchestrator
│   ├── ui/
│   │   ├── build.py                # WASM compile + Jinja2 render + asset copy
│   │   ├── clean.py                # Remove dist/ and wasm/pkg/
│   │   ├── format_code.py          # rustfmt + ruff format
│   │   ├── lint.py                 # ruff check + cargo clippy
│   │   ├── lint_js.py              # Python-based JS linter (eqeqeq, no-var, no-console.log)
│   │   ├── serve.py                # Local HTTP dev server
│   │   ├── test_components.py      # pytest runner
│   │   ├── validate_wcag.py        # WCAG 2.1 Level AA checker
│   │   ├── validate_copyright.py   # Copyright notice enforcer
│   │   ├── validate_assets.py      # Asset naming + SHA-256 validation
│   │   ├── validate_mime_type_content.py  # Mime-type content validation
│   │   └── name_mime_type.py       # Mime-type detection utility
│   ├── blockchain/
│   │   ├── generate_sbom.py        # SHA-256 manifest generator
│   │   ├── sbom.py                 # Local blockchain (proof-of-work, chain.json)
│   │   └── db.py                   # PostgreSQL SBOM storage
│   └── util/                       # Developer utilities
│
├── tests/                          # pytest test suites
│   ├── conftest.py                 # Global test fixtures
│   ├── test_all.py                 # Master test orchestrator
│   ├── test_format.py              # Format validation tests
│   ├── test_lint.py                # Lint validation tests
│   ├── test_validate_copyright.py  # Copyright notice tests
│   ├── test_validate_mime_type_content.py  # Mime-type tests
│   ├── test_validate_wcag.py       # WCAG accessibility tests
│   ├── test_validate_assets.py     # Asset validation tests
│   └── ui/                         # Web Component source-analysis tests
│       ├── conftest.py             # Component fixtures (source parsing)
│       ├── test_app_root.py
│       ├── test_app_header.py
│       └── test_app_3d_viewer.py
│
├── resources/                      # Project configuration & references
│   ├── config/
│   │   ├── ruff.toml               # Ruff linter/formatter config
│   │   └── site.json               # Project metadata
│   └── ...
│
├── api/                            # RESTful API (Lambda handlers)
│
└── .github/
    ├── copilot-instructions.md     # Project rules & conventions
    ├── instructions/               # Domain-specific coding standards
    └── workflows/
        ├── ci.yml                  # CI: Rust tests, lint, WCAG, pytest
        └── deploy-dev.yml          # Deploy: build → S3 + CloudFront
```

---

## SCSS (ITCSS Architecture)

Styles follow the **Inverted Triangle CSS** methodology with BEM naming:

| Layer | Directory | Purpose |
|---|---|---|
| Settings | `1-settings/` | Design tokens, colors, fonts, grid, spacing, breakpoints |
| Tools | `2-tools/` | Mixins, functions |
| Generic | `3-generic/` | CSS resets, normalize |
| Elements | `4-elements/` | Bare HTML element styles |
| Objects | `5-objects/` | Layout patterns (grid, flex containers) |
| Components | `6-components/` | Styled UI components (BEM: `block__element--modifier`) |
| Utilities | `7-utilities/` | Single-purpose utility classes |
| Super | `8-super/` | High-specificity overrides |
| Tip | `9-tip/` | Last-resort hacks (use sparingly) |

Component styles live inside Shadow DOM `<style>` blocks. Global CSS provides only a minimal reset + CSS custom properties.

---

## SBOM & Blockchain Auditing

Each pipeline run generates a Software Bill of Materials:

1. **Manifest** — walks all git-tracked files, computes SHA-256 hashes → `sbom.json`
2. **Blockchain** — mines a new block with proof-of-work, appends to `chain.json`
3. **Database** — stores the full manifest in PostgreSQL (`public.sbom_version`)

```bash
python run.py sbom       # Generate manifest + mine block
python run.py sbom-db    # Create/verify the PostgreSQL table
```

---

## AWS Deployment

The `deploy-dev.yml` workflow triggers on every push to the `dev` branch.

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_DEFAULT_REGION` | e.g. `us-east-1` |
| `AWS_S3_BUCKET_DEV` | Target S3 bucket name |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID_DEV` | CloudFront distribution ID |

---

## Testing

### Rust (native)

```bash
cd ui/src/wasm && cargo test
```

### Web Components (pytest source-analysis)

```bash
python run.py test
# or directly:
pytest tests/ -v
```

Tests parse component JS source files statically — no browser, no DOM engine, no JS runtime needed.

### WCAG Validation (after build)

```bash
python run.py validate
```

### All Validations

```bash
python run.py validate-copyright    # Copyright notices
python run.py validate-mime         # Binary mime-type content
python run.py validate              # WCAG 2.1 Level AA
```

---

## Pre-Commit Hooks

Hooks are managed by the [pre-commit](https://pre-commit.com/) framework. After cloning:

```bash
pip install -r requirements.txt
python run.py setup
```

Every commit runs `python run.py pipeline --skip-deploy`. Commits are rejected if any stage fails.
The `--no-verify` flag is **strictly forbidden**.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

Copyright 2026 by GuidoGerb Publishing, LLC.
