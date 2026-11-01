import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { I18nProvider } from './i18n/I18nProvider'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
    mutations: { retry: 0 },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <App />
      </I18nProvider>
    </QueryClientProvider>
  </React.StrictMode>
)

// Register PWA Service Worker in production/PWA mode
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('PWA service worker registration failed:', err)
    })
  })
}

// Background sync on network reconnect
window.addEventListener('online', async () => {
  const { syncPendingSubmissions } = await import('./lib/offlineQueue')
  const api = (await import('./lib/api')).default
  const count = await syncPendingSubmissions(api)
  if (count > 0) {
    console.info(`Synced ${count} offline responses automatically.`)
  }
})
