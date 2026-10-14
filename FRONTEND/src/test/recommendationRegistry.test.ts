import { describe, it, expect } from "vitest"
import {
  RECOMMENDATIONS_REGISTRY,
  getRecommendationsForDisease,
  getActionableTreatments,
  getBlockedTreatments,
  getRegistrySummaryStats,
} from "../data/recommendationRegistry"
import { AGRONOMIC_PRESCRIPTIONS } from "../components/TreatmentCalculatorModal"

describe("Recommendation Registry & Safety Enforcement", () => {
  it("contains 22 audited records with valid statuses and categories", () => {
    expect(RECOMMENDATIONS_REGISTRY.length).toBe(22)
    for (const r of RECOMMENDATIONS_REGISTRY) {
      expect(r.id.startsWith("REC-")).toBe(true)
      expect(r.targetDiseaseKey).toBeTruthy()
      expect(r.sourceOrganization).toBeTruthy()
      expect(r.safetyCaveats.length).toBeGreaterThan(0)

      if (r.actionableChemicalAllowed) {
        expect(r.verificationStatus).toBe("VERIFIED_OFFICIAL")
        expect(r.displayEligible).toBe(true)
      }

      if (r.verificationStatus === "BLOCKED_UNVERIFIED" || r.verificationStatus === "OUTDATED_REVIEW_REQUIRED") {
        expect(r.actionableChemicalAllowed).toBe(false)
        expect(r.displayEligible).toBe(false)
      }
    }
  })

  it("FruitRot has official 1% Bordeaux and blocks unverified systemic oomyceticides", () => {
    const records = getRecommendationsForDisease("FruitRot")
    const bordeaux = records.find((r) => r.id === "REC-FR-01")
    expect(bordeaux).toBeDefined()
    expect(bordeaux?.verificationStatus).toBe("VERIFIED_OFFICIAL")
    expect(bordeaux?.actionableChemicalAllowed).toBe(true)

    const blocked = getBlockedTreatments("FruitRot")
    expect(blocked.some((r) => r.id === "REC-FR-04")).toBe(true)
  })

  it("PhytoplasmaYellowLeaf strictly blocks fungicides from actionable advice", () => {
    const treatments = getActionableTreatments("PhytoplasmaYellowLeaf")
    for (const t of treatments) {
      expect(t.toLowerCase()).not.toContain("bordeaux")
      expect(t.toLowerCase()).not.toContain("carbendazim")
      expect(t.toLowerCase()).not.toContain("mancozeb")
    }
    const blocked = getBlockedTreatments("PhytoplasmaYellowLeaf")
    expect(blocked.some((r) => r.id === "REC-YLD-02")).toBe(true)
  })

  it("NutCracking recommends Borax, strictly not fungicides", () => {
    const treatments = getActionableTreatments("NutCracking")
    expect(treatments.some((t) => t.includes("Borax"))).toBe(true)
    expect(
      treatments.some((t) =>
        t.toLowerCase().includes("fungicides are completely ineffective")
      )
    ).toBe(true)
  })

  it("BudBorer actionable treatments do not recommend Chlorpyrifos", () => {
    const treatments = getActionableTreatments("BudBorer")
    for (const t of treatments) {
      expect(t.toLowerCase()).not.toContain("chlorpyrifos")
    }
  })

  it("StemBleeding REC-SB-01 is REVIEW_REQUIRED and topical chemical application is withheld", () => {
    const records = getRecommendationsForDisease("StemBleeding")
    const recSb01 = records.find((r) => r.id === "REC-SB-01")
    expect(recSb01).toBeDefined()
    expect(recSb01?.verificationStatus).toBe("REVIEW_REQUIRED")
    expect(recSb01?.actionableChemicalAllowed).toBe(false)
    expect(recSb01?.activeIngredient).toBeUndefined()
    expect(recSb01?.dosagePerLiter).toBeUndefined()

    const recSb02 = records.find((r) => r.id === "REC-SB-02")
    expect(recSb02).toBeDefined()
    expect(recSb02?.verificationStatus).toBe("OUTDATED_REVIEW_REQUIRED")
    expect(recSb02?.actionableChemicalAllowed).toBe(false)
    expect(recSb02?.guidanceText.toLowerCase()).toContain("banned")

    const treatments = getActionableTreatments("StemBleeding")
    expect(treatments.length).toBeGreaterThan(0)
    expect(treatments.some((t) => t.toLowerCase().includes("not shown") || t.toLowerCase().includes("could not be verified"))).toBe(true)
  })

  it("TreatmentCalculatorModal blocks unverified chemicals and flags them", () => {
    expect(AGRONOMIC_PRESCRIPTIONS.bud_borer.isChemicalBlocked).toBe(true)
    expect(AGRONOMIC_PRESCRIPTIONS.bud_borer.chemicalStandard.chemicalPerLiterGrams).toBe(0)

    expect(AGRONOMIC_PRESCRIPTIONS.yellow_leaf.isChemicalBlocked).toBe(true)
    expect(AGRONOMIC_PRESCRIPTIONS.yellow_leaf.chemicalStandard.chemicalPerLiterGrams).toBe(0)

    expect(AGRONOMIC_PRESCRIPTIONS.stem_bleeding.isChemicalBlocked).toBe(true)
    expect(AGRONOMIC_PRESCRIPTIONS.stem_bleeding.chemicalStandard.chemicalPerLiterGrams).toBe(0)
    expect(AGRONOMIC_PRESCRIPTIONS.stem_bleeding.blockedReason).toContain("conflicting documentation")

    expect(AGRONOMIC_PRESCRIPTIONS.koleroga.isChemicalBlocked).toBeFalsy()
    expect(AGRONOMIC_PRESCRIPTIONS.koleroga.chemicalStandard.chemicalPerLiterGrams).toBe(10)

    expect(AGRONOMIC_PRESCRIPTIONS.anthracnose.chemicalStandard.activeIngredient).toContain("Copper Oxychloride")
    expect(AGRONOMIC_PRESCRIPTIONS.anthracnose.chemicalStandard.activeIngredient).not.toContain("Mancozeb")
  })

  it("Fertilizer & nutrient recommendations follow ICAR-CPCRI standards and safety thresholds", () => {
    // 1. Healthy Palms Routine Fertigation (REC-HLT-01)
    const recHlt = RECOMMENDATIONS_REGISTRY.find((r) => r.id === "REC-HLT-01")
    expect(recHlt).toBeDefined()
    expect(recHlt?.verificationStatus).toBe("VERIFIED_OFFICIAL")
    expect(recHlt?.category).toBe("NUTRIENT_MANAGEMENT")
    expect(recHlt?.activeIngredient).toContain("100g N, 40g P2O5, 140g K2O")
    expect(recHlt?.formulation).toContain("220g Urea")
    expect(recHlt?.formulation).toContain("200g Rock Phosphate")
    expect(recHlt?.formulation).toContain("235g Muriate of Potash")

    // 2. Nut Cracking Borax application (REC-NC-01)
    const recNc = RECOMMENDATIONS_REGISTRY.find((r) => r.id === "REC-NC-01")
    expect(recNc).toBeDefined()
    expect(recNc?.verificationStatus).toBe("VERIFIED_OFFICIAL")
    expect(recNc?.dosagePerPalm).toContain("15g to 20g")
    expect(recNc?.safetyCaveats.some((c) => c.includes("25g"))).toBe(true)

    // 3. Phytoplasma Yellow Leaf Disease sustenance (REC-YLD-01) — NOT A CURE
    const recYld = RECOMMENDATIONS_REGISTRY.find((r) => r.id === "REC-YLD-01")
    expect(recYld).toBeDefined()
    expect(recYld?.verificationStatus).toBe("VERIFIED_OFFICIAL")
    expect(recYld?.dosagePerPalm).toContain("100g Magnesium Sulphate")
    expect(recYld?.dosagePerPalm).toContain("50g Zinc Sulphate")
    expect(recYld?.guidanceText.toLowerCase()).toContain("no chemical cure")
    expect(recYld?.safetyCaveats.some((c) => c.toLowerCase().includes("not a cure"))).toBe(true)

    // 4. Yellow Leaf nutritional chlorosis / drainage (REC-YL-01)
    const recYl = RECOMMENDATIONS_REGISTRY.find((r) => r.id === "REC-YL-01")
    expect(recYl).toBeDefined()
    expect(recYl?.verificationStatus).toBe("VERIFIED_OFFICIAL")
    expect(recYl?.dosagePerPalm).toContain("500g Dolomite")
    expect(recYl?.dosagePerPalm).toContain("50g Zinc Sulphate")

    // 5. TreatmentCalculatorModal YLD and Stem Bleeding nutrient safety checks
    expect(AGRONOMIC_PRESCRIPTIONS.yellow_leaf.blockedReason).toContain("NOT A CURE")
    expect(AGRONOMIC_PRESCRIPTIONS.yellow_leaf.fertilizerCorrection.micronutrientAddon).toContain("NOT A CURE")
    expect(AGRONOMIC_PRESCRIPTIONS.yellow_leaf.fertilizerCorrection.micronutrientAddon).not.toContain("150g Borax")
    expect(AGRONOMIC_PRESCRIPTIONS.stem_bleeding.fertilizerCorrection.micronutrientAddon).not.toContain("50g Borax")
    expect(AGRONOMIC_PRESCRIPTIONS.stem_bleeding.fertilizerCorrection.micronutrientAddon).toContain("15–20g Borax")
  })
})
