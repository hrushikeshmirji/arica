import React, { useState, useMemo } from "react"
import {
  X,
  Calculator,
  Droplets,
  Sprout,
  DollarSign,
  Printer,
  ShieldCheck,
  AlertTriangle,
  Plane,
  Layers,
  Sparkles,
  Info,
  Calendar,
  CheckCircle2,
  Package,
  FileText,
  BadgeAlert,
  Leaf,
} from "lucide-react"

export interface TreatmentCalculatorProps {
  isOpen: boolean
  onClose: () => void
  initialDisease?: string
  initialPalms?: number
  initialMode?: "pesticides" | "fertilizers"
}

export interface DiseaseTreatmentGuidance {
  name: string
  scientificName: string
  category: "fungal" | "phytoplasma" | "physiological" | "pest"
  isChemicalBlocked?: boolean
  blockedReason?: string
  chemicalStandard: {
    title: string
    activeIngredient: string
    commercialExample: string
    dosagePerLiter: string
    chemicalRatePerUnit: number // Rs per kg or L
    chemicalPerLiterGrams: number
    requiresLime?: boolean
    limeRatePerKg?: number
    stickerRequired: boolean
    stickerMlPerLiter: number
    instructions: string[]
    withholdingDays: number // PHI
    applicationNote: string
  }
  organicStandard: {
    title: string
    activeBioAgent: string
    dosagePerLiter: string
    organicRatePerUnit: number
    organicPerLiterGrams: number
    neemOilRequired: boolean
    neemOilMlPerLiter: number
    instructions: string[]
    withholdingDays: number
    applicationNote: string
  }
  fertilizerCorrection: {
    soilTreatment: string
    micronutrientAddon: string
  }
}

export type DiseasePrescription = DiseaseTreatmentGuidance

