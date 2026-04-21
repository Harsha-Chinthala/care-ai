window.CARE_AI_API_BASE = window.CARE_AI_API_BASE || "";

window.getCareAiApiUrl = function getCareAiApiUrl(path) {
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;

    if (window.CARE_AI_API_BASE) {
        return `${window.CARE_AI_API_BASE}${normalizedPath}`;
    }

    const isLocalStaticPreview = ["127.0.0.1", "localhost"].includes(window.location.hostname)
        && window.location.port === "3000";

    if (isLocalStaticPreview) {
        return `http://127.0.0.1:5000${normalizedPath}`;
    }

    return normalizedPath;
};
