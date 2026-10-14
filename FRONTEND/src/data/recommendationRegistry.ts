/**
 * FRONTEND/src/data/recommendationRegistry.ts
 *
 * Centralized, typed, auditable recommendation registry for ArecaVision AI.
 * Mirrors backend/server/recommendation_registry.py exactly.
 * Single source of truth for all fertilizer, pesticide, fungicide, and agronomic management advice.
 *
 * Audited against:
 * 1. ICAR - Central Plantation Crops Research Institute (CPCRI)
 *    - Farmer's Corner: Crop Advice for Arecanut (https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut)
 *    - Research Achievements: Crop Protection (https://cpcri.gov.in/page/article/researchachievements_crop_protection)
 * 2. Central Insecticides Board & Registration Committee (CIBRC / PPQ&S, Ministry of Agriculture)
 *    - Major Uses of Pesticides (http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides)
 * 3. Tamil Nadu Agricultural University (TNAU) Agritech Portal - Crop Protection (Arecanut)
 */

export type VerificationStatus =
  | "VERIFIED_OFFICIAL"
  | "VERIFIED_RESEARCH_ONLY"
  | "GENERAL_NON_CHEMICAL_GUIDANCE"
  | "BLOCKED_UNVERIFIED"
  | "OUTDATED_REVIEW_REQUIRED"
  | "REVIEW_REQUIRED"

export type RecommendationCategory =
  | "CHEMICAL_FUNGICIDE"
  | "CHEMICAL_INSECTICIDE"
  | "BIO_CONTROL"
  | "CULTURAL_SANITATION"
  | "NUTRIENT_MANAGEMENT"
  | "MECHANICAL_BARRIER"

export interface RecommendationRecord {
  id: string
  targetDiseaseKey: string
  targetDiseaseDisplayName: string
  scientificName: string
  category: RecommendationCategory
  title: string
  verificationStatus: VerificationStatus
  displayEligible: boolean
  actionableChemicalAllowed: boolean
  guidanceText: string
  sourceOrganization: string
  sourceTitle: string
  sourceUrl: string
  lastReviewedDate: string
  safetyCaveats: string[]
  activeIngredient?: string
  formulation?: string
  dosagePerLiter?: string
  dosagePerPalm?: string
  applicationMethod?: string
  sprayIntervalDays?: number
  withholdingPeriodDays?: number
  verificationLimitations?: string
}

