import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatRelativeTime(timestamp: number): string {
  const now = Date.now()
  const diff = Math.floor((now - timestamp) / 1000)

  if (diff < 60) {
    return `Updated ${diff}s ago`
  }

  const minutes = Math.floor(diff / 60)
  if (minutes < 60) {
    return `Updated ${minutes}m ago`
  }

  const hours = Math.floor(minutes / 60)
  if (hours < 24) {
    return `Updated ${hours}h ago`
  }

  const days = Math.floor(hours / 24)
  return `Updated ${days}d ago`
}
