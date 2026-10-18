import { afterEach, beforeEach, describe, expect, it } from "vitest";
import toolbarCssUrl from "../../debug_toolbar/static/debug_toolbar/css/toolbar.css?url";

describe("djdt.init() in the shadow DOM", () => {
    let host;
    let shadow;
    let djDebug;

    beforeEach(() => {
        host = document.createElement("div");
        host.id = "djDebugRoot";
        document.body.appendChild(host);
        shadow = host.attachShadow({ mode: "open" });
        djDebug = document.createElement("div");
        djDebug.id = "djDebug";
        djDebug.className = "djdt-hidden";
        djDebug.hidden = true;
        djDebug.dataset.defaultShow = "true";
        djDebug.innerHTML = `
            <div class="djdt-hidden" id="djDebugToolbarHandle"></div>
            <div class="djdt-hidden" id="djDebugToolbar">
                <ul id="djDebugPanelList"></ul>
            </div>
            <div id="djDebugWindow" class="djdt-panelContent djdt-hidden"></div>
        `;
        shadow.appendChild(djDebug);
    });

    afterEach(() => {
        document.body.removeChild(host);
        localStorage.removeItem("djdt.show");
        localStorage.removeItem("djdt.user-theme");
    });

    async function init() {
        if (globalThis.djdt) {
            globalThis.djdt.init();
        } else {
            // The module runs djdt.init() on import.
            await import(
                "../../debug_toolbar/static/debug_toolbar/js/toolbar.js"
            );
        }
    }

    it("keeps #djDebug hidden until toolbar.css loads", async () => {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        shadow.prepend(link);

        await init();
        expect(djDebug.hidden).toBe(true);
        expect(getComputedStyle(djDebug).display).toBe("none");

        const loaded = new Promise((resolve, reject) => {
            link.addEventListener("load", resolve);
            link.addEventListener("error", reject);
        });
        link.href = toolbarCssUrl;
        await loaded;
        expect(djDebug.hidden).toBe(false);
        expect(getComputedStyle(djDebug).display).toBe("block");
    });

    it("removes hidden at once when no stylesheet is pending", async () => {
        await init();
        expect(djDebug.hidden).toBe(false);
    });
});
