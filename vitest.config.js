import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        browser: {
            enabled: true,
            headless: true,
            provider: playwright(),
            // https://vitest.dev/guide/browser/playwright
            instances: [{ browser: "chromium" }, { browser: "firefox" }],
        },
        coverage: {
            enabled: true,
            provider: "istanbul",
            reporter: ["text", "json", "json-summary"],
            reportOnFailure: true,
        },
    },
});
