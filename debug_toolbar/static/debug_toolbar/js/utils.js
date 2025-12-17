const $$ = {
    on(root, eventName, selector, fn) {
        root.removeEventListener(eventName, fn);
        root.addEventListener(eventName, (event) => {
            const target = event.target.closest(selector);
            if (root.contains(target)) {
                fn.call(target, event);
            }
        });
    },
    onPanelRender(root, panelId, fn) {
        /*
        This is a helper function to attach a handler for a `djdt.panel.render`
        event of a specific panel.

        root: The container element that the listener should be attached to.
        panelId: The Id of the panel.
        fn: A function to execute when the event is triggered.
         */
        root.addEventListener("djdt.panel.render", (event) => {
            if (event.detail.panelId === panelId) {
                fn.call(event);
            }
        });
    },
    show(element) {
        element.classList.remove("djdt-hidden");
    },
    hide(element) {
        element.classList.add("djdt-hidden");
    },
    toggle(element, value) {
        if (value) {
            $$.show(element);
        } else {
            $$.hide(element);
        }
    },
    visible(element) {
        return !element.classList.contains("djdt-hidden");
    },
    executeScripts(scripts) {
        for (const script of scripts) {
            const el = document.createElement("script");
            el.type = "module";
            el.src = script;
            el.async = true;
            document.head.appendChild(el);
        }
    },
    applyStyles(container) {
        /*
         * Given a container element, apply styles set via data-djdt-styles attribute.
         * The format is data-djdt-styles="styleName1:value;styleName2:value2"
         * The style names should use the CSSStyleDeclaration camel cased names.
         */
        for (const element of container.querySelectorAll(
            "[data-djdt-styles]"
        )) {
            const styles = element.dataset.djdtStyles || "";
            for (const styleText of styles.split(";")) {
                const styleKeyPair = styleText.split(":");
                if (styleKeyPair.length === 2) {
                    const name = styleKeyPair[0].trim();
                    const value = styleKeyPair[1].trim();
                    element.style[name] = value;
                }
            }
        }
    },
};

function ajax(url, init) {
    return fetch(url, Object.assign({ credentials: "same-origin" }, init))
        .then((response) => {
            if (response.ok) {
                return response
                    .json()
                    .catch((error) =>
                        Promise.reject(
                            new Error(
                                `The response  is a invalid Json object : ${error}`
                            )
                        )
                    );
            }
            return Promise.reject(
                new Error(`${response.status}: ${response.statusText}`)
            );
        })
        .catch((error) => {
            const win = document.getElementById("djDebugWindow");
            win.innerHTML = `<div class="djDebugPanelTitle"><h3>${error.message}</h3><button type="button" class="djDebugClose">»</button></div>`;
            $$.show(win);
            throw error;
        });
}

function ajaxForm(element) {
    const form = element.closest("form");
    const url = new URL(form.action);
    const formData = new FormData(form);
    for (const [name, value] of formData.entries()) {
        url.searchParams.append(name, value);
    }
    const ajaxData = {
        method: form.method.toUpperCase(),
    };
    return ajax(url, ajaxData);
}

function replaceToolbarState(newRequestId, data) {
    const djDebug = document.getElementById("djDebug");
    djDebug.setAttribute("data-request-id", newRequestId);
    // Check if response is empty, it could be due to an expired requestId.
    for (const panelId of Object.keys(data)) {
        const panel = document.getElementById(panelId);
        if (panel) {
            panel.outerHTML = data[panelId].content;
            document.getElementById(`djdt-${panelId}`).outerHTML =
                data[panelId].button;
        }
    }
}

function debounce(func, delay) {
    let timer = null;
    let resolves = [];

    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            const result = func(...args);
            for (const r of resolves) {
                r(result);
            }
            resolves = [];
        }, delay);

        return new Promise((r) => resolves.push(r));
    };
}

export { $$, ajax, ajaxForm, replaceToolbarState, debounce };
