import { describe, it, expect } from "vitest"
import fs from "fs"
import path from "path"

describe("LanguageContext Translation Parity", () => {
  it("should have identical key sets across English, Kannada, and Hindi", () => {
    const filePath = path.resolve(__dirname, "../contexts/LanguageContext.tsx")
    const content = fs.readFileSync(filePath, "utf8")

    const enMatch = content.match(/en:\s*\{([\s\S]*?)\n\s*\},/)
    const knMatch = content.match(/kn:\s*\{([\s\S]*?)\n\s*\},/)
    const hiMatch = content.match(/hi:\s*\{([\s\S]*?)\n\s*\},/)

    expect(enMatch).toBeTruthy()
    expect(knMatch).toBeTruthy()
    expect(hiMatch).toBeTruthy()

    function extractKeys(dictionaryString: string): string[] {
      const keys: string[] = []
      const lines = dictionaryString.split("\n")
      for (const line of lines) {
        const match = line.match(/^\s*"([^"]+)":/)
        if (match) keys.push(match[1])
      }
      return keys
    }

    const enKeys = extractKeys(enMatch![1])
    const knKeys = extractKeys(knMatch![1])
    const hiKeys = extractKeys(hiMatch![1])

    expect(enKeys.length).toBeGreaterThan(400)
    expect(knKeys.length).toBe(enKeys.length)
    expect(hiKeys.length).toBe(enKeys.length)

    const enSet = new Set(enKeys)
    const knSet = new Set(knKeys)
    const hiSet = new Set(hiKeys)

    const missingInKn = enKeys.filter((k) => !knSet.has(k))
    const missingInHi = enKeys.filter((k) => !hiSet.has(k))
    const missingInEnFromKn = knKeys.filter((k) => !enSet.has(k))
    const missingInEnFromHi = hiKeys.filter((k) => !enSet.has(k))

    expect(missingInKn).toEqual([])
    expect(missingInHi).toEqual([])
    expect(missingInEnFromKn).toEqual([])
    expect(missingInEnFromHi).toEqual([])
  })
})
