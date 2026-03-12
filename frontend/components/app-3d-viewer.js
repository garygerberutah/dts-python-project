/**
 * app-3d-viewer — 3D canvas viewer Web Component.
 * Renders a 3D scene using the Rust WASM math engine and WebGL.
 */
class App3dViewer extends HTMLElement {
  #shadow;
  #canvas;
  #gl;
  #animFrameId;
  #wasm = null;
  #rotation = 0;

  static #RAD_TO_DEG = 180 / Math.PI;

  constructor() {
    super();
    this.#shadow = this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    this.#render();
    this.#canvas = this.#shadow.getElementById("gl-canvas");
    this.#initGL();
    window.addEventListener("wasm-ready", (e) => this.#onWasmReady(e), { once: true });
  }

  disconnectedCallback() {
    if (this.#animFrameId) {
      cancelAnimationFrame(this.#animFrameId);
    }
    window.removeEventListener("wasm-ready", this.#onWasmReady);
  }

  #render() {
    this.#shadow.innerHTML = `
      <style>
        :host {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 1rem 0;
        }
        .canvas-container {
          position: relative;
          border: 1px solid #30363d;
          border-radius: 8px;
          overflow: hidden;
          background: #010409;
        }
        canvas {
          display: block;
          width: 640px;
          height: 480px;
        }
        .overlay {
          position: absolute;
          top: 0.5rem;
          left: 0.5rem;
          font-size: 0.75rem;
          color: #8b949e;
          background: rgba(13, 17, 23, 0.8);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
        }
        .info-panel {
          width: 640px;
          background: #161b22;
          border: 1px solid #30363d;
          border-radius: 8px;
          padding: 1rem;
          font-size: 0.875rem;
        }
        .info-panel h2 {
          margin: 0 0 0.5rem;
          font-size: 1rem;
          color: #58a6ff;
        }
        dl {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.25rem 1rem;
          margin: 0;
        }
        dt { color: #8b949e; }
        dd { margin: 0; color: #e6edf3; font-family: monospace; }
      </style>
      <div class="canvas-container">
        <canvas
          id="gl-canvas"
          width="640"
          height="480"
          aria-label="Interactive 3D geometry viewer canvas"
          role="img">
          Your browser does not support WebGL or the canvas element.
        </canvas>
        <div class="overlay" aria-hidden="true">WebGL + Rust WASM</div>
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
  }

  #initGL() {
    this.#gl = this.#canvas.getContext("webgl2") || this.#canvas.getContext("webgl");
    if (!this.#gl) {
      console.warn("[app-3d-viewer] WebGL not available, falling back to 2D");
      this.#draw2dFallback();
      return;
    }
    this.#draw3d();
  }

  #onWasmReady(event) {
    this.#wasm = event.detail.wasm;
    const rotValEl = this.#shadow.getElementById("rotation-val");
    if (rotValEl) {
      rotValEl.textContent = "WASM active";
    }
  }

  #draw3d() {
    const gl = this.#gl;
    gl.clearColor(0.051, 0.067, 0.09, 1.0);
    gl.enable(gl.DEPTH_TEST);

    const vsSource = `
      attribute vec4 aPosition;
      attribute vec3 aColor;
      uniform mat4 uProjection;
      uniform mat4 uModel;
      varying vec3 vColor;
      void main() {
        gl_Position = uProjection * uModel * aPosition;
        vColor = aColor;
      }
    `;
    const fsSource = `
      precision mediump float;
      varying vec3 vColor;
      void main() {
        gl_FragColor = vec4(vColor, 1.0);
      }
    `;

    const prog = this.#compileProgram(vsSource, fsSource);
    if (!prog) return;

    const vertices = new Float32Array([
       0.0,  0.7,  0.0,   1.0, 0.22, 0.22,
      -0.6, -0.35, 0.0,   0.22, 0.55, 1.0,
       0.6, -0.35, 0.0,   0.22, 1.0, 0.55,
    ]);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

    const posLoc = gl.getAttribLocation(prog, "aPosition");
    const colLoc = gl.getAttribLocation(prog, "aColor");
    const projLoc = gl.getUniformLocation(prog, "uProjection");
    const modelLoc = gl.getUniformLocation(prog, "uModel");

    const stride = 6 * 4;
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 3, gl.FLOAT, false, stride, 0);
    gl.enableVertexAttribArray(colLoc);
    gl.vertexAttribPointer(colLoc, 3, gl.FLOAT, false, stride, 3 * 4);

    const proj = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0];
    const vertexCountEl = this.#shadow.getElementById("vertex-count");
    const rotationValEl = this.#shadow.getElementById("rotation-val");
    if (vertexCountEl) vertexCountEl.textContent = "3";

    const draw = () => {
      this.#rotation += 0.01;
      const c = Math.cos(this.#rotation);
      const s = Math.sin(this.#rotation);
      const model = [c, 0, s, 0, 0, 1, 0, 0, -s, 0, c, 0, 0, 0, 0, 1.0];

      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.useProgram(prog);
      gl.uniformMatrix4fv(projLoc, false, proj);
      gl.uniformMatrix4fv(modelLoc, false, model);
      gl.drawArrays(gl.TRIANGLES, 0, 3);

      if (rotationValEl) {
        rotationValEl.textContent = (this.#rotation * App3dViewer.#RAD_TO_DEG).toFixed(1) + "°";
      }
      this.#animFrameId = requestAnimationFrame(draw);
    };
    draw();
  }

  #draw2dFallback() {
    const ctx = this.#canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#0d1117";
    ctx.fillRect(0, 0, 640, 480);
    ctx.fillStyle = "#58a6ff";
    ctx.font = "20px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("WebGL not available", 320, 240);
  }

  #compileProgram(vsSource, fsSource) {
    const gl = this.#gl;
    const vs = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vs, vsSource);
    gl.compileShader(vs);
    if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
      console.error("[app-3d-viewer] VS compile error:", gl.getShaderInfoLog(vs));
      return null;
    }
    const fs = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fs, fsSource);
    gl.compileShader(fs);
    if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
      console.error("[app-3d-viewer] FS compile error:", gl.getShaderInfoLog(fs));
      return null;
    }
    const prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error("[app-3d-viewer] Program link error:", gl.getProgramInfoLog(prog));
      return null;
    }
    return prog;
  }
}

customElements.define("app-3d-viewer", App3dViewer);
export { App3dViewer };
