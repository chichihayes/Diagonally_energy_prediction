import pandas as pd
from src.services.monitor import check_anomaly
from src.services.database import insert_reading, store_anomaly
from src.services.cost import wh_to_cost


def seed_supabase():
    df = pd.read_csv(
        "data/processed/test.csv",
        index_col=0,
        parse_dates=True,
    )

    print(f"Seeding {len(df)} rows into Supabase...")
    anomaly_count = 0

    for i, (timestamp, row) in enumerate(df.iterrows()):

        appliance_values = {
            "Fridge":         float(row["Fridge"]),
            "ChestFreezer":   float(row["ChestFreezer"]),
            "UprightFreezer": float(row["UprightFreezer"]),
            "TumbleDryer":    float(row["TumbleDryer"]),
            "WashingMachine": float(row["WashingMachine"]),
            "Dishwasher":     float(row["Dishwasher"]),
            "Computer":       float(row["Computer"]),
            "Television":     float(row["Television"]),
            "ElectricHeater": float(row["ElectricHeater"]),
            "aggregate_wh":   float(row["aggregate_wh"]),
        }

        monitor_result = check_anomaly(appliance_values)
        _, estimated_cost_gbp = wh_to_cost(appliance_values["aggregate_wh"])

        insert_reading({
            "timestamp":          timestamp.isoformat(),
            "aggregate_wh":       appliance_values["aggregate_wh"],
            "fridge_wh":          appliance_values["Fridge"],
            "chest_freezer_wh":   appliance_values["ChestFreezer"],
            "upright_freezer_wh": appliance_values["UprightFreezer"],
            "tumble_dryer_wh":    appliance_values["TumbleDryer"],
            "washing_machine_wh": appliance_values["WashingMachine"],
            "dishwasher_wh":      appliance_values["Dishwasher"],
            "computer_wh":        appliance_values["Computer"],
            "television_wh":      appliance_values["Television"],
            "electric_heater_wh": appliance_values["ElectricHeater"],
            "estimated_cost_gbp": estimated_cost_gbp,
        })

        if monitor_result["is_anomaly"]:
            anomaly_count += 1
            store_anomaly({
                "timestamp":          timestamp.isoformat(),
                "appliance_values":   appliance_values,
                "z_scores":           monitor_result["z_scores"],
                "flagged_appliances": monitor_result["flagged_appliances"],
            })

        if i % 100 == 0:
            print(f"Progress: {i}/{len(df)} rows inserted...")

    print(f"Done.")
    print(f"Total rows inserted: {len(df)}")
    print(f"Anomalies detected: {anomaly_count}")
    print(f"Anomaly rate: {anomaly_count/len(df)*100:.1f}%")


if __name__ == "__main__":
    seed_supabase()
