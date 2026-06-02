_CLEAN_ROW_THRESHOLD = 2000
_ANOMALY_RATE_MAX = 0.10


def should_retrain(
    drift_detected: bool,
    clean_row_count: int,
    total_row_count: int,
) -> bool:
    if not drift_detected:
        return False
    if clean_row_count < _CLEAN_ROW_THRESHOLD:
        return False
    if total_row_count == 0:
        return False
    anomaly_rate = 1.0 - (clean_row_count / total_row_count)
    return anomaly_rate < _ANOMALY_RATE_MAX
