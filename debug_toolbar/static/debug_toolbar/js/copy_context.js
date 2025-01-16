document.addEventListener("click", (event) => {
    if (event.target.classList.contains("copy-context")) {
        const context = event.target.getAttribute("data-context");

        if (context) {
            try {
                const decodedContext = decodeUnicode(context);
                navigator.clipboard
                    .writeText(decodedContext)
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
                console.error("Error decoding context:", error);
            }
        }
    }
});

/**
 * Decodes escaped Unicode characters in a string.
 * E.g., converts "\\u0027" to "'".
 *
 * @param {string} text - The text containing escaped Unicode characters.
 * @returns {string} - Decoded text.
 */
function decodeUnicode(text) {
    return text.replace(/\\u[\dA-Fa-f]{4}/g, (match) => {
        return String.fromCharCode(parseInt(match.replace("\\u", ""), 16));
    });
}