export const AGRONOMIC_PRESCRIPTIONS: Record<string, DiseaseTreatmentGuidance> = {
  koleroga: {
    name: "Koleroga / Fruit Rot",
    scientificName: "Phytophthora meadii",
    category: "fungal",
    chemicalStandard: {
      title: "1% Neutral Bordeaux Mixture + Rosin-Soda Sticker",
      activeIngredient: "Copper Sulphate (CuSO₄) + Quicklime (CaO)",
      commercialExample: "Technical Grade Copper Sulphate + High Calcium Quicklime",
      dosagePerLiter: "10g CuSO₄ + 10g Quicklime / 1L water",
      chemicalRatePerUnit: 240, // Rs/kg CuSO4
      chemicalPerLiterGrams: 10,
      requiresLime: true,
      limeRatePerKg: 35,
      stickerRequired: true,
      stickerMlPerLiter: 1.0, // Rosin-soda adhesive
      instructions: [
        "Dissolve 1kg Copper Sulphate in 50L water in an earthen or plastic drum (never use metal vessels).",
        "Slake 1kg freshly burnt Quicklime in another 50L water in a separate container.",
        "Pour copper solution slowly into the lime solution while constantly stirring with a wooden rod.",
        "Knife Test: Dip a clean iron blade for 1 minute; if reddish copper precipitates, add more lime water until blade stays clean.",
        "Add rosin-soda sticker just prior to spraying to prevent heavy southwest monsoon wash-off."
      ],
      withholdingDays: 14,
      applicationNote: "Spray 2 to 2.5 Litres per mature palm canopy covering all nut bunches thoroughly before monsoon onset."
    },
    organicStandard: {
      title: "Trichoderma viride Bio-Shield + Cold-Pressed Neem Oil",
      activeBioAgent: "Trichoderma viride (min 2x10⁸ CFU/g) + Azadirachtin 10,000 ppm",
      dosagePerLiter: "10g Trichoderma viride + 5ml Cold-Pressed Neem Oil / 1L",
      organicRatePerUnit: 280, // Rs/kg bio-agent
      organicPerLiterGrams: 10,
      neemOilRequired: true,
      neemOilMlPerLiter: 5.0,
      instructions: [
        "Emulsify cold-pressed neem oil in water using 2ml soap nut extract or mild organic surfactant.",
        "Mix fresh Trichoderma viride culture into the tank immediately before spraying.",
        "Apply during morning or late afternoon to prevent sunlight UV degradation of fungal spores.",
        "Apply 2kg Trichoderma-enriched farmyard manure (FYM) around each palm root basin."
      ],
      withholdingDays: 0,
      applicationNote: "Preventive application during May pre-monsoon showers builds a protective biological biofilm."
    },
    fertilizerCorrection: {
      soilTreatment: "Incorporate 2kg Trichoderma-enriched neem cake and 15kg FYM per palm basin.",
      micronutrientAddon: "Avoid excessive Nitrogen during high rainfall; maintain adequate Potash (140g K₂O) for rind toughness."
    }
  },
  anthracnose: {
    name: "Anthracnose / Inflorescence Dieback",
    scientificName: "Colletotrichum gloeosporioides",
    category: "fungal",
    chemicalStandard: {
      title: "Copper Oxychloride 50% WP / 1% Neutral Bordeaux Mixture",
      activeIngredient: "Copper Oxychloride 50% WP (2.5g/L) or 1% Bordeaux Mixture",
      commercialExample: "Copper Oxychloride 50 WP / Neutral Bordeaux Mixture",
      dosagePerLiter: "2.5g Copper Oxychloride / 1L water",
      chemicalRatePerUnit: 420, // Rs/kg
      chemicalPerLiterGrams: 2.5,
      stickerRequired: true,
      stickerMlPerLiter: 0.5,
      instructions: [
        "Make a smooth slurry of Copper Oxychloride 50 WP with water before adding into the spray tank.",
        "Spray thoroughly over emerging female flowers and immature button bunches.",
        "Repeat after 20–25 days if humid overcast conditions persist."
      ],
      withholdingDays: 10,
      applicationNote: "First spray when female flowers open; second spray 20 days later at button set."
    },
    organicStandard: {
      title: "Pseudomonas fluorescens + Neem Seed Kernel Extract (NSKE 5%)",
      activeBioAgent: "Pseudomonas fluorescens (min 1x10⁸ CFU/ml)",
      dosagePerLiter: "10g Pseudomonas fluorescens + 50ml NSKE 5% / 1L",
      organicRatePerUnit: 260,
      organicPerLiterGrams: 10,
      neemOilRequired: true,
      neemOilMlPerLiter: 4.0,
      instructions: [
        "Spray enriched bio-consortium covering inflorescence rachis and foliage.",
        "Apply at earliest sign of brown water-soaked lesions on flowers or fronds."
      ],
      withholdingDays: 0,
      applicationNote: "Safe for pollinators; apply in late afternoon when honeybee activity subsides."
    },
    fertilizerCorrection: {
      soilTreatment: "Apply balanced NPK (100:40:140g) and avoid waterlogging around roots.",
      micronutrientAddon: "Foliar spray with Solubor (0.1% = 1g/L) during flowering to reduce button shedding."
    }
  },
  bud_borer: {
    name: "Bud Borer / Inflorescence Caterpillar",
    scientificName: "Allocasis arecae / Batrachedra amydraula",
    category: "pest",
    isChemicalBlocked: true,
    blockedReason: "Synthetic chemical crown spraying (Chlorpyrifos) is restricted under Gazette S.O. 4294(E) and lacks approved CIBRC label claims for arecanut crown drenching. ICAR-CPCRI recommends cultural crown clearance and neem cake + sand dusting (1:1).",
    chemicalStandard: {
      title: "Synthetic Insecticide Blocked (S.O. 4294(E))",
      activeIngredient: "None approved for crown drenching",
      commercialExample: "Chemical spraying unapproved",
      dosagePerLiter: "0 (Chemical Blocked)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Chemical treatment not shown: No approved CIBRC crop-specific chemical label claim exists for this condition on arecanut.",
        "Chlorpyrifos crown spraying is legally restricted under Gazette Notification S.O. 4294(E).",
        "Clean crown: remove dried leaf sheaths, frass, and dead matter from the crown axils.",
        "Dust crown axils with a 1:1 mixture of powdered neem cake and coarse river sand (250g/palm)."
      ],
      withholdingDays: 0,
      applicationNote: "Mechanical sanitation and neem cake dusting prevent caterpillar spindle boring safely without synthetic pesticides."
    },
    organicStandard: {
      title: "Beauveria bassiana Bio-Insecticide + Crown Neem Cake Dusting",
      activeBioAgent: "Beauveria bassiana entomopathogenic fungus (min 1x10⁸ CFU/g)",
      dosagePerLiter: "10g Beauveria bassiana + 5ml Neem Oil / 1L",
      organicRatePerUnit: 320,
      organicPerLiterGrams: 10,
      neemOilRequired: true,
      neemOilMlPerLiter: 5.0,
      instructions: [
        "Mix Beauveria bassiana powder in water with cold-pressed neem oil.",
        "Drench the central crown spindle and young leaf axils.",
        "Dust crown with a 1:1 mixture of powdered neem cake and coarse river sand (250g/palm)."
      ],
      withholdingDays: 0,
      applicationNote: "White muscardine spores infect and mummify caterpillars inside boreholes."
    },
    fertilizerCorrection: {
      soilTreatment: "Apply 2kg neem cake per palm basin to deter subterranean pupation.",
      micronutrientAddon: "Apply Zinc Sulphate (50g/palm) to accelerate vigorous new spindle formation."
    }
  },
  spindle_bug: {
    name: "Spindle Bug",
    scientificName: "Carvalhoia arecae",
    category: "pest",
    isChemicalBlocked: true,
    blockedReason: "Synthetic chemical insecticides (Thiamethoxam, Dimethoate) lack approved CIBRC major use label claims on arecanut. Use biological or cultural vector management.",
    chemicalStandard: {
      title: "Synthetic Insecticide Blocked (No CIBRC Label Claim)",
      activeIngredient: "None approved on arecanut",
      commercialExample: "Chemical spraying unapproved",
      dosagePerLiter: "0 (Chemical Blocked)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Chemical treatment not shown: Dimethoate and Thiamethoxam lack verified CIBRC Major Uses label claims for arecanut.",
        "Direct bio-organic sprays into the innermost funnel of the unopened spindle leaf."
      ],
      withholdingDays: 0,
      applicationNote: "Use organic bio-control to manage spindle bugs without unapproved chemicals."
    },
    organicStandard: {
      title: "Verticillium lecanii + Cold-Pressed Neem Oil",
      activeBioAgent: "Verticillium lecanii (Lecanicillium lecanii) + Neem extract",
      dosagePerLiter: "10g Verticillium lecanii + 5ml Neem Oil / 1L",
      organicRatePerUnit: 340,
      organicPerLiterGrams: 10,
      neemOilRequired: true,
      neemOilMlPerLiter: 5.0,
      instructions: [
        "Spray directly into spindle crevices in the evening.",
        "Ensure thorough wetting of young uncurled frond sheaths."
      ],
      withholdingDays: 0,
      applicationNote: "Bio-fungus colonizes and paralyses sap-sucking nymphs."
    },
    fertilizerCorrection: {
      soilTreatment: "Apply 12kg FYM and 500g Dolomite per palm basin.",
      micronutrientAddon: "Foliar mist with 0.5% micronutrient complex to rebuild chlorotic leaf tissue."
    }
  },
  white_mite: {
    name: "White Mites / Red Palm Mite",
    scientificName: "Raoiella indica / Oligonychus indicus",
    category: "pest",
    isChemicalBlocked: true,
    blockedReason: "Synthetic chemical acaricides (Fenazaquin, Spiromesifen) lack verified CIBRC major use registrations on arecanut. Use Fish Oil Rosin Soap (FORS 20g/L).",
    chemicalStandard: {
      title: "Synthetic Acaricide Blocked (No CIBRC Label Claim)",
      activeIngredient: "None approved on arecanut",
      commercialExample: "Chemical spraying unapproved",
      dosagePerLiter: "0 (Chemical Blocked)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Chemical treatment not shown: Fenazaquin and synthetic acaricides lack approved CIBRC Major Uses registrations for arecanut.",
        "Use potassium salt surfactant (Fish Oil Rosin Soap) under fronds to suffocate mite colonies safely."
      ],
      withholdingDays: 0,
      applicationNote: "Use certified botanical soap sprays."
    },
    organicStandard: {
      title: "Fish Oil Rosin Soap (FORS) / Pongamia (Honge) Oil Soap",
      activeBioAgent: "Fish Oil Rosin Soap (FORS) potassium salt formulation",
      dosagePerLiter: "20g FORS / 1L water",
      organicRatePerUnit: 190,
      organicPerLiterGrams: 20,
      neemOilRequired: false,
      neemOilMlPerLiter: 0,
      instructions: [
        "Dissolve FORS in lukewarm water until completely dissolved.",
        "High pressure spray under fronds suffocates mite eggs, nymphs, and adults."
      ],
      withholdingDays: 0,
      applicationNote: "Safe for natural predatory coccinellid beetles."
    },
    fertilizerCorrection: {
      soilTreatment: "Provide regular summer basin irrigation; water stress triggers mite proliferation.",
      micronutrientAddon: "Apply Potassium (MOP 235g/palm) to fortify cuticle thickness against piercing stylets."
    }
  },
  root_grub: {
    name: "Root Grub / White Grub",
    scientificName: "Leucopholis burmeisteri",
    category: "pest",
    isChemicalBlocked: true,
    blockedReason: "Chlorpyrifos soil drenching is restricted and lacks approved CIBRC major use label claims for arecanut root basins. Use Metarhizium anisopliae bio-enriched FYM.",
    chemicalStandard: {
      title: "Synthetic Pesticide Drenching Blocked (S.O. 4294(E))",
      activeIngredient: "None approved for root basin drenching",
      commercialExample: "Chemical drenching unapproved",
      dosagePerLiter: "0 (Chemical Blocked)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Chemical treatment not shown: Chlorpyrifos soil drenching is subject to regulatory restrictions under S.O. 4294(E) and lacks approved CIBRC label claims on arecanut.",
        "Use entomopathogenic green muscardine fungus (Metarhizium anisopliae) in farmyard manure."
      ],
      withholdingDays: 0,
      applicationNote: "Use biological grub suppression."
    },
    organicStandard: {
      title: "Metarhizium anisopliae (Green Muscardine Fungus) Soil Incorporation",
      activeBioAgent: "Metarhizium anisopliae (min 1x10⁸ CFU/g)",
      dosagePerLiter: "50g Metarhizium per palm incorporated into 5kg Farmyard Manure",
      organicRatePerUnit: 320,
      organicPerLiterGrams: 50,
      neemOilRequired: false,
      neemOilMlPerLiter: 0,
      instructions: [
        "Mix 1kg Metarhizium anisopliae in 100kg moist FYM/compost and incubate under shade for 15 days.",
        "Apply 5kg of this bio-enriched compost around each palm basin during August–September.",
        "Maintain soil moisture for rapid fungal proliferation and grub cuticle penetration."
      ],
      withholdingDays: 0,
      applicationNote: "Entomopathogenic fungus provides season-long natural biological suppression."
    },
    fertilizerCorrection: {
      soilTreatment: "Apply 2kg neem cake and 15kg FYM per palm basin to stimulate new feeder root regeneration.",
      micronutrientAddon: "Apply Single Super Phosphate (SSP 250g) for rapid root rootlet branching."
    }
  },
  stem_bleeding: {
    name: "Stem Bleeding Disease",
    scientificName: "Thielaviopsis paradoxa",
    category: "fungal",
    isChemicalBlocked: true,
    blockedReason: "Topical chemical wound dressings (Bordeaux paste concentration and wound sealants) are subject to conflicting documentation and lack approved statutory CIBRC wound-painting label claims. Obsolete hot coal tar and banned Tridemorph (S.O. 3951(E)) are strictly prohibited. Surgical excision of decayed bark to healthy wood and collection/burning of diseased wood shavings are supported. Consult your local KVK for regional wound-dressing protocols.",
    chemicalStandard: {
      title: "Chemical Dressing Under Review / Conflicting (Bordeaux Paste / Coal Tar)",
      activeIngredient: "Chemical wound dressings under review",
      commercialExample: "Topical chemical dressing withheld",
      dosagePerLiter: "0 (Actionable Chemical Withheld)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      requiresLime: false,
      limeRatePerKg: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Actionable chemical dressing not shown: Bordeaux paste concentrations conflict in literature (5% vs 10%) and lack approved CIBRC wound-painting label claims.",
        "Tridemorph (Calixin) is banned in India under Gazette Notification S.O. 3951(E).",
        "Hot coal tar is an unapproved, carcinogenic petroleum byproduct that causes thermal cambium burn and is prohibited.",
        "Chisel out infected, soft, decaying trunk tissues cleanly until fresh yellowish healthy wood is visible.",
        "Burn or deeply bury all chiseled diseased wood shavings outside the garden to prevent spore dispersal.",
        "Consult your local Krishi Vigyan Kendra (KVK) or ICAR-CPCRI agronomy officer for regional wound-dressing protocols."
      ],
      withholdingDays: 0,
      applicationNote: "Surgical bark excision and wound sanitation are supported; topical chemical dressings are under review."
    },
    organicStandard: {
      title: "Trichoderma Wound Paste & Fermented Cow Dung Slurry",
      activeBioAgent: "Trichoderma viride + Fresh Cow Dung & Urine Slurry",
      dosagePerLiter: "50g Trichoderma in 1L fresh fermented cow dung slurry",
      organicRatePerUnit: 280,
      organicPerLiterGrams: 50,
      neemOilRequired: false,
      neemOilMlPerLiter: 0,
      instructions: [
        "Chisel out decayed fibrous trunk tissue.",
        "Apply thick paste of Trichoderma-enriched microbial slurry directly into the cavity.",
        "Tie gunny cloth over the wound to retain moisture and encourage fungal antagonistic colonization."
      ],
      withholdingDays: 0,
      applicationNote: "Bio-antagonist outcompetes pathogenic Thielaviopsis spores inside wood."
    },
    fertilizerCorrection: {
      soilTreatment: "Apply 500g Dolomite / Agricultural Lime per palm to correct soil acidity.",
      micronutrientAddon: "Apply 15–20g Borax (conditional on boron deficiency) and 100g MgSO₄ to support palm recovery and vigor."
    }
  },
  yellow_leaf: {
    name: "Yellow Leaf Disease (YLD)",
    scientificName: "Candidatus Phytoplasma arecae",
    category: "phytoplasma",
    isChemicalBlocked: true,
    blockedReason: "Yellow Leaf Disease is caused by a systemic phytoplasma (wall-less bacterium). Chemical fungicides have ZERO biological efficacy and are strictly prohibited. Neonicotinoids lack approved CIBRC label claims. Practice balanced NPK + MgSO4 + ZnSO4 supportive nutrient fortification (NOT A CURE).",
    chemicalStandard: {
      title: "Chemical Fungicides Strictly Prohibited (Zero Efficacy — Nutrition is Supportive Only, Not a Cure)",
      activeIngredient: "None (Phytoplasma lacks cell walls)",
      commercialExample: "Fungicides prohibited",
      dosagePerLiter: "0 (Fungicides Blocked)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Chemical treatment not shown: Fungicides have ZERO effect against phytoplasmas and must NOT be sprayed.",
        "Imidacloprid lacks approved CIBRC label claims on arecanut.",
        "Soil basin application: 50g Zinc Sulphate, 100g Magnesium Sulphate, and balanced NPK per palm annually (supportive vigor maintenance only — NOT A CURE for systemic phytoplasma).",
        "Apply 15kg green manure / farmyard manure and 2kg neem cake per palm basin.",
        "Severely affected palms showing advanced crown choking should be rogued to prevent epidemic spread."
      ],
      withholdingDays: 0,
      applicationNote: "Nutrient management maintains palm vigor; fungicides are scientifically invalid and blocked. Nutrition does NOT cure the phytoplasma."
    },
    organicStandard: {
      title: "Bio-Consortium Soil Drench + Neem Oil Repellent",
      activeBioAgent: "Arbuscular Mycorrhizal Fungi (AMF) + Pseudomonas + 5ml/L Neem Oil",
      dosagePerLiter: "100g AMF/palm + 10g Pseudomonas/L + 5ml Neem Oil/L",
      organicRatePerUnit: 350,
      organicPerLiterGrams: 5,
      neemOilRequired: true,
      neemOilMlPerLiter: 5.0,
      instructions: [
        "Apply 10kg green manure and 5kg neem cake enriched compost to each palm basin.",
        "Inoculate root zone with Glomus intraradices mycorrhizal fungi to bolster nutrient assimilation.",
        "Regular neem foliar mists to repel plant hoppers."
      ],
      withholdingDays: 0,
      applicationNote: "Enhances root surface absorption and disease tolerance."
    },
    fertilizerCorrection: {
      soilTreatment: "Heavy organic manuring: 20kg FYM + 2kg neem cake + 100g AMF per palm.",
      micronutrientAddon: "Supportive vigor supplement (NOT A CURE): 50g ZnSO₄ + 100g MgSO₄ per palm along with balanced NPK + FYM."
    }
  },
  nut_cracking: {
    name: "Nut Cracking & Splitting Disorder",
    scientificName: "Physiological Boron/Potash Deficiency & Moisture Stress",
    category: "physiological",
    chemicalStandard: {
      title: "Borax Soil Supplement + Solubor Foliar Spray + Potash Booster",
      activeIngredient: "Di-sodium octaborate tetrahydrate (Solubor) + Borax + MOP",
      commercialExample: "Commercial Borax (10.5% B) / Solubor (20% B) / Muriate of Potash (60% K₂O)",
      dosagePerLiter: "1.0g Solubor / 1L foliar + 25g Borax & 200g MOP per palm soil basin",
      chemicalRatePerUnit: 160, // Rs/kg Borax
      chemicalPerLiterGrams: 1.0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Apply 25g Borax and 200g Muriate of Potash per palm to the root basin during post-monsoon (Sep–Oct).",
        "Spray 0.1% Solubor (1g/L water) onto tender developing nut bunches during button stage in summer.",
        "Maintain regular, uninterrupted irrigation during dry summer spells (avoid abrupt heavy watering after drought).",
        "Mulch palm basin with dry arecanut leaves or coir pith to conserve uniform soil moisture."
      ],
      withholdingDays: 0,
      applicationNote: "Nut splitting is triggered by sudden cell wall expansion due to boron deficiency and erratic moisture."
    },
    organicStandard: {
      title: "Wood Ash & Compost Soil Amendment + Biomass Mulching",
      activeBioAgent: "Hardwood Ash (Potash/Micronutrient rich) + Vermicompost + Raw Borax Mineral",
      dosagePerLiter: "2kg Wood Ash + 15kg Vermicompost + 25g Borax per palm basin",
      organicRatePerUnit: 220,
      organicPerLiterGrams: 25,
      neemOilRequired: false,
      neemOilMlPerLiter: 0,
      instructions: [
        "Spread 2kg wood ash and 15kg vermicompost evenly in a 1-meter circular ring around the palm.",
        "Mulch basin heavily with 15cm thick layer of green leaves and arecanut fronds.",
        "Provide weekly basin watering to keep root zone consistently moist."
      ],
      withholdingDays: 0,
      applicationNote: "Organic mulch buffers soil against temperature and moisture extremes."
    },
    fertilizerCorrection: {
      soilTreatment: "Ensure full 235g MOP (Potash) and mulch heavily to stabilize soil moisture.",
      micronutrientAddon: "Mandatory: 25g Borax per palm in soil + 0.1% Solubor spray on nut bunches."
    }
  },
  leaf_spot: {
    name: "Leaf Spot Complex",
    scientificName: "Phyllosticta arecae / Colletotrichum",
    category: "fungal",
    isChemicalBlocked: true,
    blockedReason: "Systemic triazoles (Hexaconazole, Carbendazim, Saaf) lack approved CIBRC Major Uses registrations for arecanut foliar blight. Use protective 1% Bordeaux mixture or Copper Oxychloride 50 WP (2.5g/L) or sanitary frond pruning.",
    chemicalStandard: {
      title: "Systemic Triazoles Blocked (Unverified Label Claims)",
      activeIngredient: "Systemic triazoles withheld",
      commercialExample: "Contaf / Saaf unverified on areca",
      dosagePerLiter: "0 (Systemic Triazoles Blocked)",
      chemicalRatePerUnit: 0,
      chemicalPerLiterGrams: 0,
      stickerRequired: false,
      stickerMlPerLiter: 0,
      instructions: [
        "Chemical treatment not shown: Systemic triazole fungicides lack approved CIBRC Major Uses registrations on arecanut.",
        "Spray protective 1% Bordeaux mixture or Copper Oxychloride 50 WP (2.5g/L) during early post-monsoon onset.",
        "Prune severely spotted lower drooping fronds and burn them to reduce inoculum.",
        "Thin overhanging shade trees to ensure good sunlight penetration through the orchard."
      ],
      withholdingDays: 0,
      applicationNote: "Use protective copper sprays or cultural pruning instead of unverified systemic triazoles."
    },
    organicStandard: {
      title: "Pseudomonas fluorescens + Neem Foliar Spray",
      activeBioAgent: "Pseudomonas fluorescens (min 1x10⁸ CFU/g)",
      dosagePerLiter: "10g Pseudomonas fluorescens + 4ml Neem Oil / 1L",
      organicRatePerUnit: 260,
      organicPerLiterGrams: 10,
      neemOilRequired: true,
      neemOilMlPerLiter: 4.0,
      instructions: [
        "Spray foliage at the first appearance of brown water-soaked circular leaf spots.",
        "Incorporate 2kg neem cake per palm basin."
      ],
      withholdingDays: 0,
      applicationNote: "Strengthens systemic acquired resistance in palm fronds."
    },
    fertilizerCorrection: {
      soilTreatment: "Maintain regular drainage; avoid stagnant surface water.",
      micronutrientAddon: "Apply Magnesium Sulphate (100g/palm) to restore lost chlorophyll."
    }
  },
  maintenance: {
    name: "Monsoon Prophylactic Shield (Seasonal Preventive)",
    scientificName: "ICAR-CPCRI Pre-Monsoon Preventive Protocol",
    category: "fungal",
    chemicalStandard: {
      title: "1% Prophylactic Bordeaux Mixture Canopy Cover",
      activeIngredient: "Copper Sulphate (10g) + Quicklime (10g) per 1L + Rosin-Soda Sticker",
      commercialExample: "Technical Grade CuSO₄ + High Calcium CaO",
      dosagePerLiter: "10g CuSO₄ + 10g Lime + 1ml Sticker / 1L",
      chemicalRatePerUnit: 240,
      chemicalPerLiterGrams: 10,
      requiresLime: true,
      limeRatePerKg: 35,
      stickerRequired: true,
      stickerMlPerLiter: 1.0,
      instructions: [
        "Apply 1st spray in May/early June immediately prior to southwest monsoon onset.",
        "Target bunches, rachis, and inner leaf whorls thoroughly with mist sprayer.",
        "Apply 2nd spray 40–45 days later during any mid-monsoon rain break."
      ],
      withholdingDays: 14,
      applicationNote: "Essential preventive shield protecting entire annual crop from Koleroga."
    },
    organicStandard: {
      title: "Bio-Prophylactic Microbial Canopy Shield",
      activeBioAgent: "Pseudomonas + Trichoderma + Cold-Pressed Neem Oil (5ml/L)",
      dosagePerLiter: "10g Bio-mix + 5ml Neem Oil / 1L",
      organicRatePerUnit: 280,
      organicPerLiterGrams: 10,
      neemOilRequired: true,
      neemOilMlPerLiter: 5.0,
      instructions: [
        "Spray entire canopy during pre-monsoon showers to establish antagonistic biofilm.",
        "Apply 5kg neem cake per palm basin to suppress soil-borne fungal inoculum."
      ],
      withholdingDays: 0,
      applicationNote: "Pre-monsoon biological barrier against fungal spores."
    },
    fertilizerCorrection: {
      soilTreatment: "Full annual ICAR-CPCRI NPK schedule (100:40:140g) + 12kg FYM.",
      micronutrientAddon: "Soil balance: Borax 25g + MgSO₄ 100g + ZnSO₄ 50g per palm annually."
    }
  }
}

