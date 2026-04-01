const rawApiBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
const API_BASE = rawApiBase.endsWith('/api') ? rawApiBase.slice(0, -4) : rawApiBase;

function buildUrl(path) {
    return `${API_BASE}${path}`;
}

export async function analyzeWallet(address) {
    const response = await fetch(buildUrl(`/api/wallet/${address}`));
    if (!response.ok) {
        const err = await response.json().catch(() => ({ message: response.statusText }));
        throw new Error(err.message || `API error: ${response.status}`);
    }
    return response.json();
}

export async function getHealthStatus() {
    const response = await fetch(buildUrl('/api/health'));
    return response.json();
}

export function getReportUrl(address) {
    return buildUrl(`/api/report/${address}`);
}
