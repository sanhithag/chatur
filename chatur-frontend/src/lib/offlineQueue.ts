import type { AxiosInstance } from 'axios'

const KEY = 'chatur-offline-queue'

export interface PendingSubmission {
  url: string
  body: unknown
}

function read(): PendingSubmission[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

function write(items: PendingSubmission[]) {
  localStorage.setItem(KEY, JSON.stringify(items))
}

export function queueSubmission(item: PendingSubmission) {
  write([...read(), item])
}

export function pendingCount(): number {
  return read().length
}

/** Replays queued submissions; returns how many succeeded. */
export async function syncPendingSubmissions(api: AxiosInstance): Promise<number> {
  const items = read()
  const remaining: PendingSubmission[] = []
  let done = 0
  for (const item of items) {
    try {
      await api.post(item.url, item.body)
      done++
    } catch {
      remaining.push(item)
    }
  }
  write(remaining)
  return done
}