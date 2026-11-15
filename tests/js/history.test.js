import { describe, expect, it, vi } from "vitest";

describe("history.js", () => {
    it("click refresh button", async () => {
        const djDebugRoot = document.createElement("div");
        djDebugRoot.id = "djDebugRoot";
        djDebugRoot.innerHTML = `
            <div id="djDebug" data-request-id="request-1">
                <div id="HistoryPanel" class="djdt-panelContent">
                    <div class="djDebugPanelTitle">
                        <form class="djdtHistoryRefreshForm" method="get" action="/refresh/">
                            <button class="refreshHistory" type="button">Refresh</button>
                        </form>
                    </div>
                    <div class="djDebugPanelContent">
                        <table><tbody id="djdtHistoryRequests">
                            <tr
                                id="historyMain_request-1" class="djdt-highlighted" data-request-id="request-1"
                            >
                                Request1
                            </tr>
                            <tr
                                id="historyMain_request-2" class="djdt-highlighted" data-request-id="request-2"
                            >
                                Request2
                            </tr>
                        </tbody></table>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(djDebugRoot);

        await vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            json: async () => ({
                requests: [
                    {
                        id: "request-1",
                        content: `
                            <tr
                                id="historyMain_request-1" data-request-id="request-1"
                            >
                                Request1
                            </tr>
                        `,
                    },
                    {
                        id: "request-2",
                        content: `
                            <tr
                                id="historyMain_request-2"" data-request-id="request-2"
                            >
                                Request2
                            </tr>
                        `,
                    },
                ],
            }),
        });
        await import("../../debug_toolbar/static/debug_toolbar/js/history.js");
        djDebugRoot.querySelector(".refreshHistory").click();

        await vi.waitFor(() => {
            expect(
                djDebugRoot
                    .querySelector('tr[data-request-id="request-1"]')
                    .classList.contains("djdt-highlighted")
            ).toBe(true);
        });
    });
});
