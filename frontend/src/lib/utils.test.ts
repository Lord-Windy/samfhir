import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { formatRelativeTime } from "./utils"

describe("formatRelativeTime", () => {
  const now = 1000000000000

  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(now)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("formats seconds ago", () => {
    expect(formatRelativeTime(now - 5000)).toBe("Updated 5s ago")
    expect(formatRelativeTime(now - 30000)).toBe("Updated 30s ago")
    expect(formatRelativeTime(now - 59000)).toBe("Updated 59s ago")
  })

  it("formats minutes ago", () => {
    expect(formatRelativeTime(now - 60000)).toBe("Updated 1m ago")
    expect(formatRelativeTime(now - 300000)).toBe("Updated 5m ago")
    expect(formatRelativeTime(now - 3599000)).toBe("Updated 59m ago")
  })

  it("formats hours ago", () => {
    expect(formatRelativeTime(now - 3600000)).toBe("Updated 1h ago")
    expect(formatRelativeTime(now - 7200000)).toBe("Updated 2h ago")
    expect(formatRelativeTime(now - 86399000)).toBe("Updated 23h ago")
  })

  it("formats days ago", () => {
    expect(formatRelativeTime(now - 86400000)).toBe("Updated 1d ago")
    expect(formatRelativeTime(now - 259200000)).toBe("Updated 3d ago")
  })
})
