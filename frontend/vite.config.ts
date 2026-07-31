/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
    // e2e/ holds Playwright specs (run via `npx playwright test`), which use a
    // different test() API than Vitest and must not be collected by it.
    exclude: ["e2e/**", "node_modules/**"],
  },
  server: { port: 5173 },
});
