# docs/architecture.md â€” Diagonally Energy Prediction
<!-- TODO: Fill after running /write-specs -->

## Data Flow
raw txt file â†’ data_loader.py â†’ features.py â†’ features.csv â†’ train.py â†’ model.joblib
                                                                              â†“
                                                           predict.py â† routes.py â† API request
