import { webdriverio } from "@vitest/browser-webdriverio";
import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        browser: {
            enabled: true,
            headless: true,
            provider: webdriverio(),
            // https://vitest.dev/config/browser/webdriverio
            instances: [{ browser: "chrome" }, { browser: "firefox" }],
        },
        coverage: {
            enabled: true,
            provider: "istanbul",
        },
    },
});
