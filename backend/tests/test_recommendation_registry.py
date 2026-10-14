"""
backend/tests/test_recommendation_registry.py

Tests for the centralized, typed, auditable recommendation registry and its
integration into FastAPI endpoints, health status, and agronomic assistant.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

from server.app import app
from server.recommendation_registry import (
    VerificationStatus,
    RecommendationCategory,
    RECOMMENDATIONS_REGISTRY,
    get_all_recommendations,
    get_recommendations_for_disease,
    get_actionable_treatments,
    get_organic_control,
    get_registry_summary_stats,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_registry_records_validity():
    """Verify all registry records adhere to schema, enums, and required fields."""
    assert len(RECOMMENDATIONS_REGISTRY) >= 20, "Registry should have comprehensive records"
    valid_statuses = set(VerificationStatus)
    valid_categories = set(RecommendationCategory)

    for r in RECOMMENDATIONS_REGISTRY:
        assert r.id.startswith("REC-"), f"Invalid ID prefix: {r.id}"
        assert r.target_disease_key, f"Missing target_disease_key in {r.id}"
        assert r.verification_status in valid_statuses, f"Invalid status in {r.id}"
        assert r.category in valid_categories, f"Invalid category in {r.id}"
        assert r.source_organization, f"Missing source org in {r.id}"
        assert r.source_url.startswith("http"), f"Invalid URL in {r.id}"
        assert len(r.safety_caveats) > 0, f"Missing safety caveats in {r.id}"

        # If chemical is actionable, must have verified status and official authorization
        if r.actionable_chemical_allowed:
            assert r.verification_status == VerificationStatus.VERIFIED_OFFICIAL
            assert r.display_eligible is True

        # If blocked, must not be actionable
        if r.verification_status == VerificationStatus.BLOCKED_UNVERIFIED:
            assert r.actionable_chemical_allowed is False
            assert r.display_eligible is False


def test_registry_covers_all_eleven_classes():
    """Verify all 11 trained and recognized disease classes have mapped records."""
    expected_classes = [
        "FruitRot",
        "Anthracnose",
        "NutCracking",
        "SootyMold",
        "Healthy",
        "PhytoplasmaYellowLeaf",
        "BudBorer",
        "StemBleeding",
        "StemCracking",
        "LeafSpotComplex",
        "YellowLeaf",
    ]
    for cls_name in expected_classes:
        records = get_recommendations_for_disease(cls_name)
        assert len(records) > 0, f"No records mapped for class: {cls_name}"


def test_koleroga_verified_official_bordeaux():
    """Verify Koleroga has official 1% Bordeaux mixture recommendation."""
    records = get_recommendations_for_disease("FruitRot")
    bordeaux = [r for r in records if "Bordeaux" in r.title]
    assert len(bordeaux) >= 1
    rec = bordeaux[0]
    assert rec.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert rec.actionable_chemical_allowed is True
    assert "10g CuSO4 + 10g Quicklime" in (rec.formulation or "")


def test_phytoplasma_fungicides_blocked():
    """Verify chemical fungicides are blocked for Phytoplasma Yellow Leaf."""
    records = get_recommendations_for_disease("PhytoplasmaYellowLeaf")
    blocked = [r for r in records if r.verification_status == VerificationStatus.BLOCKED_UNVERIFIED]
    assert len(blocked) >= 1
    assert any("Fungicide" in b.title for b in blocked)
    # Check that actionable treatments do not recommend fungicides
    treatments = get_actionable_treatments("PhytoplasmaYellowLeaf")
    for t in treatments:
        assert "Bordeaux" not in t
        assert "Carbendazim" not in t


def test_nut_cracking_fungicides_blocked():
    """Verify Nut Cracking recommends Borax, not fungicides."""
    treatments = get_actionable_treatments("NutCracking")
    assert any("Borax" in t for t in treatments)
    for t in treatments:
        assert "Fungicide" not in t


def test_registry_summary_stats():
    """Verify registry summary stats computation."""
    stats = get_registry_summary_stats()
    assert stats["total_records"] == len(RECOMMENDATIONS_REGISTRY)
    assert stats["target_diseases_covered"] >= 11
    assert "VERIFIED_OFFICIAL" in stats["by_status"]
    assert "BLOCKED_UNVERIFIED" in stats["by_status"]


def test_api_agronomy_recommendations_endpoint(client):
    """Test GET /api/v1/agronomy/recommendations endpoint."""
    resp = client.get("/api/v1/agronomy/recommendations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert "standardsSources" in data
    assert "summaryStats" in data
    assert len(data["recommendations"]) == len(RECOMMENDATIONS_REGISTRY)


def test_api_agronomy_recommendations_by_disease(client):
    """Test GET /api/v1/agronomy/recommendations/{disease_key}."""
    resp = client.get("/api/v1/agronomy/recommendations/FruitRot")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["diseaseKey"] == "FruitRot"
    assert len(data["actionableTreatments"]) > 0
    assert len(data["records"]) > 0

    # 404 for unknown disease
    resp_404 = client.get("/api/v1/agronomy/recommendations/UnknownDisease123")
    assert resp_404.status_code == 404


def test_api_agronomy_pesticides_endpoint(client):
    """Test GET /api/v1/agronomy/pesticides returns audited data with blocked items."""
    resp = client.get("/api/v1/agronomy/pesticides")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["auditStatus"] == "AUDITED_AGAINST_ICAR_CPCRI_AND_CIBRC"
    assert len(data["verifiedChemicals"]) >= 5
    assert len(data["blockedOrRestrictedChemicals"]) >= 4

    # Ensure Chlorpyrifos and Calixin are in blocked list
    blocked_chems = [b["chemical"] for b in data["blockedOrRestrictedChemicals"]]
    assert any("Chlorpyrifos" in c for c in blocked_chems)
    assert any("Tridemorph" in c or "Calixin" in c for c in blocked_chems)


def test_health_endpoint_reports_honest_readiness(client):
    """Test /health and /api/v1/health truthfully report model and dataset readiness."""
    for path in ["/health", "/api/v1/health"]:
        resp = client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["yolo_readiness"] == "requires_reannotation_and_retraining"
        assert data["dataset_status"] == "gated_pending_annotations"
        assert data["pending_annotations_count"] == 163
        assert data["training_blocked"] is True
        assert "ZeroBox_Localization_Check" in data["active_safeguards"]
        assert "Audited_Recommendation_Registry" in data["active_safeguards"]


def test_dashboard_kpi_does_not_claim_model_accuracy(client):
    response = client.get("/api/v1/dashboard/kpi")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["aiAccuracy"] is None
    assert data["dataSource"] in {"recorded", "demo_preview"}
    assert isinstance(data["todayScansCount"], int)
    if data["dataSource"] == "demo_preview":
        assert data["dataNote"]


def test_weather_endpoint_includes_live_and_source_flags(client):
    """Test /api/v1/weather reports dataSource and isLive flag."""
    resp = client.get("/api/v1/weather")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "isLive" in data
    assert "dataSource" in data
    assert isinstance(data["isLive"], bool)


def test_assistant_chat_advises_audited_guidance(client):
    """Test /api/v1/assistant/chat returns ICAR-CPCRI audited responses."""
    # Koleroga query
    resp = client.post("/api/v1/assistant/chat", json={"message": "What is the spray for Koleroga fruit rot?"})
    assert resp.status_code == 200
    reply = resp.json()["data"]["reply"]
    assert "Bordeaux" in reply
    assert "ICAR-CPCRI" in reply

    # Phytoplasma query
    resp_py = client.post("/api/v1/assistant/chat", json={"message": "Can I spray fungicide for yellow leaf disease phytoplasma?"})
    assert resp_py.status_code == 200
    reply_py = resp_py.json()["data"]["reply"]
    assert "ineffective" in reply_py or "prohibited" in reply_py or "Nutrient" in reply_py

    # Stem bleeding query
    resp_sb = client.post("/api/v1/assistant/chat", json={"message": "What is the treatment for stem bleeding?"})
    assert resp_sb.status_code == 200
    reply_sb = resp_sb.json()["data"]["reply"]
    assert "chisel" in reply_sb.lower()
    assert "review" in reply_sb.lower()
    assert "prohibited" in reply_sb.lower()


def test_stem_bleeding_recommendation_status():
    """Verify REC-SB-01 is REVIEW_REQUIRED and actionable chemical is withheld."""
    records = get_recommendations_for_disease("StemBleeding")
    rec_sb_01 = next(r for r in records if r.id == "REC-SB-01")
    assert rec_sb_01.verification_status == VerificationStatus.REVIEW_REQUIRED
    assert rec_sb_01.actionable_chemical_allowed is False
    assert rec_sb_01.active_ingredient is None
    assert rec_sb_01.dosage_per_liter is None
    assert "chisel" in rec_sb_01.guidance_text.lower()

    rec_sb_02 = next(r for r in records if r.id == "REC-SB-02")
    assert rec_sb_02.verification_status == VerificationStatus.OUTDATED_REVIEW_REQUIRED
    assert rec_sb_02.actionable_chemical_allowed is False
    assert "banned" in rec_sb_02.guidance_text.lower() or "banned" in rec_sb_02.safety_caveats[0].lower()

    # Actionable treatments for StemBleeding should withhold chemical paste application
    treatments = get_actionable_treatments("StemBleeding")
    assert len(treatments) >= 1
    assert any("not shown" in t.lower() or "could not be verified" in t.lower() for t in treatments)


def test_fertilizer_and_nutrient_registry_integrity():
    """Verify all fertilizer and nutrient recommendations follow ICAR-CPCRI standards and safety limits."""
    # 1. Healthy palms routine NPK schedule (REC-HLT-01)
    rec_hlt = next(r for r in RECOMMENDATIONS_REGISTRY if r.id == "REC-HLT-01")
    assert rec_hlt.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert rec_hlt.category == RecommendationCategory.NUTRIENT_MANAGEMENT
    assert "100g N, 40g P2O5, 140g K2O" in rec_hlt.active_ingredient
    assert "220g Urea" in rec_hlt.formulation
    assert "200g Rock Phosphate" in rec_hlt.formulation
    assert "235g Muriate of Potash" in rec_hlt.formulation
    assert "ICAR" in rec_hlt.source_organization

    # 2. Nut cracking Borax application (REC-NC-01)
    rec_nc = next(r for r in RECOMMENDATIONS_REGISTRY if r.id == "REC-NC-01")
    assert rec_nc.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert rec_nc.category == RecommendationCategory.NUTRIENT_MANAGEMENT
    assert "15g to 20g" in rec_nc.dosage_per_palm
    assert any("25g" in c for c in rec_nc.safety_caveats)

    # 3. Phytoplasma Yellow Leaf Disease sustenance (REC-YLD-01) - NOT A CURE
    rec_yld = next(r for r in RECOMMENDATIONS_REGISTRY if r.id == "REC-YLD-01")
    assert rec_yld.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert "100g Magnesium Sulphate" in rec_yld.dosage_per_palm
    assert "50g Zinc Sulphate" in rec_yld.dosage_per_palm
    # Must explicitly state that it is supportive and NOT a cure
    assert "not a cure" in rec_yld.safety_caveats[1].lower() or "no chemical cure" in rec_yld.title.lower()
    assert "no chemical cure" in rec_yld.guidance_text.lower()

    # 4. Yellow Leaf nutritional chlorosis / drainage (REC-YL-01)
    rec_yl = next(r for r in RECOMMENDATIONS_REGISTRY if r.id == "REC-YL-01")
    assert rec_yl.verification_status == VerificationStatus.VERIFIED_OFFICIAL
    assert rec_yl.category == RecommendationCategory.NUTRIENT_MANAGEMENT
    assert "500g Dolomite" in rec_yl.dosage_per_palm
    assert "50g Zinc Sulphate" in rec_yl.dosage_per_palm


def test_fertilizer_plan_api_endpoint(client):
    """Test GET /api/v1/agronomy/fertilizer-plan computes exact ICAR-CPCRI quantities."""
    # Test mature bearing palms (default 500 palms)
    resp = client.get("/api/v1/agronomy/fertilizer-plan?palms=500&age=mature")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["palms"] == 500
    assert data["annualRequirement"]["ureaKg"] == 110.0  # 500 * 220g / 1000
    assert data["annualRequirement"]["rockPhosphateKg"] == 100.0  # 500 * 200g / 1000
    assert data["annualRequirement"]["muriateOfPotashKg"] == 117.5  # 500 * 235g / 1000
    assert data["annualRequirement"]["farmyardManureTons"] == 6.0  # 500 * 12kg / 1000

    # Test age scaling for 1st year palms (25% dose)
    resp_y1 = client.get("/api/v1/agronomy/fertilizer-plan?palms=400&age=year1")
    assert resp_y1.status_code == 200
    data_y1 = resp_y1.json()["data"]
    assert data_y1["annualRequirement"]["ureaKg"] == 22.0  # 400 * 220 * 0.25 / 1000
    assert data_y1["annualRequirement"]["rockPhosphateKg"] == 20.0  # 400 * 200 * 0.25 / 1000
    assert data_y1["annualRequirement"]["muriateOfPotashKg"] == 23.5  # 400 * 235 * 0.25 / 1000
    assert data_y1["annualRequirement"]["farmyardManureTons"] == 1.2  # 400 * 12 * 0.25 / 1000