export const RECOMMENDATIONS_REGISTRY: RecommendationRecord[] = [
  {
    "id": "REC-FR-01",
    "targetDiseaseKey": "FruitRot",
    "targetDiseaseDisplayName": "Fruit Rot (Koleroga / Mahali)",
    "scientificName": "Phytophthora meadii",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "1% Neutral Bordeaux Mixture Prophylactic Canopy & Bunch Spray",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Apply first prophylactic spray thoroughly covering all nut bunches just before the onset of the South-West monsoon (late May / early June). A second spray should be applied 40\u201345 days later if rainfall persists. Always conduct the iron knife test to ensure neutrality before spraying.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Crop Advice for Arecanut: Monsoon Disease Management",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Never prepare or store Bordeaux mixture in metal containers (use plastic or earthen drums).",
      "Spray must be completed within 12 hours of preparation to prevent copper crystallization.",
      "Wear protective goggles, gloves, and face shield during canopy application."
    ],
    "activeIngredient": "Copper Sulphate (CuSO4) + Calcium Hydroxide / Quicklime (CaO) (1:1 ratio)",
    "formulation": "1% Bordeaux Mixture (10g CuSO4 + 10g Quicklime per 1L water) with Rosin-Soda Sticker",
    "dosagePerLiter": "10g CuSO4 + 10g Quicklime / 1L water",
    "dosagePerPalm": "2.0 to 2.5 Litres per mature palm canopy",
    "applicationMethod": "High-pressure canopy and bunch drench spray using gator/rocker sprayer before monsoon onset",
    "sprayIntervalDays": 45,
    "withholdingPeriodDays": 14,
    "verificationLimitations": "Prophylactic shield only; will not reverse decay on already rotted nuts."
  },
  {
    "id": "REC-FR-02",
    "targetDiseaseKey": "FruitRot",
    "targetDiseaseDisplayName": "Fruit Rot (Koleroga / Mahali)",
    "scientificName": "Phytophthora meadii",
    "category": "MECHANICAL_BARRIER",
    "title": "Polythene Bunch Covering & Fallen Nut Sanitation",
    "verificationStatus": "GENERAL_NON_CHEMICAL_GUIDANCE",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Tie clean, high-density polythene covers over maturing nut bunches prior to monsoon onset. Ensure the bottom remains open for ventilation while deflecting rain splash. Promptly collect and deeply bury or incinerate all fallen rotted nuts to eliminate the primary oospore reservoir.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "Research Achievements: Integrated Management of Koleroga in Arecanut",
    "sourceUrl": "https://cpcri.gov.in/page/article/researchachievements_crop_protection",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Ensure climber safety during manual tying at palm height.",
      "Bagging must allow bottom drainage to avoid moisture condensation inside the sleeve."
    ],
    "applicationMethod": "Manual bunch covering with 200-gauge UV-stabilized polythene bags before monsoon showers",
    "verificationLimitations": "Non-chemical cultural barrier; effective primarily when installed before first rain."
  },
  {
    "id": "REC-FR-03",
    "targetDiseaseKey": "FruitRot",
    "targetDiseaseDisplayName": "Fruit Rot (Koleroga / Mahali)",
    "scientificName": "Phytophthora meadii",
    "category": "BIO_CONTROL",
    "title": "Trichoderma harzianum Pre-Monsoon Soil Basin Inoculation",
    "verificationStatus": "VERIFIED_RESEARCH_ONLY",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Enrich 100 kg well-decomposed FYM with 1 kg Trichoderma harzianum culture under shade for 15 days. Apply 2 kg of this bio-enriched mixture around the root zone basin of each palm in May before monsoon onset.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "CPCRI Crop Protection: Biological Control of Phytophthora in Plantation Crops",
    "sourceUrl": "https://cpcri.gov.in/page/article/researchachievements_crop_protection",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Do not mix or apply Trichoderma simultaneously with chemical fungicides or copper sprays in the basin.",
      "Maintain soil moisture for bio-agent colonization."
    ],
    "activeIngredient": "Trichoderma harzianum (min 2x10^8 CFU/g)",
    "formulation": "Talc-based bio-formulation (10g/L or 2kg enriched FYM/palm)",
    "dosagePerPalm": "2 kg enriched Farmyard Manure (FYM) incorporated into basin",
    "applicationMethod": "Soil incorporation into root zone basin in May",
    "verificationLimitations": "Research-supported bio-control; cannot replace canopy fungicide during high-intensity monsoons."
  },
  {
    "id": "REC-FR-04",
    "targetDiseaseKey": "FruitRot",
    "targetDiseaseDisplayName": "Fruit Rot (Koleroga / Mahali)",
    "scientificName": "Phytophthora meadii",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "Mandipropamid / Metalaxyl Systemic Oomyceticides",
    "verificationStatus": "BLOCKED_UNVERIFIED",
    "displayEligible": false,
    "actionableChemicalAllowed": false,
    "guidanceText": "Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
    "sourceOrganization": "CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
    "sourceTitle": "Major Uses of Pesticides - Registered under the Insecticides Act, 1968",
    "sourceUrl": "http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Off-label systemic chemical application is strictly prohibited without official CIBRC label registration on arecanut.",
      "Risk of chemical residue accumulation in areca masticatory kernel."
    ],
    "verificationLimitations": "Lacks explicit, direct CIBRC label-claim registration for arecanut canopy spraying."
  },
  {
    "id": "REC-ANT-01",
    "targetDiseaseKey": "Anthracnose",
    "targetDiseaseDisplayName": "Anthracnose (Dieback & Nut Spot)",
    "scientificName": "Colletotrichum gloeosporioides",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "1% Bordeaux Mixture or Copper Oxychloride 50% WP Protective Spray",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Spray Copper Oxychloride (2.5g to 3.0g/L) or 1% Bordeaux mixture on emergent inflorescences and blighted fronds when symptoms appear. Prune and destroy dead spadices and severely spotted frond tips before spraying to optimize chemical coverage.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Package of Practices: Inflorescence Dieback and Foliar Anthracnose",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Prune blighted fronds first before spraying to eliminate sporulating source.",
      "Do not spray during peak midday solar radiation to prevent chemical leaf scorch."
    ],
    "activeIngredient": "Copper Oxychloride 50% WP or 1% Bordeaux Mixture",
    "formulation": "Copper Oxychloride 50% WP (2.5g to 3.0g / 1L water)",
    "dosagePerLiter": "2.5g to 3.0g COC per 1L water",
    "dosagePerPalm": "1.5 to 2.0 Litres per affected palm canopy",
    "applicationMethod": "Foliar canopy spray targeting blighted fronds and emergent inflorescences",
    "sprayIntervalDays": 21,
    "withholdingPeriodDays": 10,
    "verificationLimitations": "Contact protective action; requires thorough wetting of both upper and lower leaf surfaces."
  },
  {
    "id": "REC-ANT-02",
    "targetDiseaseKey": "Anthracnose",
    "targetDiseaseDisplayName": "Anthracnose (Dieback & Nut Spot)",
    "scientificName": "Colletotrichum gloeosporioides",
    "category": "CULTURAL_SANITATION",
    "title": "Sanitary Frond Pruning & Plantation Aeration",
    "verificationStatus": "GENERAL_NON_CHEMICAL_GUIDANCE",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Cut away severely infected necrotic fronds and dry spadices using disinfected pruning shears. Burn the pruned material outside the garden. Thin dense overhanging shade trees to improve sunlight penetration into the canopy and lower microclimate leaf-wetness duration.",
    "sourceOrganization": "Tamil Nadu Agricultural University (TNAU) Agritech Portal",
    "sourceTitle": "Crop Protection - Arecanut Diseases: Inflorescence Dieback & Blight",
    "sourceUrl": "https://agritech.tnau.ac.in/crop_protection/arecanut_diseases_3.html",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Disinfect cutting tools between palms using 70% alcohol or 1% sodium hypochlorite.",
      "Avoid deep wounding of tender crown green tissue."
    ],
    "applicationMethod": "Sanitary excision of necrotic rachis tips and thinning of overhanging intercrop shade",
    "verificationLimitations": "Cultural management protocol; essential companion to any fungicidal intervention."
  },
  {
    "id": "REC-ANT-03",
    "targetDiseaseKey": "Anthracnose",
    "targetDiseaseDisplayName": "Anthracnose (Dieback & Nut Spot)",
    "scientificName": "Colletotrichum gloeosporioides",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "Hexaconazole 5% EC / Carbendazim Systemic Fungicides",
    "verificationStatus": "BLOCKED_UNVERIFIED",
    "displayEligible": false,
    "actionableChemicalAllowed": false,
    "guidanceText": "Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
    "sourceOrganization": "CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
    "sourceTitle": "Major Uses of Pesticides - Registered under the Insecticides Act, 1968",
    "sourceUrl": "http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Carbendazim is under ongoing regulatory review and potential restriction in India.",
      "Off-label systemic triazole use on arecanut lacks verified MRL data."
    ],
    "verificationLimitations": "Blocked from actionable prescription pending verified CIBRC arecanut label claim."
  },
  {
    "id": "REC-NC-01",
    "targetDiseaseKey": "NutCracking",
    "targetDiseaseDisplayName": "Nut Cracking & Splitting Disorder",
    "scientificName": "Physiological moisture shock & Boron deficiency",
    "category": "NUTRIENT_MANAGEMENT",
    "title": "Soil Borax Application & Water Regulation (Not a Fungal Disease)",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Nut cracking is a physiological disorder, NOT an infectious fungal or bacterial disease. FUNGICIDES ARE COMPLETELY INEFFECTIVE AND MUST NOT BE USED. Apply 15g to 20g Borax per palm annually in the root zone along with regular irrigation. Maintain uniform basin or drip irrigation during hot summer months to avoid sudden turgor pressure surges when rains arrive.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Crop Advice: Physiological Disorders in Arecanut",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "DO NOT apply fungicides or insecticides \u2014 this is a physiological disorder.",
      "Do not exceed 25g Borax per palm to avoid boron phytotoxicity (leaf tip necrosis).",
      "Ensure uniform soil moisture; avoid prolonged drought followed by heavy flood irrigation."
    ],
    "activeIngredient": "Disodium tetraborate decahydrate (Borax / Na2B4O7\u00b710H2O)",
    "formulation": "Agricultural Grade Borax (11% Boron content)",
    "dosagePerPalm": "15g to 20g Borax per palm annually in root basin",
    "applicationMethod": "Soil incorporation into root zone basin mixed with compost or farmyard manure",
    "verificationLimitations": "Nutritional and irrigation management protocol; cannot repair already cracked nuts."
  },
  {
    "id": "REC-NC-02",
    "targetDiseaseKey": "NutCracking",
    "targetDiseaseDisplayName": "Nut Cracking & Splitting Disorder",
    "scientificName": "Physiological moisture shock & Boron deficiency",
    "category": "CULTURAL_SANITATION",
    "title": "Basin Mulching & Summer Soil Moisture Conservation",
    "verificationStatus": "GENERAL_NON_CHEMICAL_GUIDANCE",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Mulch palm basins up to a radius of 1 meter with dry areca leaves or organic green matter (8\u201310 cm depth). This insulates soil against extreme temperature swings and minimizes evaporation loss, preventing abrupt sap pressure shocks that trigger pericarp splitting.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Package of Practices: Soil and Water Management in Arecanut",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Keep mulch 10 cm away from trunk collar to prevent collar fungal dampness."
    ],
    "applicationMethod": "Heavy organic mulching of palm basins with dry arecanut leaves and organic residue",
    "verificationLimitations": "General soil moisture management."
  },
  {
    "id": "REC-SM-01",
    "targetDiseaseKey": "SootyMold",
    "targetDiseaseDisplayName": "Sooty Mold (Epiphytic Fungal Crust)",
    "scientificName": "Capnodium spp.",
    "category": "CULTURAL_SANITATION",
    "title": "2% Boiled Starch Paste Mechanical Foliar Spray",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Sooty mold is non-parasitic and grows exclusively on honeydew excreted by sap-sucking insects. Prepare a 2% starch paste by boiling 20g maida or starch in 1 liter of water. Spray thoroughly on the blackened canopy during bright sunshine. On drying, the starch forms thin dry flakes that naturally peel off, pulling the black mold crust away without damaging leaf tissue.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Crop Protection: Management of Sooty Mold in Palms",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Spray must be executed on a clear sunny day for effective starch crust formation and peeling.",
      "Do not spray systemic fungicides; the fungus is non-parasitic and lives on honeydew exudate."
    ],
    "activeIngredient": "Boiled agricultural starch / Maida (20g per 1L water)",
    "formulation": "2% Starch Paste (20g Maida boiled in water, cooled and strained)",
    "dosagePerLiter": "20g boiled starch / 1L water",
    "dosagePerPalm": "1.5 to 2.0 Litres on blackened foliage",
    "applicationMethod": "Foliar spray on sunlit days targeting soot-blackened frond surfaces",
    "verificationLimitations": "Mechanical removal technique; does not kill the underlying insect vectors."
  },
  {
    "id": "REC-SM-02",
    "targetDiseaseKey": "SootyMold",
    "targetDiseaseDisplayName": "Sooty Mold (Epiphytic Fungal Crust)",
    "scientificName": "Capnodium spp.",
    "category": "BIO_CONTROL",
    "title": "Fish Oil Rosin Soap (FORS) or Neem Oil for Underlying Sucking Insects",
    "verificationStatus": "GENERAL_NON_CHEMICAL_GUIDANCE",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "To prevent mold recurrence, control the underlying sap-sucking scale insects and mealybugs using Fish Oil Rosin Soap (FORS at 20g/L) or Neem Oil (5ml/L emulsified with soap nut). Spray undersides of leaflets where insect colonies congregate.",
    "sourceOrganization": "Tamil Nadu Agricultural University (TNAU) Agritech Portal",
    "sourceTitle": "Crop Protection: Eco-friendly Pest Management in Plantation Crops",
    "sourceUrl": "https://agritech.tnau.ac.in/crop_protection/arecanut_diseases_3.html",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Test emulsification before full application to avoid leaf burn.",
      "Avoid spraying during high noon temperature."
    ],
    "activeIngredient": "Fish Oil Rosin Soap (20g/L) or Cold-Pressed Neem Oil (5ml/L)",
    "formulation": "Natural botanical surfactant emulsion",
    "dosagePerLiter": "20g FORS or 5ml Neem Oil / 1L water",
    "applicationMethod": "High-pressure foliar wash targeting scale insects, mealybugs, and whiteflies",
    "verificationLimitations": "Bio-surfactant pest suppression."
  },
  {
    "id": "REC-SM-03",
    "targetDiseaseKey": "SootyMold",
    "targetDiseaseDisplayName": "Sooty Mold (Epiphytic Fungal Crust)",
    "scientificName": "Capnodium spp.",
    "category": "CHEMICAL_INSECTICIDE",
    "title": "Dimethoate / Chlorpyrifos Synthetic Insecticides",
    "verificationStatus": "BLOCKED_UNVERIFIED",
    "displayEligible": false,
    "actionableChemicalAllowed": false,
    "guidanceText": "Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
    "sourceOrganization": "CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
    "sourceTitle": "Major Uses of Pesticides - Registered under the Insecticides Act, 1968",
    "sourceUrl": "http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Dimethoate and Chlorpyrifos lack approved CIBRC label directions on arecanut canopy for Sooty Mold.",
      "High toxicity to beneficial pollinators and natural predators."
    ],
    "verificationLimitations": "Blocked from actionable prescription."
  },
  {
    "id": "REC-HLT-01",
    "targetDiseaseKey": "Healthy",
    "targetDiseaseDisplayName": "Healthy (Optimal Vigor)",
    "scientificName": "Areca catechu L. (Optimal Health)",
    "category": "NUTRIENT_MANAGEMENT",
    "title": "Standard Annual Split Fertigation Schedule (Bearing Palm)",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Maintain standard annual nutritional regimen for bearing palms (5+ years). Apply pure nutrients of 100g Nitrogen, 40g Phosphorus, and 140g Potash per palm annually in two splits: 1/3rd in April\u2013May with summer showers, and 2/3rd in September\u2013October with 12\u201315kg well-decomposed FYM. THIS IS ROUTINE SEASONAL MAINTENANCE, NOT A DISEASE TREATMENT.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "Package of Practices for Arecanut: Fertilizer Management for Bearing Palms",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Never apply fertilizer directly touching the palm collar.",
      "Ensure adequate soil moisture before and after fertilizer application."
    ],
    "activeIngredient": "Pure Nutrients: 100g N, 40g P2O5, 140g K2O + 12\u201315kg FYM / palm / year",
    "formulation": "Commercial equivalents: 220g Urea, 200g Rock Phosphate, 235g Muriate of Potash (MOP)",
    "dosagePerPalm": "Split 1: 75g Urea, 70g Rock Phos, 80g MOP; Split 2: 145g Urea, 130g Rock Phos, 155g MOP + full FYM",
    "applicationMethod": "Ring trench application 0.75m to 1.0m from trunk base followed by light irrigation",
    "verificationLimitations": "Nutrient maintenance for healthy palms; does not prevent or treat active infections."
  },
  {
    "id": "REC-YLD-01",
    "targetDiseaseKey": "PhytoplasmaYellowLeaf",
    "targetDiseaseDisplayName": "Phytoplasma Yellow Leaf Disease (YLD)",
    "scientificName": "Areca palm phytoplasma (16SrXI group)",
    "category": "CULTURAL_SANITATION",
    "title": "Integrated Disease Management: Eradication & Nutrient Fortification (No Chemical Cure)",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Yellow Leaf Disease is caused by a systemic phytoplasma pathogen. THERE IS CURRENTLY NO CHEMICAL CURE. FUNGICIDES HAVE ZERO EFFECT AND ARE STRICTLY PROHIBITED. Practice Integrated Disease Management: 1. Severely stunted, non-bearing palms must be uprooted and burnt immediately to destroy the inoculum reservoir. 2. Mildly infected palms can sustain economic bearing through supplemental Magnesium Sulphate (100g/palm) and Zinc Sulphate (50g/palm) along with balanced NPK and organic manures. 3. Ensure excellent drainage during monsoons.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "Technical Bulletin: Yellow Leaf Disease of Arecanut and its Integrated Management",
    "sourceUrl": "https://cpcri.gov.in/page/article/researchachievements_crop_protection",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Fungicides have zero efficacy against phytoplasmas; do not spray fungicides.",
      "Fertilizer is a supportive vigor measure, NOT a cure for the phytoplasma infection.",
      "Do not transport seedlings or seed nuts from YLD-endemic zones to disease-free tracts."
    ],
    "dosagePerPalm": "Supplemental: 100g Magnesium Sulphate + 50g Zinc Sulphate per palm annually",
    "applicationMethod": "Basal trench application incorporated with organic compost",
    "verificationLimitations": "Incurable systemic infection; management focuses on containment and vigor maintenance."
  },
  {
    "id": "REC-YLD-02",
    "targetDiseaseKey": "PhytoplasmaYellowLeaf",
    "targetDiseaseDisplayName": "Phytoplasma Yellow Leaf Disease (YLD)",
    "scientificName": "Areca palm phytoplasma (16SrXI group)",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "Fungicide Application for Phytoplasma",
    "verificationStatus": "BLOCKED_UNVERIFIED",
    "displayEligible": false,
    "actionableChemicalAllowed": false,
    "guidanceText": "Chemical treatment not shown: Fungicides have zero biological efficacy against phytoplasmas and are prohibited.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "Research Achievements: Phytoplasma Pathology in Palms",
    "sourceUrl": "https://cpcri.gov.in/page/article/researchachievements_crop_protection",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Phytoplasmas lack cell walls; fungicides targeting fungal chitin/ergosterol are biologically useless."
    ],
    "verificationLimitations": "Scientifically invalid treatment. Strictly blocked."
  },
  {
    "id": "REC-BB-01",
    "targetDiseaseKey": "BudBorer",
    "targetDiseaseDisplayName": "Bud Borer / Inflorescence Caterpillar",
    "scientificName": "Allocasis arecae",
    "category": "CULTURAL_SANITATION",
    "title": "Crown Debris Clearance & Neem Cake Dusting",
    "verificationStatus": "GENERAL_NON_CHEMICAL_GUIDANCE",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Clean dead debris, dry spathes, and frass from leaf axils and the crown. Dust leaf axils with a mixture of neem cake and coarse river sand (1:1 ratio) to deter adult moths from oviposition. Inspect spindle shoots regularly for early bore holes.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Crop Protection: Management of Emerging Pests in Arecanut",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Ensure climber safety during manual crown cleaning."
    ],
    "applicationMethod": "Manual sanitation of leaf axils and crown dusting with neem cake and sand (1:1)",
    "verificationLimitations": "Cultural pest management."
  },
  {
    "id": "REC-BB-02",
    "targetDiseaseKey": "BudBorer",
    "targetDiseaseDisplayName": "Bud Borer / Inflorescence Caterpillar",
    "scientificName": "Allocasis arecae",
    "category": "CHEMICAL_INSECTICIDE",
    "title": "Chlorpyrifos 20% EC / Cartap Hydrochloride Crown Spraying",
    "verificationStatus": "BLOCKED_UNVERIFIED",
    "displayEligible": false,
    "actionableChemicalAllowed": false,
    "guidanceText": "Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
    "sourceOrganization": "CIBRC / Ministry of Agriculture and Farmers Welfare",
    "sourceTitle": "Gazette Notification S.O. 4294(E) regarding Insecticide Restrictions",
    "sourceUrl": "http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Chlorpyrifos is subject to national regulatory restrictions and phase-out scrutiny.",
      "Lacks approved CIBRC label claims for arecanut crown drenching."
    ],
    "verificationLimitations": "Blocked from actionable prescription."
  },
  {
    "id": "REC-SB-01",
    "targetDiseaseKey": "StemBleeding",
    "targetDiseaseDisplayName": "Stem Bleeding Disease",
    "scientificName": "Thielaviopsis paradoxa / Ceratocystis paradoxa",
    "category": "CULTURAL_SANITATION",
    "title": "Surgical Bark Excision & Wound Sanitation (Chemical Dressing Under Review)",
    "verificationStatus": "REVIEW_REQUIRED",
    "displayEligible": true,
    "actionableChemicalAllowed": false,
    "guidanceText": "Cleanly chisel off the affected bleeding patches of bark until healthy, yellowish-white tissue is exposed. Collect and burn all scraped diseased wood shavings outside the garden to eliminate spores. Chemical wound dressings (Bordeaux paste concentration) are under agronomic review and lack specific CIBRC label claims. Hot coal tar and banned Tridemorph are strictly prohibited. Consult your local Krishi Vigyan Kendra (KVK) for regional wound-dressing protocols.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Extension Bulletin: Stem Bleeding Disease of Palms & Bio-agent Research",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-13",
    "safetyCaveats": [
      "Do not apply hot coal tar or banned Tridemorph (S.O. 3951(E)).",
      "Bordeaux paste concentrations are conflicting across historical literature (5% vs 10%) and lack statutory CIBRC label claims for stem swabbing.",
      "Collect and burn all scraped wood shavings; do not leave on orchard floor."
    ],
    "applicationMethod": "Clean surgical chiseling of decaying bark tissue to healthy wood; collection and burning of diseased wood shavings",
    "verificationLimitations": "Surgical sanitation protocol supported; topical chemical wound dressing under regulatory review."
  },
  {
    "id": "REC-SB-02",
    "targetDiseaseKey": "StemBleeding",
    "targetDiseaseDisplayName": "Stem Bleeding Disease",
    "scientificName": "Thielaviopsis paradoxa",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "Tridemorph 5% (Calixin) Swabbing & Hot Coal Tar Dressing (Banned / Obsolete)",
    "verificationStatus": "OUTDATED_REVIEW_REQUIRED",
    "displayEligible": false,
    "actionableChemicalAllowed": false,
    "guidanceText": "Obsolete and prohibited practice: Tridemorph is banned in India under Gazette S.O. 3951(E) and hot coal tar is an unapproved, hazardous petroleum product causing cambium injury.",
    "sourceOrganization": "CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
    "sourceTitle": "Historical Insecticides Schedule & Gazette S.O. 3951(E)",
    "sourceUrl": "http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
    "lastReviewedDate": "2026-10-13",
    "safetyCaveats": [
      "Tridemorph is banned in India under Gazette Notification S.O. 3951(E) dated August 8, 2018.",
      "Coal tar is a carcinogenic crude petroleum derivative with zero CIBRC registration."
    ],
    "verificationLimitations": "Banned and obsolete historical practice. Strictly blocked."
  },
  {
    "id": "REC-SC-01",
    "targetDiseaseKey": "StemCracking",
    "targetDiseaseDisplayName": "Stem Cracking (Sun Scorch Disorder)",
    "scientificName": "Physiological Solar Radiation & Thermal Stress",
    "category": "MECHANICAL_BARRIER",
    "title": "Trunk Whitewashing with Slaked Lime Wash",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Stem cracking is a physical sun-scorch disorder caused by intense direct solar heating of southern and western trunk faces during winter/summer, followed by sudden cool nights. Paint the exposed trunk up to 2.5 meters with a white slaked lime wash to reflect solar radiation. FUNGICIDES ARE NOT APPLICABLE.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Crop Advice: Protection of Arecanut Trunks Against Sun Scorch",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Do not use chemical fungicides \u2014 this is physical solar radiation damage.",
      "Wear eye protection when preparing slaked lime wash."
    ],
    "activeIngredient": "Calcium Hydroxide (Slaked Lime / Ca(OH)2)",
    "formulation": "Lime wash (1 kg Slaked Lime per 5L water)",
    "dosagePerPalm": "Topical coating on trunk up to 2.0 to 2.5 meters from ground",
    "applicationMethod": "Brush application on southern and western exposed trunk sides before summer (December\u2013January)",
    "verificationLimitations": "Preventive solar deflection; does not heal preexisting mechanical trunk fissures."
  },
  {
    "id": "REC-LSC-01",
    "targetDiseaseKey": "LeafSpotComplex",
    "targetDiseaseDisplayName": "Leaf Spot Complex",
    "scientificName": "Phyllosticta arecae / Colletotrichum gloeosporioides",
    "category": "CHEMICAL_FUNGICIDE",
    "title": "1% Bordeaux Mixture or Copper Oxychloride Protective Spray",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Spray 1% Bordeaux mixture or Copper Oxychloride (2.5g/L) on affected foliage. Improve sunlight penetration by thinning overhanging intercrop canopy.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Extension Bulletin: Foliar Diseases of Arecanut",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "Spray both upper and lower leaf surfaces.",
      "Avoid spraying during windy conditions."
    ],
    "activeIngredient": "1% Bordeaux Mixture or Copper Oxychloride 50% WP (2.5g/L)",
    "formulation": "1% Bordeaux Mixture or COC 50% WP",
    "dosagePerLiter": "10g Bordeaux or 2.5g COC / 1L water",
    "applicationMethod": "Foliar canopy spray during early post-monsoon or pre-summer appearance",
    "sprayIntervalDays": 25,
    "withholdingPeriodDays": 10,
    "verificationLimitations": "Contact protective spray."
  },
  {
    "id": "REC-YL-01",
    "targetDiseaseKey": "YellowLeaf",
    "targetDiseaseDisplayName": "Yellow Leaf (Nutritional Chlorosis)",
    "scientificName": "Physiological Chlorosis / Soil Drainage Deficit",
    "category": "NUTRIENT_MANAGEMENT",
    "title": "Drainage Amelioration & Soil Micronutrient Balance",
    "verificationStatus": "VERIFIED_OFFICIAL",
    "displayEligible": true,
    "actionableChemicalAllowed": true,
    "guidanceText": "Non-phytoplasma yellowing is primarily caused by poor drainage, root waterlogging, or acidic soil micronutrient lock-up. Dig 0.75m drainage channels between rows to lower water table. Apply Dolomite lime (500g/palm) in alternate years if soil pH is below 5.5, accompanied by zinc and magnesium.",
    "sourceOrganization": "ICAR - Central Plantation Crops Research Institute (CPCRI)",
    "sourceTitle": "ICAR-CPCRI Package of Practices: Soil Amelioration in Laterite Soils",
    "sourceUrl": "https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
    "lastReviewedDate": "2026-10-12",
    "safetyCaveats": [
      "DO NOT apply fungicides for nutritional or drainage chlorosis.",
      "Test soil pH before adding lime."
    ],
    "dosagePerPalm": "Soil Application: 500g Dolomite Lime (in acidic soils) + 50g Zinc Sulphate",
    "applicationMethod": "Basal soil application in ring trenches",
    "verificationLimitations": "Soil and water management protocol."
  }
]

