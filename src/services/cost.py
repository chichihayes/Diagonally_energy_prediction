import os


def wh_to_cost(predicted_wh: float) -> tuple[float, float]:
    tariff = float(os.environ["ELECTRICITY_TARIFF_NGN_PER_KWH"])
    kwh = predicted_wh / 1000.0
    cost = round(kwh * tariff, 2)
    return kwh, cost