// ---------------------------------------------------------------------------
// Component Implementation
// ---------------------------------------------------------------------------

export default function TreatmentCalculatorModal({
  isOpen,
  onClose,
  initialDisease = "koleroga",
  initialPalms = 500,
  initialMode = "pesticides",
}: TreatmentCalculatorProps) {
  // Normalize initial disease string
  const cleanInitialKey = useMemo(() => {
    const s = initialDisease.toLowerCase()
    if (s.includes("kole") || s.includes("rot")) return "koleroga"
    if (s.includes("anthrac")) return "anthracnose"
    if (s.includes("bud") || s.includes("borer")) return "bud_borer"
    if (s.includes("spindle") || s.includes("bug")) return "spindle_bug"
    if (s.includes("mite")) return "white_mite"
    if (s.includes("grub")) return "root_grub"
    if (s.includes("bleed")) return "stem_bleeding"
    if (s.includes("yellow") || s.includes("yld")) return "yellow_leaf"
    if (s.includes("crack") || s.includes("split")) return "nut_cracking"
    if (s.includes("spot")) return "leaf_spot"
    return "koleroga"
  }, [initialDisease])

  const [activeTab, setActiveTab] = useState<"pesticides" | "fertilizers">(initialMode)
  const [selectedDisease, setSelectedDisease] = useState<string>(cleanInitialKey)
  const [palms, setPalms] = useState<number>(initialPalms)
  const [acres, setAcres] = useState<number>(Math.round((initialPalms / 535) * 10) / 10 || 1.0)
  const [applicationMethod, setApplicationMethod] = useState<"manual" | "drone">("manual")
  const [protocol, setProtocol] = useState<"chemical" | "organic">("chemical")

  // Fertilizer specific state
  const [palmAge, setPalmAge] = useState<"mature" | "year3" | "year2" | "year1">("mature")
  const [includeBorax, setIncludeBorax] = useState(true)
  const [includeMg, setIncludeMg] = useState(true)
  const [includeZinc, setIncludeZinc] = useState(true)
  const [includeLime, setIncludeLime] = useState(false) // Acidic soil correction

  if (!isOpen) return null

  const prescription = AGRONOMIC_PRESCRIPTIONS[selectedDisease] || AGRONOMIC_PRESCRIPTIONS.koleroga

  // Handle Synchronized Inputs (Standard planting density ~535 palms/acre in Karnataka / Kerala)
  const handlePalmsChange = (val: number) => {
    const p = Math.max(1, val)
    setPalms(p)
    setAcres(Math.round((p / 535) * 10) / 10)
  }

  const handleAcresChange = (val: number) => {
    const a = Math.max(0.1, val)
    setAcres(a)
    setPalms(Math.round(a * 535))
  }

  // --- Calculations for Pesticides / Sprays ---
  // Spray volume required
  // Manual tree climber / power foot sprayer: ~2.5 Litres per mature palm canopy
  // Drone ULV spraying: ~50 Litres total per acre
  const totalWaterLiters = Math.round(
    applicationMethod === "manual" ? palms * 2.5 : acres * 50
  )

  const chemPlan = prescription.chemicalStandard
  const orgPlan = prescription.organicStandard
  const activePlan = protocol === "chemical" ? chemPlan : orgPlan

  const isChemicalBlocked = !!prescription.isChemicalBlocked && protocol === "chemical"

  // Chemical calculation
  const primaryQuantityKg = isChemicalBlocked
    ? 0
    : protocol === "chemical"
      ? (totalWaterLiters * chemPlan.chemicalPerLiterGrams) / 1000
      : (totalWaterLiters * orgPlan.organicPerLiterGrams) / 1000

  const limeQuantityKg =
    !isChemicalBlocked && protocol === "chemical" && chemPlan.requiresLime ? primaryQuantityKg : 0

  const stickerLiters =
    !isChemicalBlocked && protocol === "chemical" && chemPlan.stickerRequired
      ? (totalWaterLiters * chemPlan.stickerMlPerLiter) / 1000
      : 0

  const neemOilLiters =
    protocol === "organic" && orgPlan.neemOilRequired
      ? (totalWaterLiters * orgPlan.neemOilMlPerLiter) / 1000
      : 0

  // Cost estimates in INR
  const primaryCost = isChemicalBlocked
    ? 0
    : protocol === "chemical"
      ? Math.round(primaryQuantityKg * chemPlan.chemicalRatePerUnit)
      : Math.round(primaryQuantityKg * orgPlan.organicRatePerUnit)

  const limeCost =
    !isChemicalBlocked && protocol === "chemical" && chemPlan.requiresLime
      ? Math.round(limeQuantityKg * (chemPlan.limeRatePerKg || 35))
      : 0

  const stickerCost = isChemicalBlocked ? 0 : Math.round(stickerLiters * 180) // Rs 180 / L sticker
  const neemOilCost = Math.round(neemOilLiters * 380) // Rs 380 / L cold pressed neem oil

  const totalMaterialCost = isChemicalBlocked ? 0 : (primaryCost + limeCost + stickerCost + neemOilCost)

  // Labor estimation:
  // Manual climber: Rs 18 per palm for canopy spraying
  // Drone spraying: Rs 650 per acre
  const laborCost = Math.round(
    applicationMethod === "manual" ? palms * 18 : acres * 650
  )

  const totalEstimatedCost = totalMaterialCost + laborCost
  const costPerPalm = Math.round((totalEstimatedCost / palms) * 10) / 10

  // --- Calculations for ICAR-CPCRI Fertilizer Program ---
  const ageFactor = {
    mature: 1.0,
    year3: 0.75,
    year2: 0.5,
    year1: 0.25,
  }[palmAge]

  // Standard recommended annual quantities per bearing palm (ICAR-CPCRI standard):
  // Urea: 220g (provides 100g N)
  // Rock Phosphate: 200g (provides 40g P2O5)
  // Muriate of Potash (MOP): 235g (provides 140g K2O)
  // FYM / Compost: 12 kg
  const ureaPerPalmGrams = 220 * ageFactor
  const rockPhosPerPalmGrams = 200 * ageFactor
  const mopPerPalmGrams = 235 * ageFactor
  const fymPerPalmKg = 12 * ageFactor

  const totalUreaKg = Math.round((palms * ureaPerPalmGrams) / 1000)
  const totalRockPhosKg = Math.round((palms * rockPhosPerPalmGrams) / 1000)
  const totalMopKg = Math.round((palms * mopPerPalmGrams) / 1000)
  const totalFymTons = Math.round(((palms * fymPerPalmKg) / 1000) * 10) / 10

  // 50kg bags count
  const ureaBags = Math.ceil(totalUreaKg / 50)
  const rockPhosBags = Math.ceil(totalRockPhosKg / 50)
  const mopBags = Math.ceil(totalMopKg / 50)

  // Micronutrients
  const boraxKg = includeBorax ? Math.round((palms * 25) / 1000) : 0
  const mgKg = includeMg ? Math.round((palms * 100) / 1000) : 0
  const zincKg = includeZinc ? Math.round((palms * 50) / 1000) : 0
  const limeDolomiteKg = includeLime ? Math.round((palms * 500) / 1000) : 0

  // Fertilizer Commercial Costs (INR):
  // Subsidized Urea: ~Rs 270 / 50kg bag (Rs 5.4/kg)
  // Rock Phosphate: ~Rs 450 / 50kg bag (Rs 9/kg)
  // MOP: ~Rs 1,700 / 50kg bag (Rs 34/kg)
  // FYM: ~Rs 3,000 per tractor load (approx 3 tons = Rs 1,000/ton)
  // Borax: Rs 160/kg
  // MgSO4: Rs 35/kg
  // ZnSO4: Rs 85/kg
  // Dolomite: Rs 12/kg
  const ureaCost = Math.round(totalUreaKg * 5.4)
  const rockPhosCost = Math.round(totalRockPhosKg * 9.0)
  const mopCost = Math.round(totalMopKg * 34.0)
  const fymCost = Math.round(totalFymTons * 1000)
  const boraxCost = Math.round(boraxKg * 160)
  const mgCost = Math.round(mgKg * 35)
  const zincCost = Math.round(zincKg * 85)
  const limeCostFert = Math.round(limeDolomiteKg * 12)

  const totalFertilizerInvestment =
    ureaCost + rockPhosCost + mopCost + fymCost + boraxCost + mgCost + zincCost + limeCostFert
  const fertilizerCostPerPalm = Math.round((totalFertilizerInvestment / palms) * 10) / 10

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/60 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden my-auto max-h-[92vh] flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-border/80 flex items-center justify-between bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary">
              <Calculator size={20} />
            </div>
            <div>
              <h3 className="font-bold text-base text-foreground flex items-center gap-2">
                ICAR-CPCRI Fertilizer & Pesticide Hub
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                  Verified Agronomy
                </span>
              </h3>
              <p className="text-xs text-muted-foreground">
                Scientific dosages, commercial mixing rates, and economic planning for Arecanut
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Toggle Bar */}
        <div className="px-6 pt-3 pb-0 border-b border-border bg-card flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("pesticides")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all ${
              activeTab === "pesticides"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <ShieldCheck size={15} />
            <span>Pesticides & Fungicide Sprays</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("fertilizers")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all ${
              activeTab === "fertilizers"
                ? "border-emerald-600 text-emerald-600"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sprout size={15} />
            <span>Annual Fertilizer & Nutrition Program</span>
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Universal Estate Scale Bar */}
          <div className="p-4 rounded-xl bg-muted/30 border border-border/80 grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground mb-1">
                Number of Palms to Treat:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={10}
                  max={50000}
                  step={50}
                  value={palms}
                  onChange={(e) => handlePalmsChange(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-1.5 rounded-lg bg-card border border-border text-foreground font-mono font-bold text-sm"
                />
                <span className="text-xs text-muted-foreground shrink-0 font-medium">Palms</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground mb-1">
                Estimated Orchard Area:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min={0.1}
                  max={100}
                  step={0.5}
                  value={acres}
                  onChange={(e) => handleAcresChange(parseFloat(e.target.value) || 0.1)}
                  className="w-full px-3 py-1.5 rounded-lg bg-card border border-border text-foreground font-mono font-bold text-sm"
                />
                <span className="text-xs text-muted-foreground shrink-0 font-medium">Acres (~535 palms/ac)</span>
              </div>
            </div>
          </div>

          {/* TAB 1: PESTICIDES & DISEASE MANAGEMENT */}
          {activeTab === "pesticides" && (
            <div className="space-y-6">
              {/* Disease Selector & Protocol */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-foreground mb-1.5 uppercase tracking-wider">
                    Select Diagnosed Pathology / Pest
                  </label>
                  <select
                    value={selectedDisease}
                    onChange={(e) => setSelectedDisease(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-background border border-border text-foreground font-semibold text-xs focus:outline-none focus:ring-2 focus:ring-primary/40"
                  >
                    <option value="koleroga">Fruit Rot / Koleroga (1% Bordeaux Mixture - Official)</option>
                    <option value="anthracnose">Anthracnose / Inflorescence Dieback (Copper Oxychloride / Bordeaux - Official)</option>
                    <option value="stem_bleeding">Stem Bleeding (Surgical Sanitation - Review Required)</option>
                    <option value="nut_cracking">Nut Cracking Disorder (Borax Soil Application - Official)</option>
                    <option value="maintenance">Monsoon Prophylactic Shield (1% Bordeaux Canopy Spray - Official)</option>
                    <option value="bud_borer">Bud Borer / Caterpillar (Cultural Neem Dusting Only - Chemical Blocked)</option>
                    <option value="yellow_leaf">Yellow Leaf Disease (Nutrient Fortification - Fungicides Blocked)</option>
                    <option value="leaf_spot">Leaf Spot Complex (Cultural Sanitation - Systemic Triazoles Blocked)</option>
                    <option value="spindle_bug">Spindle Bug (Bio-Control Only - Chemical Blocked)</option>
                    <option value="white_mite">White Mites (FORS Bio-Soap Only - Chemical Blocked)</option>
                    <option value="root_grub">Root Grub (Metarhizium Bio-Control - Chemical Blocked)</option>
                  </select>
                </div>

                {/* Protocol Choice: Chemical vs Organic */}
                <div>
                  <label className="block text-xs font-bold text-foreground mb-1.5 uppercase tracking-wider">
                    Treatment Formulation Approach
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setProtocol("chemical")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl border text-xs font-bold transition-all ${
                        protocol === "chemical"
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-background text-muted-foreground border-border hover:bg-muted/40"
                      }`}
                    >
                      <ShieldCheck size={14} />
                      <span>Standard Chemical</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setProtocol("organic")}
                      className={`flex items-center justify-center gap-2 py-2 px-3 rounded-xl border text-xs font-bold transition-all ${
                        protocol === "organic"
                          ? "bg-emerald-700 text-white border-emerald-700"
                          : "bg-background text-muted-foreground border-border hover:bg-muted/40"
                      }`}
                    >
                      <Sprout size={14} />
                      <span>Certified Bio-Organic</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Chemical Blocked Warning Notice */}
              {isChemicalBlocked && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-3">
                  <AlertTriangle className="shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" size={18} />
                  <div>
                    <span className="font-bold block text-xs uppercase tracking-wide">Chemical Treatment Blocked / Unverified</span>
                    <p className="mt-1">{prescription.blockedReason}</p>
                    <p className="mt-1 font-semibold text-[11px]">
                      Synthetic chemical dosage calculations are zeroed out for farmer safety. Switch to "Certified Bio-Organic" above or consult your local Krishi Vigyan Kendra (KVK) extension officer.
                    </p>
                  </div>
                </div>
              )}

              {/* Application Technique Selection */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-card border border-border">
                <span className="text-xs font-semibold text-foreground">Spraying Application Method:</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setApplicationMethod("manual")}
                    className={`py-1.5 px-3 text-xs font-bold rounded-lg border flex items-center gap-1.5 ${
                      applicationMethod === "manual"
                        ? "bg-primary/10 border-primary text-primary"
                        : "bg-transparent border-border text-muted-foreground"
                    }`}
                  >
                    <Droplets size={13} />
                    <span>Manual Climber / Power Sprayer (2.5 L/palm)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setApplicationMethod("drone")}
                    className={`py-1.5 px-3 text-xs font-bold rounded-lg border flex items-center gap-1.5 ${
                      applicationMethod === "drone"
                        ? "bg-primary/10 border-primary text-primary"
                        : "bg-transparent border-border text-muted-foreground"
                    }`}
                  >
                    <Plane size={13} />
                    <span>Agri Drone ULV (50 L/acre)</span>
                  </button>
                </div>
              </div>

              {/* Primary Calculated Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Spray Water Vol.</span>
                  <div className="text-xl font-extrabold font-mono text-primary mt-1">{totalWaterLiters.toLocaleString()} L</div>
                  <span className="text-[10px] text-muted-foreground">
                    {applicationMethod === "manual" ? "2.5 L / palm" : "50 L / acre"}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Active Pesticide / Fungicide</span>
                  <div className="text-xl font-extrabold font-mono text-foreground mt-1">
                    {primaryQuantityKg.toFixed(1)} {protocol === "chemical" ? "kg" : "kg bio"}
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {activePlan.dosagePerLiter}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Adjuvant / Sticker</span>
                  <div className="text-xl font-extrabold font-mono text-foreground mt-1">
                    {protocol === "chemical"
                      ? `${stickerLiters.toFixed(1)} L`
                      : `${neemOilLiters.toFixed(1)} L Oil`}
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    {protocol === "chemical" ? "Rosin-Soda sticker" : "Neem emulsifier"}
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary">Est. Spray Expense</span>
                  <div className="text-xl font-extrabold font-mono text-primary mt-1">₹{totalEstimatedCost.toLocaleString()}</div>
                  <span className="text-[10px] text-primary/80 font-medium">₹{costPerPalm} / palm treated</span>
                </div>
              </div>

              {/* Formulation Specifications */}
              <div className="p-4 rounded-xl border border-border bg-card space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-foreground border-b border-border/60 pb-2">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck size={15} className="text-primary" />
                    Prescription Specs — {activePlan.title}
                  </span>
                  <span className="text-xs text-muted-foreground font-mono">
                    {prescription.scientificName}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-muted/20">
                    <span className="text-muted-foreground block text-[11px]">Active Ingredient:</span>
                    <span className="font-semibold text-foreground">
                      {protocol === "chemical" ? chemPlan.activeIngredient : orgPlan.activeBioAgent}
                    </span>
                  </div>
                  {protocol === "chemical" && (
                    <div className="p-2.5 rounded-lg bg-muted/20">
                      <span className="text-muted-foreground block text-[11px]">Commercial Brand Examples:</span>
                      <span className="font-semibold text-foreground">{chemPlan.commercialExample}</span>
                    </div>
                  )}
                  <div className="p-2.5 rounded-lg bg-muted/20">
                    <span className="text-muted-foreground block text-[11px]">Safety Pre-Harvest Interval (PHI):</span>
                    <span className="font-semibold text-foreground">{activePlan.withholdingDays} days</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-muted/20">
                    <span className="text-muted-foreground block text-[11px]">Application Target:</span>
                    <span className="font-semibold text-foreground">{activePlan.applicationNote}</span>
                  </div>
                </div>
              </div>

              {/* Mixing Instructions & Safety */}
              <div className="p-4 rounded-xl border border-border bg-card space-y-2.5">
                <div className="flex items-center gap-2 text-xs font-bold text-foreground">
                  <Layers size={14} className="text-primary" />
                  <span>Standard Field Mixing Protocol (ICAR-CPCRI Standard)</span>
                </div>
                <ul className="text-xs text-muted-foreground space-y-1.5 list-disc list-inside">
                  {activePlan.instructions.map((ins, i) => (
                    <li key={i} className="leading-relaxed">{ins}</li>
                  ))}
                </ul>
              </div>

              {/* Fertilizer & Soil Rehabilitation Note for this disease */}
              <div className="p-3.5 rounded-xl border border-emerald-600/30 bg-emerald-600/5 space-y-1 text-xs">
                <div className="font-bold text-emerald-700 flex items-center gap-1.5">
                  <Sprout size={14} />
                  <span>Post-Infection Soil & Nutrition Rehabilitation:</span>
                </div>
                <p className="text-muted-foreground">{prescription.fertilizerCorrection.soilTreatment}</p>
                <p className="text-muted-foreground font-medium">{prescription.fertilizerCorrection.micronutrientAddon}</p>
              </div>
            </div>
          )}

          {/* TAB 2: ICAR-CPCRI FERTILIZER & NUTRITION PROGRAM */}
          {activeTab === "fertilizers" && (
            <div className="space-y-6">
              {/* Palm Age Selector */}
              <div>
                <label className="block text-xs font-bold text-foreground mb-1.5 uppercase tracking-wider">
                  Select Plantation Age Category
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { id: "mature", label: "Mature Bearing (5+ Yrs)", sub: "100% Full Dose" },
                    { id: "year3", label: "3rd–4th Year", sub: "75% Dose" },
                    { id: "year2", label: "2nd Year", sub: "50% Dose" },
                    { id: "year1", label: "1st Year (New)", sub: "25% Dose" },
                  ].map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setPalmAge(cat.id as any)}
                      className={`p-2.5 rounded-xl border text-left transition-all ${
                        palmAge === cat.id
                          ? "bg-emerald-600/10 border-emerald-600 text-emerald-800 dark:text-emerald-300 font-bold"
                          : "bg-card border-border text-muted-foreground hover:bg-muted/40"
                      }`}
                    >
                      <div className="text-xs">{cat.label}</div>
                      <div className="text-[10px] text-muted-foreground">{cat.sub}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* NPK Bag Breakdown Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Urea (46% N)</span>
                  <div className="text-xl font-extrabold font-mono text-emerald-600 mt-1">{totalUreaKg.toLocaleString()} kg</div>
                  <span className="text-[11px] font-bold text-foreground">~{ureaBags} Bags (50kg)</span>
                  <div className="text-[10px] text-muted-foreground mt-0.5">₹{ureaCost.toLocaleString()} est.</div>
                </div>

                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Rock Phosphate / SSP</span>
                  <div className="text-xl font-extrabold font-mono text-emerald-600 mt-1">{totalRockPhosKg.toLocaleString()} kg</div>
                  <span className="text-[11px] font-bold text-foreground">~{rockPhosBags} Bags (50kg)</span>
                  <div className="text-[10px] text-muted-foreground mt-0.5">₹{rockPhosCost.toLocaleString()} est.</div>
                </div>

                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Potash (MOP 60%)</span>
                  <div className="text-xl font-extrabold font-mono text-emerald-600 mt-1">{totalMopKg.toLocaleString()} kg</div>
                  <span className="text-[11px] font-bold text-foreground">~{mopBags} Bags (50kg)</span>
                  <div className="text-[10px] text-muted-foreground mt-0.5">₹{mopCost.toLocaleString()} est.</div>
                </div>

                <div className="p-3.5 rounded-xl bg-card border border-border text-center shadow-sm">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Organic Manure (FYM)</span>
                  <div className="text-xl font-extrabold font-mono text-emerald-600 mt-1">{totalFymTons} Tons</div>
                  <span className="text-[11px] font-bold text-foreground">~{Math.ceil(totalFymTons / 3)} Tractor Loads</span>
                  <div className="text-[10px] text-muted-foreground mt-0.5">₹{fymCost.toLocaleString()} est.</div>
                </div>
              </div>

              {/* Split Dose Schedule */}
              <div className="p-4 rounded-xl border border-border bg-card space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-foreground border-b border-border/60 pb-2">
                  <span className="flex items-center gap-1.5">
                    <Calendar size={14} className="text-emerald-600" />
                    Two-Split Application Schedule (ICAR-CPCRI Package of Practices)
                  </span>
                  <span className="text-[11px] text-muted-foreground font-normal">Apply in shallow circular trench 0.75m from trunk</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {/* Split 1 */}
                  <div className="p-3 rounded-xl bg-muted/20 border border-border space-y-1.5">
                    <div className="flex items-center justify-between font-bold text-foreground">
                      <span className="text-emerald-600">Split 1: Pre-Monsoon (April–May)</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-600/10 text-emerald-600 font-semibold">1/3rd Dose</span>
                    </div>
                    <p className="text-muted-foreground text-[11px]">
                      Apply along with early summer showers or under summer irrigation:
                    </p>
                    <ul className="text-muted-foreground text-[11px] space-y-1 font-mono">
                      <li>• Urea: {Math.round(totalUreaKg * 0.33)} kg (~75g / palm)</li>
                      <li>• Rock Phosphate: {Math.round(totalRockPhosKg * 0.33)} kg (~70g / palm)</li>
                      <li>• MOP (Potash): {Math.round(totalMopKg * 0.33)} kg (~80g / palm)</li>
                    </ul>
                  </div>

                  {/* Split 2 */}
                  <div className="p-3 rounded-xl bg-muted/20 border border-border space-y-1.5">
                    <div className="flex items-center justify-between font-bold text-foreground">
                      <span className="text-emerald-600">Split 2: Post-Monsoon (Sept–Oct)</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-600/10 text-emerald-600 font-semibold">2/3rd Dose + FYM</span>
                    </div>
                    <p className="text-muted-foreground text-[11px]">
                      Incorporate into circular trench after heavy monsoon rains stop:
                    </p>
                    <ul className="text-muted-foreground text-[11px] space-y-1 font-mono">
                      <li>• Urea: {Math.round(totalUreaKg * 0.67)} kg (~145g / palm)</li>
                      <li>• Rock Phosphate: {Math.round(totalRockPhosKg * 0.67)} kg (~130g / palm)</li>
                      <li>• MOP (Potash): {Math.round(totalMopKg * 0.67)} kg (~155g / palm)</li>
                      <li>• Full Farmyard Manure: {totalFymTons} Tons (~12kg / palm)</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Micronutrient & Soil Amendment Checkbox Selectors */}
              <div className="p-4 rounded-xl border border-border bg-card space-y-3">
                <div className="text-xs font-bold text-foreground border-b border-border/60 pb-2 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Sparkles size={14} className="text-emerald-600" />
                    Essential Micronutrient & Soil Correction Supplements
                  </span>
                  <span className="text-[11px] text-muted-foreground">Select required amendments</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-muted/20 cursor-pointer hover:bg-muted/30">
                    <input
                      type="checkbox"
                      checked={includeBorax}
                      onChange={(e) => setIncludeBorax(e.target.checked)}
                      className="mt-0.5 rounded border-border text-emerald-600 focus:ring-emerald-500"
                    />
                    <div>
                      <div className="font-semibold text-foreground">Borax (Boron 10.5%) — 25g/palm</div>
                      <div className="text-[11px] text-muted-foreground">
                        Prevents nut cracking, button shedding, and inflorescence choking ({boraxKg} kg = ₹{boraxCost.toLocaleString()})
                      </div>
                    </div>
                  </label>

                  <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-muted/20 cursor-pointer hover:bg-muted/30">
                    <input
                      type="checkbox"
                      checked={includeMg}
                      onChange={(e) => setIncludeMg(e.target.checked)}
                      className="mt-0.5 rounded border-border text-emerald-600 focus:ring-emerald-500"
                    />
                    <div>
                      <div className="font-semibold text-foreground">Magnesium Sulphate (MgSO₄) — 100g/palm</div>
                      <div className="text-[11px] text-muted-foreground">
                        Restores chlorotic middle whorl leaves & chlorophyll vigor ({mgKg} kg = ₹{mgCost.toLocaleString()})
                      </div>
                    </div>
                  </label>

                  <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-muted/20 cursor-pointer hover:bg-muted/30">
                    <input
                      type="checkbox"
                      checked={includeZinc}
                      onChange={(e) => setIncludeZinc(e.target.checked)}
                      className="mt-0.5 rounded border-border text-emerald-600 focus:ring-emerald-500"
                    />
                    <div>
                      <div className="font-semibold text-foreground">Zinc Sulphate (ZnSO₄) — 50g/palm</div>
                      <div className="text-[11px] text-muted-foreground">
                        Prevents crown tapering and leaf rosette deformities ({zincKg} kg = ₹{zincCost.toLocaleString()})
                      </div>
                    </div>
                  </label>

                  <label className="flex items-start gap-2.5 p-2.5 rounded-lg bg-muted/20 cursor-pointer hover:bg-muted/30">
                    <input
                      type="checkbox"
                      checked={includeLime}
                      onChange={(e) => setIncludeLime(e.target.checked)}
                      className="mt-0.5 rounded border-border text-emerald-600 focus:ring-emerald-500"
                    />
                    <div>
                      <div className="font-semibold text-foreground">Agricultural Lime / Dolomite — 500g/palm</div>
                      <div className="text-[11px] text-muted-foreground">
                        Essential for acidic laterite soils (pH &lt; 5.5) in alternate years ({limeDolomiteKg} kg = ₹{limeCostFert.toLocaleString()})
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Total Investment Summary */}
              <div className="p-4 rounded-xl bg-emerald-600/10 border border-emerald-600/20 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
                    Total Estimated Annual Nutrition Budget
                  </span>
                  <div className="text-2xl font-extrabold font-mono text-emerald-700 dark:text-emerald-300">
                    ₹{totalFertilizerInvestment.toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold text-foreground">₹{fertilizerCostPerPalm} per palm / year</div>
                  <div className="text-[10px] text-muted-foreground">Calibrated to Karnataka State Fertilizer rates</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-border bg-muted/20 flex items-center justify-between">
          <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
            <Info size={13} className="text-primary" />
            <span>Formulation conforms strictly to ICAR-CPCRI agronomic research standards</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-3.5 py-1.5 rounded-xl border border-border bg-card text-foreground font-semibold text-xs hover:bg-muted/50 flex items-center gap-1.5 transition-colors"
            >
              <Printer size={13} />
              <span>Print Prescription Sheet</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-xl bg-primary text-primary-foreground font-semibold text-xs hover:opacity-90 transition-opacity"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
