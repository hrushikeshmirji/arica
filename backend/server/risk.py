"""
server/risk.py — Live Epidemiological Infection Risk & Microclimate Disease Forecasting Engine.

Implements botanical & phytosanitary models for Areca catechu plantations:
- Fruit Rot / Koleroga (Phytophthora meadii) infection pressure index
- Anthracnose Blight (Colletotrichum gloeosporioides) index
- Physiological Nut Cracking moisture shock index
- 7-Day predictive infection trajectory
- Block-by-block vulnerability matrix
- Prophylactic spraying window determination
"""

import math
from datetime import datetime, timedelta
from typing import Any

def calculate_epidemiological_risk(
    weather_data: dict[str, Any],
    blocks_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Computes real-time epidemiological disease risk from live microclimate telemetry
    and active plantation block conditions.
    """
    humidity = float(weather_data.get("humidity", 82))
    temp = float(weather_data.get("temperature", 25))
    rainfall = float(weather_data.get("rainfall", 12))
    wind = float(weather_data.get("windSpeed", 10))

    # --- 1. Koleroga (Fruit Rot) Pathogen Model ---
    # Phytophthora meadii sporangia sporulate rapidly when RH > 85% and rainfall is frequent.
    rh_factor_koleroga = max(0.0, (humidity - 68.0) / 32.0) # 0 to 1
    rain_factor_koleroga = min(1.0, rainfall / 25.0)
    temp_factor_koleroga = 1.0 - (abs(temp - 24.5) / 10.0) # Optimal at 24.5°C
    temp_factor_koleroga = max(0.2, min(1.0, temp_factor_koleroga))

    koleroga_score = round(
        (rh_factor_koleroga * 45.0 + rain_factor_koleroga * 35.0 + temp_factor_koleroga * 20.0), 1
    )
    koleroga_score = max(8.0, min(98.5, koleroga_score))

    # --- 2. Anthracnose (Colletotrichum) Model ---
    # Thrives in warm, humid conditions with splashing rain
    rh_factor_anthracnose = max(0.0, (humidity - 60.0) / 35.0)
    temp_factor_anthracnose = max(0.0, 1.0 - (abs(temp - 28.0) / 8.0))
    wind_splash_factor = min(1.0, (wind + rainfall) / 30.0)

    anthracnose_score = round(
        (rh_factor_anthracnose * 40.0 + temp_factor_anthracnose * 40.0 + wind_splash_factor * 20.0), 1
    )
    anthracnose_score = max(5.0, min(95.0, anthracnose_score))

    # --- 3. Nut Cracking Physiological Shock Model ---
    # Driven by rapid changes in moisture and temperature swings
    nut_cracking_score = round(min(85.0, max(10.0, abs(temp - 22.0) * 4.0 + (rainfall > 20.0 and 25.0 or 5.0))), 1)

    # Composite overall infection pressure
    composite_index = round((koleroga_score * 0.45 + anthracnose_score * 0.35 + nut_cracking_score * 0.20), 1)

    if composite_index >= 75.0:
        overall_severity = "Critical"
        advisory_headline = "Urgent: High Fungal Infection Pressure Alert"
        advisory_action = "Apply 1% Bordeaux mixture prophylactic canopy spray immediately before next rainfall."
    elif composite_index >= 50.0:
        overall_severity = "Severe"
        advisory_headline = "Moderate-to-High Pathogen Germination Risk"
        advisory_action = "Inspect canopy crowns in valley blocks and prepare systemic copper fungicide."
    elif composite_index >= 30.0:
        overall_severity = "Moderate"
        advisory_headline = "Favorable Canopy Vigor with Low Sporulation"
        advisory_action = "Maintain standard orchard hygiene and ensure drainage ditches remain clear."
    else:
        overall_severity = "Healthy"
        advisory_headline = "Optimal Plantation Health & Microclimate"
        advisory_action = "Continue regular seasonal fertigation schedule."

    # --- 4. 7-Day Risk Trajectory Projection ---
    forecast_list = weather_data.get("forecast", [])
    seven_day_trajectory = []
    base_date = datetime.now()

    days_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today_idx = base_date.weekday()

    for i in range(7):
        day_date = base_date + timedelta(days=i)
        day_name = days_names[(today_idx + i) % 7]
        fc_item = forecast_list[i] if i < len(forecast_list) else None

        day_rain_prob = fc_item.get("rainProb", 50) if fc_item else 40
        # Dynamic variation based on projected rain
        fluctuation = (day_rain_prob - 50) * 0.35

        d_koleroga = round(max(10.0, min(99.0, koleroga_score + fluctuation + (i * 1.5))), 1)
        d_anthracnose = round(max(10.0, min(95.0, anthracnose_score + (fluctuation * 0.8))), 1)
        d_nut_crack = round(max(5.0, min(80.0, nut_cracking_score - (i * 0.8))), 1)

        seven_day_trajectory.append({
            "day": day_name,
            "date": day_date.strftime("%b %d"),
            "kolerogaRisk": d_koleroga,
            "anthracnoseRisk": d_anthracnose,
            "nutCrackingRisk": d_nut_crack,
            "rainProbability": day_rain_prob,
        })

    # --- 5. Block Vulnerability Matrix ---
    block_vulnerability = []
    for b in blocks_data:
        b_id = b.get("id", "Block")
        b_name = b.get("name", b_id)
        b_trees = b.get("trees", 1500)
        b_health = b.get("healthScore", b.get("health", 80))
        b_disease = b.get("primaryDisease", "None")

        # Valley/Lowland blocks have +10% higher humidity risk
        is_valley = "valley" in b_name.lower() or "river" in b_name.lower() or "c" in b_id.lower()
        block_risk_score = round(min(100.0, (100.0 - b_health) * 0.7 + (is_valley and 25.0 or 10.0) + (koleroga_score * 0.3)), 1)

        if block_risk_score >= 70:
            b_status = "High Vulnerability"
            b_badge = "Critical"
        elif block_risk_score >= 45:
            b_status = "Moderate Alert"
            b_badge = "Warning"
        else:
            b_status = "Resilient"
            b_badge = "Healthy"

        block_vulnerability.append({
            "blockId": b_id,
            "name": b_name,
            "trees": b_trees,
            "healthScore": b_health,
            "vulnerabilityScore": block_risk_score,
            "primaryThreat": b_disease if b_disease != "None" else ("Fruit Rot" if is_valley else "Anthracnose"),
            "status": b_status,
            "severity": b_badge,
        })

    # Sort blocks by vulnerability descending
    block_vulnerability.sort(key=lambda x: x["vulnerabilityScore"], reverse=True)

    # --- 6. Prophylactic Spraying Window Recommendation ---
    # Best spray window: days with rain probability < 40%
    optimal_spray_days = [
        d["day"] for d in seven_day_trajectory if d["rainProbability"] < 45
    ]
    spray_recommendation = {
        "suitableWindow": ", ".join(optimal_spray_days) if optimal_spray_days else "Immediate early morning window",
        "recommendedChemical": "1% Bordeaux Mixture (10g Copper Sulphate + 10g Quick Lime per 1L) with resin sticker",
        "organicAlternative": "Pseudomonas fluorescens (10g/L) + Trichoderma viride soil application",
        "withholdingPeriodDays": 14,
    }

    return {
        "compositeIndex": composite_index,
        "overallSeverity": overall_severity,
        "advisoryHeadline": advisory_headline,
        "advisoryAction": advisory_action,
        "pathogenMetrics": {
            "koleroga": {
                "name": "Koleroga / Fruit Rot (Phytophthora meadii)",
                "riskScore": koleroga_score,
                "status": "Critical" if koleroga_score >= 75 else "High" if koleroga_score >= 50 else "Moderate",
                "incubationDays": 4,
            },
            "anthracnose": {
                "name": "Anthracnose Blight (Colletotrichum gloeosporioides)",
                "riskScore": anthracnose_score,
                "status": "Critical" if anthracnose_score >= 75 else "High" if anthracnose_score >= 50 else "Moderate",
                "incubationDays": 7,
            },
            "nutCracking": {
                "name": "Nut Cracking & Splitting Disorder",
                "riskScore": nut_cracking_score,
                "status": "Moderate" if nut_cracking_score >= 40 else "Low",
                "incubationDays": 2,
            },
        },
        "trajectory": seven_day_trajectory,
        "blockVulnerability": block_vulnerability,
        "spraySchedule": spray_recommendation,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
    }
