import os


def wh_to_cost(predicted_wh: float) -> tuple[float, float]:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    kwh = predicted_wh / 1000.0
    cost = round(kwh * tariff, 2)
    return kwh, cost


def project_monthly_bill(forecast: list[dict]) -> dict:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    scale = 30 / 7
    optimistic_ngn = round(
        sum(r["lower_wh"] for r in forecast) / 1000 * scale * tariff, 2
    )
    most_likely_ngn = round(
        sum(r["predicted_wh"] for r in forecast) / 1000 * scale * tariff, 2
    )
    pessimistic_ngn = round(
        sum(r["upper_wh"] for r in forecast) / 1000 * scale * tariff, 2
    )
    return {
        "optimistic_ngn": optimistic_ngn,
        "most_likely_ngn": most_likely_ngn,
        "pessimistic_ngn": pessimistic_ngn,
    }