// Lookup dictionaries
const _BY_ID: Record<string, RecommendationRecord> = {}
const _BY_DISEASE_KEY: Record<string, RecommendationRecord[]> = {}

for (const r of RECOMMENDATIONS_REGISTRY) {
  _BY_ID[r.id] = r
  if (!_BY_DISEASE_KEY[r.targetDiseaseKey]) {
    _BY_DISEASE_KEY[r.targetDiseaseKey] = []
  }
  _BY_DISEASE_KEY[r.targetDiseaseKey].push(r)
}

const ALIAS_MAP: Record<string, string> = {
  koleroga: "FruitRot",
  "fruit rot": "FruitRot",
  fruitrot: "FruitRot",
  anthracnose: "Anthracnose",
  "nut cracking": "NutCracking",
  nutcracking: "NutCracking",
  "sooty mold": "SootyMold",
  sootymold: "SootyMold",
  healthy: "Healthy",
  phytoplasma: "PhytoplasmaYellowLeaf",
  "yellow leaf disease": "PhytoplasmaYellowLeaf",
  phytoplasmayellowleaf: "PhytoplasmaYellowLeaf",
  "bud borer": "BudBorer",
  budborer: "BudBorer",
  "stem bleeding": "StemBleeding",
  stembleeding: "StemBleeding",
  "stem cracking": "StemCracking",
  stemcracking: "StemCracking",
  "leaf spot": "LeafSpotComplex",
  leafspotcomplex: "LeafSpotComplex",
  "yellow leaf": "YellowLeaf",
  yellowleaf: "YellowLeaf",
}

