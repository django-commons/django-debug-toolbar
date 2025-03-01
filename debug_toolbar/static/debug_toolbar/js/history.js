import { $$, ajaxForm, replaceToolbarState } from "./utils.js";

const djDebug = document.getElementById("djDebug");

function difference(setA, setB) {
    const _difference = new Set(setA);
    for (const elem of setB) {
        _difference.delete(elem);
    }
    return _difference;
}

/**
 * Create an array of dataset properties from a NodeList.
 */
function pluckData(nodes, key) {
    return [...nodes].map((obj) => obj.dataset[key]);
}

function refreshHistory() {
    const formTarget = djDebug.querySelector(".refreshHistory");
    const container = document.getElementById("djdtHistoryRequests");
    const oldIds = new Set(
        pluckData(container.querySelectorAll("tr[data-store-id]"), "storeId")
    );

    ajaxForm(formTarget)
        .then((data) => {
            // Remove existing rows first then re-populate with new data
            for (const node of container.querySelectorAll(
                "tr[data-store-id]"
            )) {
                node.remove();
            }
            for (const request of data.requests) {
                container.innerHTML = request.content + container.innerHTML;
            }
        })
        .then(() => {
            const allIds = new Set(
                pluckData(
                    container.querySelectorAll("tr[data-store-id]"),
                    "storeId"
                )
            );
            const newIds = difference(allIds, oldIds);
            const lastRequestId = newIds.values().next().value;
            return {
                allIds,
                newIds,
                lastRequestId,
            };
        })
        .then((refreshInfo) => {
            for (const newId of refreshInfo.newIds) {
                const row = container.querySelector(
                    `tr[data-store-id="${newId}"]`
                );
                row.classList.add("flash-new");
            }
            setTimeout(() => {
                for (const row of container.querySelectorAll(
                    "tr[data-store-id]"
                )) {
                    row.classList.remove("flash-new");
                }
            }, 2000);
        });
}

function switchHistory(newStoreId) {
    const formTarget = djDebug.querySelector(
        `.switchHistory[data-store-id='${newStoreId}']`
    );
    const tbody = formTarget.closest("tbody");

    const highlighted = tbody.querySelector(".djdt-highlighted");
    if (highlighted) {
        highlighted.classList.remove("djdt-highlighted");
    }
    formTarget.closest("tr").classList.add("djdt-highlighted");

    ajaxForm(formTarget).then((data) => {
        if (Object.keys(data).length === 0) {
            const container = document.getElementById("djdtHistoryRequests");
            container.querySelector(
                `button[data-store-id="${newStoreId}"]`
            ).innerHTML = "Switch [EXPIRED]";
        }
        replaceToolbarState(newStoreId, data);
    });
}

$$.on(djDebug, "click", ".switchHistory", function (event) {
    event.preventDefault();
    switchHistory(this.dataset.storeId);
});

$$.on(djDebug, "click", ".refreshHistory", (event) => {
    event.preventDefault();
    refreshHistory();
});
// We don't refresh the whole toolbar each fetch or ajax request,
// so we need to refresh the history when we open the panel
$$.onPanelRender(djDebug, "HistoryPanel", refreshHistory);
