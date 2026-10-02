import { afterEach, beforeEach, describe, expect, it } from "vitest";
import toolbarCssUrl from "../../debug_toolbar/static/debug_toolbar/css/toolbar.css?url";
import { $$ } from "../../debug_toolbar/static/debug_toolbar/js/utils.js";

describe("toolbar.css in the shadow DOM", () => {
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
        shadow.appendChild(djDebug);
    });

    afterEach(() => {
        document.body.removeChild(host);
    });

    function loadToolbarCss() {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = toolbarCssUrl;
        const loaded = new Promise((resolve, reject) => {
            link.addEventListener("load", resolve);
            link.addEventListener("error", reject);
        });
        shadow.prepend(link);
        return loaded;
    }

    it("keeps #djDebug hidden before the stylesheet loads", () => {
        $$.show(djDebug);
        expect(getComputedStyle(djDebug).display).toBe("none");
    });

    it("shows and hides #djDebug once the stylesheet loads", async () => {
        await loadToolbarCss();
        expect(getComputedStyle(djDebug).display).toBe("none");

        $$.show(djDebug);
        expect(getComputedStyle(djDebug).display).toBe("block");

        $$.hide(djDebug);
        expect(getComputedStyle(djDebug).display).toBe("none");
    });
});