export function getRecommendationById(id: string): RecommendationRecord | undefined {
  return _BY_ID[id]
}

export function getRecommendationsForDisease(diseaseKey: string): RecommendationRecord[] {
  const normKey = diseaseKey.toLowerCase().trim()
  const resolved = ALIAS_MAP[normKey] || diseaseKey
  return _BY_DISEASE_KEY[resolved] || []
}

export function getActionableTreatments(diseaseKey: string): string[] {
  const records = getRecommendationsForDisease(diseaseKey)
  if (!records.length) {
    return [
      "Chemical treatment not shown because current crop-specific approval and dosage could not be verified. Please consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer.",
    ]
  }

  const items: string[] = []
  let hasVerifiedChemical = false

  for (const r of records) {
    if (r.verificationStatus === "VERIFIED_OFFICIAL" && r.actionableChemicalAllowed) {
      hasVerifiedChemical = true
      items.push(`[Official Recommendation] ${r.title}: ${r.guidanceText}`)
    } else if (r.verificationStatus === "GENERAL_NON_CHEMICAL_GUIDANCE" && r.displayEligible) {
      items.push(`[Cultural / Sanitation Guidance] ${r.title}: ${r.guidanceText}`)
    }
  }

  const nonDiseaseKeys = ["Healthy", "NutCracking", "StemCracking"]
  const resolved = ALIAS_MAP[diseaseKey.toLowerCase().trim()] || diseaseKey
  if (!hasVerifiedChemical && !nonDiseaseKeys.includes(resolved)) {
    items.unshift(
      "Chemical treatment not shown because current crop-specific approval and dosage could not be verified. Please consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer."
    )
  }

  return items.length > 0
    ? items
    : [
        "Chemical treatment not shown because current crop-specific approval and dosage could not be verified. Please consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer.",
      ]
}

