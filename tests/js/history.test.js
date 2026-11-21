import {
    afterAll,
    afterEach,
    beforeAll,
    beforeEach,
    describe,
    expect,
    it,
    vi,
} from "vitest";

describe("history.js", () => {
    let djDebugRoot;

    // history.js binds its handlers to #djDebug when it's imported, so the
    // toolbar markup is created once and the rows are reset between tests.
    beforeAll(async () => {
        djDebugRoot = document.createElement("div");
        djDebugRoot.id = "djDebugRoot";
        djDebugRoot.innerHTML = `
            <div id="djDebug" data-request-id="request-1">
                <div id="djdtStatus" role="status"></div>
                <div id="HistoryPanel" class="djdt-panelContent">
                    <div class="djDebugPanelTitle">
                        <form class="djdtHistoryRefreshForm" method="get" action="/refresh/">
                            <button class="refreshHistory" type="button">Refresh</button>
                        </form>
                    </div>
                    <div class="djDebugPanelContent">
                        <table><tbody id="djdtHistoryRequests"></tbody></table>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(djDebugRoot);
        await import("../../debug_toolbar/static/debug_toolbar/js/history.js");
    });

    beforeEach(() => {
        // The rows start without djdt-highlighted so only the refresh can
        // add it.
        djDebugRoot.querySelector("#djdtHistoryRequests").innerHTML = `
            <tr
                id="historyMain_request-1" data-request-id="request-1"
            >
                Request1
            </tr>
            <tr
                id="historyMain_request-2" data-request-id="request-2"
            >
                Request2
            </tr>
        `;
        djDebugRoot.querySelector("#djdtStatus").textContent = "";
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    afterAll(() => {
        djDebugRoot.remove();
    });

    it("click refresh button", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
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
                                id="historyMain_request-2" data-request-id="request-2"
                            >
                                Request2
                            </tr>
                        `,
                    },
                ],
            }),
        });
        djDebugRoot.querySelector(".refreshHistory").click();

        await vi.waitFor(() => {
            expect(
                djDebugRoot
                    .querySelector('tr[data-request-id="request-1"]')
                    .classList.contains("djdt-highlighted")
            ).toBe(true);
        });
        expect(
            djDebugRoot
                .querySelector('tr[data-request-id="request-2"]')
                .classList.contains("djdt-highlighted")
        ).toBe(false);
    });

    it("does not highlight when the selected request was dropped on the server", async () => {
        // The store dropped request-1 due to RESULTS_CACHE_SIZE.
        vi.spyOn(globalThis, "fetch").mockResolvedValue({
            ok: true,
            json: async () => ({
                requests: [
                    {
                        id: "request-2",
                        content: `
                            <tr
                                id="historyMain_request-2" data-request-id="request-2"
                            >
                                Request2
                            </tr>
                        `,
                    },
                ],
            }),
        });
        djDebugRoot.querySelector(".refreshHistory").click();

        // The status is set after the highlighting, so the refresh has
        // finished once it appears.
        await vi.waitFor(() => {
            expect(djDebugRoot.querySelector("#djdtStatus").textContent).toBe(
                "History up to date"
            );
        });
        expect(djDebugRoot.querySelector("tr.djdt-highlighted")).toBeNull();
    });
});
