import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:5185" },
  webServer: {
    command: "npm run dev -- --port 5185 --strictPort",
    url: "http://localhost:5185",
    reuseExistingServer: true,
  },
});
