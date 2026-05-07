import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
    $$,
    ajax,
    ajaxForm,
    debounce,
    replaceToolbarState,
} from "../../debug_toolbar/static/debug_toolbar/js/utils.js";

describe("utils.js", () => {
    describe("$$", () => {
        let root;

        beforeEach(() => {
            root = document.createElement("div");
            document.body.appendChild(root);
        });

        afterEach(() => {
            document.body.removeChild(root);
        });

        describe("on", () => {
            it("attaches an event listener with delegation", async () => {
                const fn = vi.fn();
                const selector = ".target";
                const target = document.createElement("button");
                target.className = "target";
                root.appendChild(target);

                $$.on(root, "click", selector, fn);

                target.click();

                expect(fn).toHaveBeenCalledTimes(1);
                expect(fn.mock.contexts[0]).toBe(target);
            });

            it("does not call fn if target is not within root", () => {
                const fn = vi.fn();
                const selector = ".target";
                const outside = document.createElement("button");
                outside.className = "target";
                document.body.appendChild(outside);

                $$.on(root, "click", selector, fn);

                outside.click();

                expect(fn).not.toHaveBeenCalled();
                document.body.removeChild(outside);
            });
        });

        describe("onPanelRender", () => {
            it("calls fn when djdt.panel.render event is triggered for the specific panel", () => {
                const fn = vi.fn();
                const panelId = "test-panel";
                $$.onPanelRender(root, panelId, fn);

                const event = new CustomEvent("djdt.panel.render", {
                    detail: { panelId },
                });
                root.dispatchEvent(event);

                expect(fn).toHaveBeenCalledTimes(1);
            });

            it("does not call fn when djdt.panel.render event is triggered for a different panel", () => {
                const fn = vi.fn();
                const panelId = "test-panel";
                $$.onPanelRender(root, panelId, fn);

                const event = new CustomEvent("djdt.panel.render", {
                    detail: { panelId: "other-panel" },
                });
                root.dispatchEvent(event);

                expect(fn).not.toHaveBeenCalled();
            });
        });

        describe("visibility functions", () => {
            let element;

            beforeEach(() => {
                element = document.createElement("div");
                root.appendChild(element);
            });

            it("show removes djdt-hidden class", () => {
                element.classList.add("djdt-hidden");
                $$.show(element);
                expect(element.classList.contains("djdt-hidden")).toBe(false);
            });

            it("hide adds djdt-hidden class", () => {
                $$.hide(element);
                expect(element.classList.contains("djdt-hidden")).toBe(true);
            });

            it("toggle shows or hides based on value", () => {
                $$.toggle(element, true);
                expect(element.classList.contains("djdt-hidden")).toBe(false);
                $$.toggle(element, false);
                expect(element.classList.contains("djdt-hidden")).toBe(true);
            });

            it("visible returns true if djdt-hidden class is not present", () => {
                expect($$.visible(element)).toBe(true);
                element.classList.add("djdt-hidden");
                expect($$.visible(element)).toBe(false);
            });
        });

        describe("executeScripts", () => {
            it("creates and appends script elements to document head", () => {
                const scripts = ["/test1.js", "/test2.js"];
                const appendSpy = vi.spyOn(document.head, "appendChild");

                $$.executeScripts(scripts);

                expect(appendSpy).toHaveBeenCalledTimes(2);
                const firstCall = appendSpy.mock.calls[0][0];
                expect(firstCall.tagName).toBe("SCRIPT");
                expect(firstCall.src).toContain("/test1.js");
                expect(firstCall.type).toBe("module");
                expect(firstCall.async).toBe(true);

                appendSpy.mockRestore();
            });
        });

        describe("applyStyles", () => {
            it("applies styles from data-djdt-styles attribute", () => {
                const element = document.createElement("div");
                element.setAttribute(
                    "data-djdt-styles",
                    "backgroundColor:red; display : block"
                );
                root.appendChild(element);

                $$.applyStyles(root);

                expect(element.style.backgroundColor).toBe("red");
                expect(element.style.display).toBe("block");
            });
        });
    });

    describe("ajax", () => {
        const url = "/test-ajax/";

        beforeEach(() => {
            vi.stubGlobal("fetch", vi.fn());
            const djDebugRoot = document.createElement("div");
            djDebugRoot.id = "djDebugRoot";
            const djDebug = document.createElement("div");
            djDebug.id = "djDebug";
            const win = document.createElement("div");
            win.id = "djDebugWindow";
            djDebug.appendChild(win);
            djDebugRoot.appendChild(djDebug);
            document.body.appendChild(djDebugRoot);
        });

        afterEach(() => {
            vi.unstubAllGlobals();
            const djDebugRoot = document.getElementById("djDebugRoot");
            if (djDebugRoot) document.body.removeChild(djDebugRoot);
        });

        it("returns json data on success", async () => {
            const mockData = { key: "value" };
            fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve(mockData),
            });

            const result = await ajax(url);

            expect(result).toEqual(mockData);
            expect(fetch).toHaveBeenCalledWith(url, {
                credentials: "same-origin",
            });
        });

        it("throws error and updates djDebugWindow on non-ok response", async () => {
            fetch.mockResolvedValue({
                ok: false,
                status: 404,
                statusText: "Not Found",
            });

            await expect(ajax(url)).rejects.toThrow("404: Not Found");
            const win = document.getElementById("djDebugWindow");
            expect(win.innerHTML).toContain("404: Not Found");
        });

        it("throws error and updates djDebugWindow on invalid json", async () => {
            fetch.mockResolvedValue({
                ok: true,
                json: () => {
                    throw new Error("JSON parse error");
                },
            });

            await expect(ajax(url)).rejects.toThrow(/JSON parse error/);
            const win = document.getElementById("djDebugWindow");
            expect(win.innerHTML).toContain("JSON parse error");
        });

        it("throws error and updates djDebugWindow on fetch failure", async () => {
            fetch.mockRejectedValue(new Error("Network Error"));

            await expect(ajax(url)).rejects.toThrow("Network Error");
            const win = document.getElementById("djDebugWindow");
            expect(win.innerHTML).toContain("Network Error");
        });
    });

    describe("ajaxForm", () => {
        it("calls ajax with form data and method", async () => {
            vi.stubGlobal("fetch", vi.fn());
            const form = document.createElement("form");
            form.action = "http://localhost/test/";
            form.method = "post";
            const input = document.createElement("input");
            input.name = "field";
            input.value = "val";
            form.appendChild(input);
            const element = document.createElement("button");
            form.appendChild(element);
            document.body.appendChild(form);

            fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true }),
            });

            const result = await ajaxForm(element);

            expect(result).toEqual({ success: true });
            const calledUrl = fetch.mock.calls[0][0];
            expect(calledUrl.toString()).toContain("field=val");
            expect(fetch.mock.calls[0][1].method).toBe("POST");

            document.body.removeChild(form);
            vi.unstubAllGlobals();
        });
    });

    describe("replaceToolbarState", () => {
        it("replaces toolbar state and panels", () => {
            const djDebugRoot = document.createElement("div");
            djDebugRoot.id = "djDebugRoot";
            const djDebug = document.createElement("div");
            djDebug.id = "djDebug";

            const panel = document.createElement("div");
            panel.id = "panel1";
            djDebug.appendChild(panel);

            const buttonContainer = document.createElement("div");
            buttonContainer.id = "djdt-panel1";
            djDebug.appendChild(buttonContainer);

            djDebugRoot.appendChild(djDebug);
            document.body.appendChild(djDebugRoot);

            const data = {
                panel1: {
                    content: '<div id="panel1">New Content</div>',
                    button: '<div id="djdt-panel1">New Button</div>',
                },
            };

            replaceToolbarState("new-id", data);

            expect(djDebug.getAttribute("data-request-id")).toBe("new-id");
            expect(document.getElementById("panel1").innerHTML).toBe(
                "New Content"
            );
            expect(document.getElementById("djdt-panel1").innerHTML).toBe(
                "New Button"
            );

            document.body.removeChild(djDebugRoot);
        });
    });

    describe("debounce", () => {
        beforeEach(() => {
            vi.useFakeTimers();
        });
        afterEach(() => {
            vi.useRealTimers();
        });
        it("debounces sync function calls", async () => {
            const fn = vi.fn((val) => val);
            const debounced = debounce(fn, 100);

            debounced("first");
            debounced("second");

            vi.advanceTimersByTime(50);
            debounced("third");

            vi.advanceTimersByTime(100);

            expect(fn).toHaveBeenCalledTimes(1);
            expect(fn).toHaveBeenCalledWith("third");
        });
        it("debounces async function calls", async () => {
            const fn = vi.fn(async (val) => val);
            const debounced = debounce(fn, 100);

            debounced("first");
            debounced("second");

            vi.advanceTimersByTime(50);
            debounced("third");

            vi.advanceTimersByTime(100);

            expect(fn).toHaveBeenCalledWith("third");
        });
    });
});
