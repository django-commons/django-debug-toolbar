const $$ = {
    on: function (root, eventName, selector, fn) {
        root.addEventListener(eventName, function (event) {
            const target = event.target.closest(selector);
            if (root.contains(target)) {
                fn.call(target, event);
            }
        });
    },
    show: function (element) {
        element.classList.remove("djdt-hidden");
    },
    hide: function (element) {
        element.classList.add("djdt-hidden");
    },
    toggle: function (element, value) {
        if (value) {
            $$.show(element);
        } else {
            $$.hide(element);
        }
    },
    visible: function (element) {
        element.classList.contains("djdt-hidden");
    },
    executeScripts: function (scripts) {
        scripts.forEach(function (script) {
            const el = document.createElement("script");
            el.type = "module";
            el.src = script;
            el.async = true;
            document.head.appendChild(el);
        });
    },
};

function ajax(url, init) {
    init = Object.assign({ credentials: "same-origin" }, init);
    return fetch(url, init).then(function (response) {
        if (response.ok) {
            return response.json();
        } else {
            const win = document.querySelector("#djDebugWindow");
            win.innerHTML =
                '<div class="djDebugPanelTitle"><a class="djDebugClose" href="">»</a><h3>' +
                response.status +
                ": " +
                response.statusText +
                "</h3></div>";
            $$.show(win);
            return Promise.reject();
        }
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

export { $$, ajax, ajaxForm };
