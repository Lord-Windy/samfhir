import { describe, beforeEach, afterEach, it, expect, vi } from "vitest"
import {
  startRequest,
  endRequest,
  getSlowRequestElapsed,
  subscribe,
  reset,
} from "./request-timing"

describe("request-timing", () => {
  beforeEach(() => {
    reset()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe("startRequest and endRequest", () => {
    it("returns null when no requests are pending", () => {
      expect(getSlowRequestElapsed()).toBeNull()
    })

    it("returns null for requests under 1 second", () => {
      const id = startRequest("/api/test")
      vi.advanceTimersByTime(500)
      expect(getSlowRequestElapsed()).toBeNull()
      endRequest(id)
    })

    it("returns elapsed time for slow requests", () => {
      const id = startRequest("/api/test")
      vi.advanceTimersByTime(1500)
      expect(getSlowRequestElapsed()).toBe(1500)
      endRequest(id)
    })

    it("returns null after request ends", () => {
      const id = startRequest("/api/test")
      vi.advanceTimersByTime(1500)
      expect(getSlowRequestElapsed()).toBe(1500)
      endRequest(id)
      expect(getSlowRequestElapsed()).toBeNull()
    })

    it("tracks the maximum elapsed time across multiple requests", () => {
      const id1 = startRequest("/api/test1")
      vi.advanceTimersByTime(500)
      const id2 = startRequest("/api/test2")
      vi.advanceTimersByTime(700)
      
      expect(getSlowRequestElapsed()).toBe(1200)
      
      endRequest(id1)
      expect(getSlowRequestElapsed()).toBeNull()
      
      endRequest(id2)
      expect(getSlowRequestElapsed()).toBeNull()
    })
  })

  describe("subscribe", () => {
    it("notifies listeners when requests start", () => {
      const listener = vi.fn()
      subscribe(listener)
      
      startRequest("/api/test")
      expect(listener).toHaveBeenCalledTimes(1)
    })

    it("notifies listeners when requests end", () => {
      const listener = vi.fn()
      subscribe(listener)
      
      const id = startRequest("/api/test")
      listener.mockClear()
      
      endRequest(id)
      expect(listener).toHaveBeenCalledTimes(1)
    })

    it("unsubscribe removes the listener", () => {
      const listener = vi.fn()
      const unsubscribe = subscribe(listener)
      
      unsubscribe()
      
      startRequest("/api/test")
      expect(listener).not.toHaveBeenCalled()
    })
  })
})
