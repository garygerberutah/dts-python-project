/**
 * Copyright 2026 by GuidoGerb Publishing, LLC
 *
 * main.js — application entry point.
 * Registers all Web Components and bootstraps the application.
 */

// Dynamic import of components ensures they are defined before use.
import "./components/app-root.js";
import "./components/app-header.js";
import "./components/app-3d-viewer.js";

// Log readiness for debugging during development.
console.info("[app] Web Components registered.");