export function getOrganicControl(diseaseKey: string): string[] {
  const records = getRecommendationsForDisease(diseaseKey)
  const items: string[] = []
  for (const r of records) {
    if (r.category === "BIO_CONTROL" || r.category === "MECHANICAL_BARRIER") {
      const tag =
        r.verificationStatus === "VERIFIED_RESEARCH_ONLY"
          ? "[Bio-Control / Research]"
          : "[Mechanical / Cultural Barrier]"
      items.push(`${tag} ${r.title}: ${r.guidanceText}`)
    }
  }
  return items.length > 0
    ? items
    : ["Maintain field hygiene, ensure adequate drainage, and apply enriched organic compost."]
}

export function getBlockedTreatments(diseaseKey: string): RecommendationRecord[] {
  const records = getRecommendationsForDisease(diseaseKey)
  return records.filter(
    (r) =>
      r.verificationStatus === "BLOCKED_UNVERIFIED" ||
      r.verificationStatus === "OUTDATED_REVIEW_REQUIRED"
  )
}

export function getRegistrySummaryStats() {
  const totalRecords = RECOMMENDATIONS_REGISTRY.length
  const byStatus: Record<string, number> = {}
  const byCategory: Record<string, number> = {}

  for (const r of RECOMMENDATIONS_REGISTRY) {
    byStatus[r.verificationStatus] = (byStatus[r.verificationStatus] || 0) + 1
    byCategory[r.category] = (byCategory[r.category] || 0) + 1
  }

  return {
    totalRecords,
    byStatus,
    byCategory,
    targetDiseasesCovered: Object.keys(_BY_DISEASE_KEY).length,
  }
}
