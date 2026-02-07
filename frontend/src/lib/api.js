async function api(path, options = {}) {
    const res = await fetch(path, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        credentials: 'same-origin',
        ...options
    });

    if (res.status === 401) {
        if (typeof window !== 'undefined' && !path.includes('/api/me')) {
            window.location.href = '/login';
        }
        throw new Error('Not authenticated');
    }

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${res.status}`);
    }

    return res.json();
}

export const get = (path) => api(path);
export const post = (path, body) =>
    api(path, { method: 'POST', body: JSON.stringify(body) });
export const put = (path, body) =>
    api(path, { method: 'PUT', body: JSON.stringify(body) });
