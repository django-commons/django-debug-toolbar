document.addEventListener("click", (event) => {
    if (event.target.classList.contains("copy-context")) {
        const context = event.target.getAttribute("data-context");

        if (context) {
            try {
                const decodedContext = decodeUnicode(context);
                const listContext = makeList(decodedContext);

                navigator.clipboard
                    .writeText(listContext)
                    .then(() => {
                        const originalText = event.target.textContent;
                        event.target.textContent = "Copied!";

                        setTimeout(() => {
                            event.target.textContent = originalText;
                        }, 2000);
                    })
                    .catch((error) => {
                        console.error("Failed to copy context:", error);
                    });
            } catch (error) {
                console.error("Error processing context:", error);
            }
        }
    }
});

/**
 * Decodes escaped Unicode characters in a string.
 *
 * @param {string} text - The text containing escaped Unicode characters.
 * @returns {string} - Decoded text.
 */
function decodeUnicode(text) {
    return text.replace(/\\u[\dA-Fa-f]{4}/g, (match) => {
        return String.fromCharCode(
            Number.parseInt(match.replace("\\u", ""), 16)
        );
    });
}

/**
 * Wraps multiple JSON objects into a list format.
 *
 * @param {string} text - The raw text containing multiple JSON objects.
 * @returns {string} - Properly formatted JSON array string.
 */
function makeList(text) {
    return `[${text.replace(/\n(?=\{)/g, ",")}]`;
}
