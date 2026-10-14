import { describe, it, expect, beforeEach, vi } from "vitest"
import {
  safeGetItem,
  safeSetItem,
  safeRemoveItem,
  safeGetJSON,
  safeSetJSON,
} from "../utils/safeStorage"

describe("safeStorage utility", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it("stores and retrieves strings safely", () => {
    expect(safeSetItem("test_key", "hello")).toBe(true)
    expect(safeGetItem("test_key")).toBe("hello")
    expect(safeGetItem("nonexistent", "default")).toBe("default")
  })

  it("removes items safely", () => {
    safeSetItem("remove_key", "value")
    safeRemoveItem("remove_key")
    expect(safeGetItem("remove_key")).toBeNull()
  })

  it("stores and retrieves JSON objects safely", () => {
    const data = { id: 1, name: "Block A" }
    expect(safeSetJSON("data_key", data)).toBe(true)
    expect(safeGetJSON("data_key", null)).toEqual(data)
  })

  it("returns fallback on invalid JSON", () => {
    localStorage.setItem("bad_json", "{invalid_json")
    expect(safeGetJSON("bad_json", { fallback: true })).toEqual({ fallback: true })
  })

  it("validates data using the provided validator", () => {
    safeSetJSON("not_array", { a: 1 })
    const result = safeGetJSON("not_array", [], Array.isArray)
    expect(result).toEqual([])

    safeSetJSON("is_array", [1, 2, 3])
    const arrayResult = safeGetJSON("is_array", [], Array.isArray)
    expect(arrayResult).toEqual([1, 2, 3])
  })

  it("handles SecurityError gracefully (private browsing mode)", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("The operation is insecure.", "SecurityError")
    })
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("The operation is insecure.", "SecurityError")
    })

    expect(safeGetItem("any_key", "fallback")).toBe("fallback")
    expect(safeSetItem("any_key", "val")).toBe(false)
    expect(safeGetJSON("any_key", [1], Array.isArray)).toEqual([1])
    expect(safeSetJSON("any_key", { x: 1 })).toBe(false)
  })
})
