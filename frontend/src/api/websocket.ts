function getWebSocketBaseUrl() {
  const configuredBaseUrl = import.meta.env.VITE_WS_URL?.trim()

  if (configuredBaseUrl) {
    return configuredBaseUrl.replace(/\/$/, '')
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
}

export function createWebSocketUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${getWebSocketBaseUrl()}${normalizedPath}`
}
