import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    files: ["frontend/**/*.js"],
    ignores: ["frontend/**/*.test.js", "node_modules/**", "dist/**"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        customElements: "readonly",
        HTMLElement: "readonly",
        CustomEvent: "readonly",
        requestAnimationFrame: "readonly",
        cancelAnimationFrame: "readonly",
      },
    },
    rules: {
      "no-unused-vars": "error",
      "no-console": ["warn", { allow: ["info", "warn", "error"] }],
      "eqeqeq": "error",
      "no-var": "error",
      "prefer-const": "error",
    },
  },
];
