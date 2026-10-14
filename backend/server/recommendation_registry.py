"""
backend/server/recommendation_registry.py

Centralized, typed, auditable recommendation registry for ArecaVision AI.
Serves as the single source of truth for all fertilizer, pesticide, fungicide,
biological control, and agronomic management advice across the backend,
frontend API endpoints, and AI Assistant.

Audited against:
1. ICAR - Central Plantation Crops Research Institute (CPCRI)
   - Farmer's Corner: Crop Advice for Arecanut (https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut)
   - Research Achievements: Crop Protection (https://cpcri.gov.in/page/article/researchachievements_crop_protection)
2. Central Insecticides Board & Registration Committee (CIBRC / PPQ&S, Ministry of Agriculture)
   - Major Uses of Pesticides (http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides)
3. Tamil Nadu Agricultural University (TNAU) Agritech Portal - Crop Protection (Arecanut)
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Optional


class VerificationStatus(str, Enum):
    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"
    VERIFIED_RESEARCH_ONLY = "VERIFIED_RESEARCH_ONLY"
    GENERAL_NON_CHEMICAL_GUIDANCE = "GENERAL_NON_CHEMICAL_GUIDANCE"
    BLOCKED_UNVERIFIED = "BLOCKED_UNVERIFIED"
    OUTDATED_REVIEW_REQUIRED = "OUTDATED_REVIEW_REQUIRED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RecommendationCategory(str, Enum):
    CHEMICAL_FUNGICIDE = "CHEMICAL_FUNGICIDE"
    CHEMICAL_INSECTICIDE = "CHEMICAL_INSECTICIDE"
    BIO_CONTROL = "BIO_CONTROL"
    CULTURAL_SANITATION = "CULTURAL_SANITATION"
    NUTRIENT_MANAGEMENT = "NUTRIENT_MANAGEMENT"
    MECHANICAL_BARRIER = "MECHANICAL_BARRIER"


@dataclass(frozen=True)
class RecommendationRecord:
    id: str
    target_disease_key: str
    target_disease_display_name: str
    scientific_name: str
    category: RecommendationCategory
    title: str
    verification_status: VerificationStatus
    display_eligible: bool
    actionable_chemical_allowed: bool
    guidance_text: str
    source_organization: str
    source_title: str
    source_url: str
    last_reviewed_date: str
    safety_caveats: list[str]
    active_ingredient: Optional[str] = None
    formulation: Optional[str] = None
    dosage_per_liter: Optional[str] = None
    dosage_per_palm: Optional[str] = None
    application_method: Optional[str] = None
    spray_interval_days: Optional[int] = None
    withholding_period_days: Optional[int] = None
    source_date: Optional[str] = None
    verification_limitations: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["verification_status"] = self.verification_status.value
        return d


RECOMMENDATIONS_REGISTRY: list[RecommendationRecord] = [
    # -------------------------------------------------------------------------
    # 1. FruitRot (Koleroga / Mahali - Phytophthora meadii)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-FR-01",
        target_disease_key="FruitRot",
        target_disease_display_name="Fruit Rot (Koleroga / Mahali)",
        scientific_name="Phytophthora meadii",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="1% Neutral Bordeaux Mixture Prophylactic Canopy & Bunch Spray",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="Copper Sulphate (CuSO4) + Calcium Hydroxide / Quicklime (CaO) (1:1 ratio)",
        formulation="1% Bordeaux Mixture (10g CuSO4 + 10g Quicklime per 1L water) with Rosin-Soda Sticker",
        dosage_per_liter="10g CuSO4 + 10g Quicklime / 1L water",
        dosage_per_palm="2.0 to 2.5 Litres per mature palm canopy",
        application_method="High-pressure canopy and bunch drench spray using gator/rocker sprayer before monsoon onset",
        spray_interval_days=45,
        withholding_period_days=14,
        guidance_text=(
            "Apply first prophylactic spray thoroughly covering all nut bunches just before the onset of the "
            "South-West monsoon (late May / early June). A second spray should be applied 40–45 days later "
            "if rainfall persists. Always conduct the iron knife test to ensure neutrality before spraying."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Crop Advice for Arecanut: Monsoon Disease Management",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2024",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Never prepare or store Bordeaux mixture in metal containers (use plastic or earthen drums).",
            "Spray must be completed within 12 hours of preparation to prevent copper crystallization.",
            "Wear protective goggles, gloves, and face shield during canopy application."
        ],
        verification_limitations="Prophylactic shield only; will not reverse decay on already rotted nuts."
    ),
    RecommendationRecord(
        id="REC-FR-02",
        target_disease_key="FruitRot",
        target_disease_display_name="Fruit Rot (Koleroga / Mahali)",
        scientific_name="Phytophthora meadii",
        category=RecommendationCategory.MECHANICAL_BARRIER,
        title="Polythene Bunch Covering & Fallen Nut Sanitation",
        verification_status=VerificationStatus.GENERAL_NON_CHEMICAL_GUIDANCE,
        display_eligible=True,
        actionable_chemical_allowed=False,
        application_method="Manual bunch covering with 200-gauge UV-stabilized polythene bags before monsoon showers",
        guidance_text=(
            "Tie clean, high-density polythene covers over maturing nut bunches prior to monsoon onset. "
            "Ensure the bottom remains open for ventilation while deflecting rain splash. Promptly collect and "
            "deeply bury or incinerate all fallen rotted nuts to eliminate the primary oospore reservoir."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="Research Achievements: Integrated Management of Koleroga in Arecanut",
        source_url="https://cpcri.gov.in/page/article/researchachievements_crop_protection",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Ensure climber safety during manual tying at palm height.",
            "Bagging must allow bottom drainage to avoid moisture condensation inside the sleeve."
        ],
        verification_limitations="Non-chemical cultural barrier; effective primarily when installed before first rain."
    ),
    RecommendationRecord(
        id="REC-FR-03",
        target_disease_key="FruitRot",
        target_disease_display_name="Fruit Rot (Koleroga / Mahali)",
        scientific_name="Phytophthora meadii",
        category=RecommendationCategory.BIO_CONTROL,
        title="Trichoderma harzianum Pre-Monsoon Soil Basin Inoculation",
        verification_status=VerificationStatus.VERIFIED_RESEARCH_ONLY,
        display_eligible=True,
        actionable_chemical_allowed=False,
        active_ingredient="Trichoderma harzianum (min 2x10^8 CFU/g)",
        formulation="Talc-based bio-formulation (10g/L or 2kg enriched FYM/palm)",
        dosage_per_palm="2 kg enriched Farmyard Manure (FYM) incorporated into basin",
        application_method="Soil incorporation into root zone basin in May",
        guidance_text=(
            "Enrich 100 kg well-decomposed FYM with 1 kg Trichoderma harzianum culture under shade for 15 days. "
            "Apply 2 kg of this bio-enriched mixture around the root zone basin of each palm in May before monsoon onset."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="CPCRI Crop Protection: Biological Control of Phytophthora in Plantation Crops",
        source_url="https://cpcri.gov.in/page/article/researchachievements_crop_protection",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Do not mix or apply Trichoderma simultaneously with chemical fungicides or copper sprays in the basin.",
            "Maintain soil moisture for bio-agent colonization."
        ],
        verification_limitations="Research-supported bio-control; cannot replace canopy fungicide during high-intensity monsoons."
    ),
    RecommendationRecord(
        id="REC-FR-04",
        target_disease_key="FruitRot",
        target_disease_display_name="Fruit Rot (Koleroga / Mahali)",
        scientific_name="Phytophthora meadii",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="Mandipropamid / Metalaxyl Systemic Oomyceticides",
        verification_status=VerificationStatus.BLOCKED_UNVERIFIED,
        display_eligible=False,
        actionable_chemical_allowed=False,
        guidance_text="Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
        source_organization="CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
        source_title="Major Uses of Pesticides - Registered under the Insecticides Act, 1968",
        source_url="http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
        source_date="2024",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Off-label systemic chemical application is strictly prohibited without official CIBRC label registration on arecanut.",
            "Risk of chemical residue accumulation in areca masticatory kernel."
        ],
        verification_limitations="Lacks explicit, direct CIBRC label-claim registration for arecanut canopy spraying."
    ),

    # -------------------------------------------------------------------------
    # 2. Anthracnose (Colletotrichum gloeosporioides - Inflorescence Dieback & Foliar Spot)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-ANT-01",
        target_disease_key="Anthracnose",
        target_disease_display_name="Anthracnose (Dieback & Nut Spot)",
        scientific_name="Colletotrichum gloeosporioides",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="1% Bordeaux Mixture or Copper Oxychloride 50% WP Protective Spray",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="Copper Oxychloride 50% WP or 1% Bordeaux Mixture",
        formulation="Copper Oxychloride 50% WP (2.5g to 3.0g / 1L water)",
        dosage_per_liter="2.5g to 3.0g COC per 1L water",
        dosage_per_palm="1.5 to 2.0 Litres per affected palm canopy",
        application_method="Foliar canopy spray targeting blighted fronds and emergent inflorescences",
        spray_interval_days=21,
        withholding_period_days=10,
        guidance_text=(
            "Spray Copper Oxychloride (2.5g to 3.0g/L) or 1% Bordeaux mixture on emergent inflorescences "
            "and blighted fronds when symptoms appear. Prune and destroy dead spadices and severely spotted "
            "frond tips before spraying to optimize chemical coverage."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Package of Practices: Inflorescence Dieback and Foliar Anthracnose",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Prune blighted fronds first before spraying to eliminate sporulating source.",
            "Do not spray during peak midday solar radiation to prevent chemical leaf scorch."
        ],
        verification_limitations="Contact protective action; requires thorough wetting of both upper and lower leaf surfaces."
    ),
    RecommendationRecord(
        id="REC-ANT-02",
        target_disease_key="Anthracnose",
        target_disease_display_name="Anthracnose (Dieback & Nut Spot)",
        scientific_name="Colletotrichum gloeosporioides",
        category=RecommendationCategory.CULTURAL_SANITATION,
        title="Sanitary Frond Pruning & Plantation Aeration",
        verification_status=VerificationStatus.GENERAL_NON_CHEMICAL_GUIDANCE,
        display_eligible=True,
        actionable_chemical_allowed=False,
        application_method="Sanitary excision of necrotic rachis tips and thinning of overhanging intercrop shade",
        guidance_text=(
            "Cut away severely infected necrotic fronds and dry spadices using disinfected pruning shears. "
            "Burn the pruned material outside the garden. Thin dense overhanging shade trees to improve sunlight "
            "penetration into the canopy and lower microclimate leaf-wetness duration."
        ),
        source_organization="Tamil Nadu Agricultural University (TNAU) Agritech Portal",
        source_title="Crop Protection - Arecanut Diseases: Inflorescence Dieback & Blight",
        source_url="https://agritech.tnau.ac.in/crop_protection/arecanut_diseases_3.html",
        source_date="2022",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Disinfect cutting tools between palms using 70% alcohol or 1% sodium hypochlorite.",
            "Avoid deep wounding of tender crown green tissue."
        ],
        verification_limitations="Cultural management protocol; essential companion to any fungicidal intervention."
    ),
    RecommendationRecord(
        id="REC-ANT-03",
        target_disease_key="Anthracnose",
        target_disease_display_name="Anthracnose (Dieback & Nut Spot)",
        scientific_name="Colletotrichum gloeosporioides",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="Hexaconazole 5% EC / Carbendazim Systemic Fungicides",
        verification_status=VerificationStatus.BLOCKED_UNVERIFIED,
        display_eligible=False,
        actionable_chemical_allowed=False,
        guidance_text="Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
        source_organization="CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
        source_title="Major Uses of Pesticides - Registered under the Insecticides Act, 1968",
        source_url="http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
        source_date="2024",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Carbendazim is under ongoing regulatory review and potential restriction in India.",
            "Off-label systemic triazole use on arecanut lacks verified MRL data."
        ],
        verification_limitations="Blocked from actionable prescription pending verified CIBRC arecanut label claim."
    ),

    # -------------------------------------------------------------------------
    # 3. NutCracking (Physiological / Nutritional Disorder)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-NC-01",
        target_disease_key="NutCracking",
        target_disease_display_name="Nut Cracking & Splitting Disorder",
        scientific_name="Physiological moisture shock & Boron deficiency",
        category=RecommendationCategory.NUTRIENT_MANAGEMENT,
        title="Soil Borax Application & Water Regulation (Not a Fungal Disease)",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="Disodium tetraborate decahydrate (Borax / Na2B4O7·10H2O)",
        formulation="Agricultural Grade Borax (11% Boron content)",
        dosage_per_palm="15g to 20g Borax per palm annually in root basin",
        application_method="Soil incorporation into root zone basin mixed with compost or farmyard manure",
        guidance_text=(
            "Nut cracking is a physiological disorder, NOT an infectious fungal or bacterial disease. "
            "FUNGICIDES ARE COMPLETELY INEFFECTIVE AND MUST NOT BE USED. Apply 15g to 20g Borax per palm "
            "annually in the root zone along with regular irrigation. Maintain uniform basin or drip irrigation "
            "during hot summer months to avoid sudden turgor pressure surges when rains arrive."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Crop Advice: Physiological Disorders in Arecanut",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "DO NOT apply fungicides or insecticides — this is a physiological disorder.",
            "Do not exceed 25g Borax per palm to avoid boron phytotoxicity (leaf tip necrosis).",
            "Ensure uniform soil moisture; avoid prolonged drought followed by heavy flood irrigation."
        ],
        verification_limitations="Nutritional and irrigation management protocol; cannot repair already cracked nuts."
    ),
    RecommendationRecord(
        id="REC-NC-02",
        target_disease_key="NutCracking",
        target_disease_display_name="Nut Cracking & Splitting Disorder",
        scientific_name="Physiological moisture shock & Boron deficiency",
        category=RecommendationCategory.CULTURAL_SANITATION,
        title="Basin Mulching & Summer Soil Moisture Conservation",
        verification_status=VerificationStatus.GENERAL_NON_CHEMICAL_GUIDANCE,
        display_eligible=True,
        actionable_chemical_allowed=False,
        application_method="Heavy organic mulching of palm basins with dry arecanut leaves and organic residue",
        guidance_text=(
            "Mulch palm basins up to a radius of 1 meter with dry areca leaves or organic green matter (8–10 cm depth). "
            "This insulates soil against extreme temperature swings and minimizes evaporation loss, preventing "
            "abrupt sap pressure shocks that trigger pericarp splitting."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Package of Practices: Soil and Water Management in Arecanut",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Keep mulch 10 cm away from trunk collar to prevent collar fungal dampness."
        ],
        verification_limitations="General soil moisture management."
    ),

    # -------------------------------------------------------------------------
    # 4. SootyMold (Capnodium spp. - Epiphytic fungal crust on insect honeydew)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-SM-01",
        target_disease_key="SootyMold",
        target_disease_display_name="Sooty Mold (Epiphytic Fungal Crust)",
        scientific_name="Capnodium spp.",
        category=RecommendationCategory.CULTURAL_SANITATION,
        title="2% Boiled Starch Paste Mechanical Foliar Spray",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="Boiled agricultural starch / Maida (20g per 1L water)",
        formulation="2% Starch Paste (20g Maida boiled in water, cooled and strained)",
        dosage_per_liter="20g boiled starch / 1L water",
        dosage_per_palm="1.5 to 2.0 Litres on blackened foliage",
        application_method="Foliar spray on sunlit days targeting soot-blackened frond surfaces",
        guidance_text=(
            "Sooty mold is non-parasitic and grows exclusively on honeydew excreted by sap-sucking insects. "
            "Prepare a 2% starch paste by boiling 20g maida or starch in 1 liter of water. Spray thoroughly on "
            "the blackened canopy during bright sunshine. On drying, the starch forms thin dry flakes that naturally "
            "peel off, pulling the black mold crust away without damaging leaf tissue."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Crop Protection: Management of Sooty Mold in Palms",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Spray must be executed on a clear sunny day for effective starch crust formation and peeling.",
            "Do not spray systemic fungicides; the fungus is non-parasitic and lives on honeydew exudate."
        ],
        verification_limitations="Mechanical removal technique; does not kill the underlying insect vectors."
    ),
    RecommendationRecord(
        id="REC-SM-02",
        target_disease_key="SootyMold",
        target_disease_display_name="Sooty Mold (Epiphytic Fungal Crust)",
        scientific_name="Capnodium spp.",
        category=RecommendationCategory.BIO_CONTROL,
        title="Fish Oil Rosin Soap (FORS) or Neem Oil for Underlying Sucking Insects",
        verification_status=VerificationStatus.GENERAL_NON_CHEMICAL_GUIDANCE,
        display_eligible=True,
        actionable_chemical_allowed=False,
        active_ingredient="Fish Oil Rosin Soap (20g/L) or Cold-Pressed Neem Oil (5ml/L)",
        formulation="Natural botanical surfactant emulsion",
        dosage_per_liter="20g FORS or 5ml Neem Oil / 1L water",
        application_method="High-pressure foliar wash targeting scale insects, mealybugs, and whiteflies",
        guidance_text=(
            "To prevent mold recurrence, control the underlying sap-sucking scale insects and mealybugs using "
            "Fish Oil Rosin Soap (FORS at 20g/L) or Neem Oil (5ml/L emulsified with soap nut). Spray undersides "
            "of leaflets where insect colonies congregate."
        ),
        source_organization="Tamil Nadu Agricultural University (TNAU) Agritech Portal",
        source_title="Crop Protection: Eco-friendly Pest Management in Plantation Crops",
        source_url="https://agritech.tnau.ac.in/crop_protection/arecanut_diseases_3.html",
        source_date="2022",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Test emulsification before full application to avoid leaf burn.",
            "Avoid spraying during high noon temperature."
        ],
        verification_limitations="Bio-surfactant pest suppression."
    ),
    RecommendationRecord(
        id="REC-SM-03",
        target_disease_key="SootyMold",
        target_disease_display_name="Sooty Mold (Epiphytic Fungal Crust)",
        scientific_name="Capnodium spp.",
        category=RecommendationCategory.CHEMICAL_INSECTICIDE,
        title="Dimethoate / Chlorpyrifos Synthetic Insecticides",
        verification_status=VerificationStatus.BLOCKED_UNVERIFIED,
        display_eligible=False,
        actionable_chemical_allowed=False,
        guidance_text="Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
        source_organization="CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
        source_title="Major Uses of Pesticides - Registered under the Insecticides Act, 1968",
        source_url="http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
        source_date="2024",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Dimethoate and Chlorpyrifos lack approved CIBRC label directions on arecanut canopy for Sooty Mold.",
            "High toxicity to beneficial pollinators and natural predators."
        ],
        verification_limitations="Blocked from actionable prescription."
    ),

    # -------------------------------------------------------------------------
    # 5. Healthy (Optimal Palm Vigor & Routine Maintenance)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-HLT-01",
        target_disease_key="Healthy",
        target_disease_display_name="Healthy (Optimal Vigor)",
        scientific_name="Areca catechu L. (Optimal Health)",
        category=RecommendationCategory.NUTRIENT_MANAGEMENT,
        title="Standard Annual Split Fertigation Schedule (Bearing Palm)",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="Pure Nutrients: 100g N, 40g P2O5, 140g K2O + 12–15kg FYM / palm / year",
        formulation="Commercial equivalents: 220g Urea, 200g Rock Phosphate, 235g Muriate of Potash (MOP)",
        dosage_per_palm="Split 1: 75g Urea, 70g Rock Phos, 80g MOP; Split 2: 145g Urea, 130g Rock Phos, 155g MOP + full FYM",
        application_method="Ring trench application 0.75m to 1.0m from trunk base followed by light irrigation",
        guidance_text=(
            "Maintain standard annual nutritional regimen for bearing palms (5+ years). Apply pure nutrients "
            "of 100g Nitrogen, 40g Phosphorus, and 140g Potash per palm annually in two splits: "
            "1/3rd in April–May with summer showers, and 2/3rd in September–October with 12–15kg well-decomposed FYM. "
            "THIS IS ROUTINE SEASONAL MAINTENANCE, NOT A DISEASE TREATMENT."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="Package of Practices for Arecanut: Fertilizer Management for Bearing Palms",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2024",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Never apply fertilizer directly touching the palm collar.",
            "Ensure adequate soil moisture before and after fertilizer application."
        ],
        verification_limitations="Nutrient maintenance for healthy palms; does not prevent or treat active infections."
    ),

    # -------------------------------------------------------------------------
    # 6. PhytoplasmaYellowLeaf (Yellow Leaf Disease - YLD)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-YLD-01",
        target_disease_key="PhytoplasmaYellowLeaf",
        target_disease_display_name="Phytoplasma Yellow Leaf Disease (YLD)",
        scientific_name="Areca palm phytoplasma (16SrXI group)",
        category=RecommendationCategory.CULTURAL_SANITATION,
        title="Integrated Disease Management: Eradication & Nutrient Fortification (No Chemical Cure)",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=False,
        dosage_per_palm="Supplemental: 100g Magnesium Sulphate + 50g Zinc Sulphate per palm annually",
        application_method="Basal trench application incorporated with organic compost",
        guidance_text=(
            "Yellow Leaf Disease is caused by a systemic phytoplasma pathogen. THERE IS CURRENTLY NO CHEMICAL CURE. "
            "FUNGICIDES HAVE ZERO EFFECT AND ARE STRICTLY PROHIBITED. Practice Integrated Disease Management: "
            "1. Severely stunted, non-bearing palms must be uprooted and burnt immediately to destroy the inoculum reservoir. "
            "2. Mildly infected palms can sustain economic bearing through supplemental Magnesium Sulphate (100g/palm) "
            "and Zinc Sulphate (50g/palm) along with balanced NPK and organic manures. "
            "3. Ensure excellent drainage during monsoons."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="Technical Bulletin: Yellow Leaf Disease of Arecanut and its Integrated Management",
        source_url="https://cpcri.gov.in/page/article/researchachievements_crop_protection",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Fungicides have zero efficacy against phytoplasmas; do not spray fungicides.",
            "Fertilizer is a supportive vigor measure, NOT a cure for the phytoplasma infection.",
            "Do not transport seedlings or seed nuts from YLD-endemic zones to disease-free tracts."
        ],
        verification_limitations="Incurable systemic infection; management focuses on containment and vigor maintenance."
    ),
    RecommendationRecord(
        id="REC-YLD-02",
        target_disease_key="PhytoplasmaYellowLeaf",
        target_disease_display_name="Phytoplasma Yellow Leaf Disease (YLD)",
        scientific_name="Areca palm phytoplasma (16SrXI group)",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="Fungicide Application for Phytoplasma",
        verification_status=VerificationStatus.BLOCKED_UNVERIFIED,
        display_eligible=False,
        actionable_chemical_allowed=False,
        guidance_text="Chemical treatment not shown: Fungicides have zero biological efficacy against phytoplasmas and are prohibited.",
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="Research Achievements: Phytoplasma Pathology in Palms",
        source_url="https://cpcri.gov.in/page/article/researchachievements_crop_protection",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Phytoplasmas lack cell walls; fungicides targeting fungal chitin/ergosterol are biologically useless."
        ],
        verification_limitations="Scientifically invalid treatment. Strictly blocked."
    ),

    # -------------------------------------------------------------------------
    # 7. BudBorer (Allocasis arecae / Inflorescence caterpillar)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-BB-01",
        target_disease_key="BudBorer",
        target_disease_display_name="Bud Borer / Inflorescence Caterpillar",
        scientific_name="Allocasis arecae",
        category=RecommendationCategory.CULTURAL_SANITATION,
        title="Crown Debris Clearance & Neem Cake Dusting",
        verification_status=VerificationStatus.GENERAL_NON_CHEMICAL_GUIDANCE,
        display_eligible=True,
        actionable_chemical_allowed=False,
        application_method="Manual sanitation of leaf axils and crown dusting with neem cake and sand (1:1)",
        guidance_text=(
            "Clean dead debris, dry spathes, and frass from leaf axils and the crown. Dust leaf axils with a "
            "mixture of neem cake and coarse river sand (1:1 ratio) to deter adult moths from oviposition. "
            "Inspect spindle shoots regularly for early bore holes."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Crop Protection: Management of Emerging Pests in Arecanut",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Ensure climber safety during manual crown cleaning."
        ],
        verification_limitations="Cultural pest management."
    ),
    RecommendationRecord(
        id="REC-BB-02",
        target_disease_key="BudBorer",
        target_disease_display_name="Bud Borer / Inflorescence Caterpillar",
        scientific_name="Allocasis arecae",
        category=RecommendationCategory.CHEMICAL_INSECTICIDE,
        title="Chlorpyrifos 20% EC / Cartap Hydrochloride Crown Spraying",
        verification_status=VerificationStatus.BLOCKED_UNVERIFIED,
        display_eligible=False,
        actionable_chemical_allowed=False,
        guidance_text="Chemical treatment not shown because current crop-specific approval and dosage could not be verified.",
        source_organization="CIBRC / Ministry of Agriculture and Farmers Welfare",
        source_title="Gazette Notification S.O. 4294(E) regarding Insecticide Restrictions",
        source_url="http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Chlorpyrifos is subject to national regulatory restrictions and phase-out scrutiny.",
            "Lacks approved CIBRC label claims for arecanut crown drenching."
        ],
        verification_limitations="Blocked from actionable prescription."
    ),

    # -------------------------------------------------------------------------
    # 8. StemBleeding (Thielaviopsis paradoxa)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-SB-01",
        target_disease_key="StemBleeding",
        target_disease_display_name="Stem Bleeding Disease",
        scientific_name="Thielaviopsis paradoxa / Ceratocystis paradoxa",
        category=RecommendationCategory.CULTURAL_SANITATION,
        title="Surgical Bark Excision & Wound Sanitation (Chemical Dressing Under Review)",
        verification_status=VerificationStatus.REVIEW_REQUIRED,
        display_eligible=True,
        actionable_chemical_allowed=False,
        active_ingredient=None,
        formulation=None,
        dosage_per_palm=None,
        dosage_per_liter=None,
        application_method="Clean surgical chiseling of decaying bark tissue to healthy wood; collection and burning of diseased wood shavings",
        spray_interval_days=None,
        withholding_period_days=None,
        guidance_text=(
            "Cleanly chisel off the affected bleeding patches of bark until healthy, yellowish-white tissue is exposed. "
            "Collect and burn all scraped diseased wood shavings outside the garden to eliminate spores. Chemical wound dressings "
            "(Bordeaux paste concentration) are under agronomic review and lack specific CIBRC label claims. Hot coal tar and "
            "banned Tridemorph are strictly prohibited. Consult your local Krishi Vigyan Kendra (KVK) for regional wound-dressing protocols."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Extension Bulletin: Stem Bleeding Disease of Palms & Bio-agent Research",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-13",
        safety_caveats=[
            "Do not apply hot coal tar or banned Tridemorph (S.O. 3951(E)).",
            "Bordeaux paste concentrations are conflicting across historical literature (5% vs 10%) and lack statutory CIBRC label claims for stem swabbing.",
            "Collect and burn all scraped wood shavings; do not leave on orchard floor."
        ],
        verification_limitations="Surgical sanitation protocol supported; topical chemical wound dressing under regulatory review."
    ),
    RecommendationRecord(
        id="REC-SB-02",
        target_disease_key="StemBleeding",
        target_disease_display_name="Stem Bleeding Disease",
        scientific_name="Thielaviopsis paradoxa",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="Tridemorph 5% (Calixin) Swabbing & Hot Coal Tar Dressing (Banned / Obsolete)",
        verification_status=VerificationStatus.OUTDATED_REVIEW_REQUIRED,
        display_eligible=False,
        actionable_chemical_allowed=False,
        guidance_text="Obsolete and prohibited practice: Tridemorph is banned in India under Gazette S.O. 3951(E) and hot coal tar is an unapproved, hazardous petroleum product causing cambium injury.",
        source_organization="CIBRC / Directorate of Plant Protection, Quarantine & Storage (PPQ&S)",
        source_title="Historical Insecticides Schedule & Gazette S.O. 3951(E)",
        source_url="http://ppqs.gov.in/divisions/cibrc/major-uses-of-pesticides",
        source_date="2020",
        last_reviewed_date="2026-10-13",
        safety_caveats=[
            "Tridemorph is banned in India under Gazette Notification S.O. 3951(E) dated August 8, 2018.",
            "Coal tar is a carcinogenic crude petroleum derivative with zero CIBRC registration."
        ],
        verification_limitations="Banned and obsolete historical practice. Strictly blocked."
    ),

    # -------------------------------------------------------------------------
    # 9. StemCracking (Sun Scorch & Thermal Expansion)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-SC-01",
        target_disease_key="StemCracking",
        target_disease_display_name="Stem Cracking (Sun Scorch Disorder)",
        scientific_name="Physiological Solar Radiation & Thermal Stress",
        category=RecommendationCategory.MECHANICAL_BARRIER,
        title="Trunk Whitewashing with Slaked Lime Wash",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="Calcium Hydroxide (Slaked Lime / Ca(OH)2)",
        formulation="Lime wash (1 kg Slaked Lime per 5L water)",
        dosage_per_palm="Topical coating on trunk up to 2.0 to 2.5 meters from ground",
        application_method="Brush application on southern and western exposed trunk sides before summer (December–January)",
        guidance_text=(
            "Stem cracking is a physical sun-scorch disorder caused by intense direct solar heating of southern and "
            "western trunk faces during winter/summer, followed by sudden cool nights. Paint the exposed trunk up to "
            "2.5 meters with a white slaked lime wash to reflect solar radiation. FUNGICIDES ARE NOT APPLICABLE."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Crop Advice: Protection of Arecanut Trunks Against Sun Scorch",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Do not use chemical fungicides — this is physical solar radiation damage.",
            "Wear eye protection when preparing slaked lime wash."
        ],
        verification_limitations="Preventive solar deflection; does not heal preexisting mechanical trunk fissures."
    ),

    # -------------------------------------------------------------------------
    # 10. LeafSpotComplex (Phyllosticta / Colletotrichum foliar complex)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-LSC-01",
        target_disease_key="LeafSpotComplex",
        target_disease_display_name="Leaf Spot Complex",
        scientific_name="Phyllosticta arecae / Colletotrichum gloeosporioides",
        category=RecommendationCategory.CHEMICAL_FUNGICIDE,
        title="1% Bordeaux Mixture or Copper Oxychloride Protective Spray",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        active_ingredient="1% Bordeaux Mixture or Copper Oxychloride 50% WP (2.5g/L)",
        formulation="1% Bordeaux Mixture or COC 50% WP",
        dosage_per_liter="10g Bordeaux or 2.5g COC / 1L water",
        application_method="Foliar canopy spray during early post-monsoon or pre-summer appearance",
        spray_interval_days=25,
        withholding_period_days=10,
        guidance_text=(
            "Spray 1% Bordeaux mixture or Copper Oxychloride (2.5g/L) on affected foliage. "
            "Improve sunlight penetration by thinning overhanging intercrop canopy."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Extension Bulletin: Foliar Diseases of Arecanut",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "Spray both upper and lower leaf surfaces.",
            "Avoid spraying during windy conditions."
        ],
        verification_limitations="Contact protective spray."
    ),

    # -------------------------------------------------------------------------
    # 11. YellowLeaf (Nutritional Chlorosis / Moisture Stress)
    # -------------------------------------------------------------------------
    RecommendationRecord(
        id="REC-YL-01",
        target_disease_key="YellowLeaf",
        target_disease_display_name="Yellow Leaf (Nutritional Chlorosis)",
        scientific_name="Physiological Chlorosis / Soil Drainage Deficit",
        category=RecommendationCategory.NUTRIENT_MANAGEMENT,
        title="Drainage Amelioration & Soil Micronutrient Balance",
        verification_status=VerificationStatus.VERIFIED_OFFICIAL,
        display_eligible=True,
        actionable_chemical_allowed=True,
        dosage_per_palm="Soil Application: 500g Dolomite Lime (in acidic soils) + 50g Zinc Sulphate",
        application_method="Basal soil application in ring trenches",
        guidance_text=(
            "Non-phytoplasma yellowing is primarily caused by poor drainage, root waterlogging, or acidic soil "
            "micronutrient lock-up. Dig 0.75m drainage channels between rows to lower water table. Apply Dolomite "
            "lime (500g/palm) in alternate years if soil pH is below 5.5, accompanied by zinc and magnesium."
        ),
        source_organization="ICAR - Central Plantation Crops Research Institute (CPCRI)",
        source_title="ICAR-CPCRI Package of Practices: Soil Amelioration in Laterite Soils",
        source_url="https://cpcri.gov.in/page/article/farmers_corner_crop_advice_arecanut",
        source_date="2023",
        last_reviewed_date="2026-10-12",
        safety_caveats=[
            "DO NOT apply fungicides for nutritional or drainage chlorosis.",
            "Test soil pH before adding lime."
        ],
        verification_limitations="Soil and water management protocol."
    ),
]


# Lookup dictionaries for fast access
_BY_ID: dict[str, RecommendationRecord] = {r.id: r for r in RECOMMENDATIONS_REGISTRY}
_BY_DISEASE_KEY: dict[str, list[RecommendationRecord]] = {}
for r in RECOMMENDATIONS_REGISTRY:
    _BY_DISEASE_KEY.setdefault(r.target_disease_key, []).append(r)


def get_all_recommendations() -> list[dict[str, Any]]:
    """Return all recommendation records as serializable dictionaries."""
    return [r.to_dict() for r in RECOMMENDATIONS_REGISTRY]


def get_recommendations_for_disease(disease_key: str) -> list[RecommendationRecord]:
    """Return all recommendation records mapped to a disease key."""
    # Normalize aliases
    alias_map = {
        "koleroga": "FruitRot",
        "fruit rot": "FruitRot",
        "anthracnose": "Anthracnose",
        "nut cracking": "NutCracking",
        "nutcracking": "NutCracking",
        "sooty mold": "SootyMold",
        "sootymold": "SootyMold",
        "healthy": "Healthy",
        "phytoplasma": "PhytoplasmaYellowLeaf",
        "yellow leaf disease": "PhytoplasmaYellowLeaf",
        "bud borer": "BudBorer",
        "budborer": "BudBorer",
        "stem bleeding": "StemBleeding",
        "stembleeding": "StemBleeding",
        "stem cracking": "StemCracking",
        "stemcracking": "StemCracking",
        "leaf spot": "LeafSpotComplex",
        "leafspotcomplex": "LeafSpotComplex",
        "yellow leaf": "YellowLeaf",
        "yellowleaf": "YellowLeaf",
    }
    key = alias_map.get(disease_key.lower().strip(), disease_key)
    return _BY_DISEASE_KEY.get(key, [])


def get_actionable_treatments(disease_key: str) -> list[str]:
    """
    Return human-facing actionable treatment strings for a disease.
    CRITICAL POLICY:
    - Only VERIFIED_OFFICIAL actionable recommendations and GENERAL_NON_CHEMICAL_GUIDANCE are displayed.
    - If NO actionable chemical treatment is verified, a clear explanatory message is returned.
    """
    records = get_recommendations_for_disease(disease_key)
    if not records:
        return [
            "Chemical treatment not shown because current crop-specific approval and dosage could not be verified. "
            "Please consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer."
        ]

    actionable_items: list[str] = []
    has_verified_chemical = False

    for r in records:
        if r.verification_status == VerificationStatus.VERIFIED_OFFICIAL and r.actionable_chemical_allowed:
            has_verified_chemical = True
            actionable_items.append(f"[Official Recommendation] {r.title}: {r.guidance_text}")
        elif r.verification_status == VerificationStatus.GENERAL_NON_CHEMICAL_GUIDANCE and r.display_eligible:
            actionable_items.append(f"[Cultural / Sanitation Guidance] {r.title}: {r.guidance_text}")

    if not has_verified_chemical and disease_key not in ["Healthy", "NutCracking", "StemCracking"]:
        actionable_items.insert(
            0,
            "Chemical treatment not shown because current crop-specific approval and dosage could not be verified. "
            "Please consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer."
        )

    return actionable_items or [
        "Chemical treatment not shown because current crop-specific approval and dosage could not be verified. "
        "Please consult your local Krishi Vigyan Kendra (KVK) or agricultural extension officer."
    ]


def get_organic_control(disease_key: str) -> list[str]:
    """Return organic / bio-control / cultural options for a disease."""
    records = get_recommendations_for_disease(disease_key)
    organic_items = []
    for r in records:
        if r.category in [RecommendationCategory.BIO_CONTROL, RecommendationCategory.MECHANICAL_BARRIER]:
            tag = "[Bio-Control / Research]" if r.verification_status == VerificationStatus.VERIFIED_RESEARCH_ONLY else "[Mechanical / Cultural]"
            organic_items.append(f"{tag} {r.title}: {r.guidance_text}")
    return organic_items or ["Maintain field hygiene, ensure adequate drainage, and apply enriched organic compost."]


def get_registry_summary_stats() -> dict[str, Any]:
    """Return audit summary counts."""
    from collections import Counter
    status_counts = Counter(r.verification_status.value for r in RECOMMENDATIONS_REGISTRY)
    cat_counts = Counter(r.category.value for r in RECOMMENDATIONS_REGISTRY)
    return {
        "total_records": len(RECOMMENDATIONS_REGISTRY),
        "by_status": dict(status_counts),
        "by_category": dict(cat_counts),
        "target_diseases_covered": len(_BY_DISEASE_KEY),
    }
