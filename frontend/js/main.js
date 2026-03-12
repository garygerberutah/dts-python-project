/**
 * main.js — application entry point.
 * Registers all Web Components and bootstraps the application.
 */

// Dynamic import of components ensures they are defined before use.
import "./components/app-root.js";
import "./components/app-header.js";
import "./components/app-3d-viewer.js";

// Log readiness for debugging during development.
console.info("[ggp3d] Web Components registered.");
