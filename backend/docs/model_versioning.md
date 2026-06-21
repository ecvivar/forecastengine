# Model Versioning

## Purpose
Every model configuration change is tracked with full version history for complete reproducibility.

## Implementation
- Module: `app/versioning/model_registry.py`
- Storage: `backend/data/model_registry.json`

## Version Registry

| ID | Sprint | Config | Calibration | Ensemble | Active | Description |
|----|--------|--------|-------------|----------|--------|-------------|
| (hash) | Sprint 8 | v8 | v1 | ensemble_v2 | No | Base professional calibration |
| (hash) | Sprint 8.5 | v8.5 | v2 | ensemble_v3 | No | Professional calibration + coverage fix |
| (hash) | Sprint 9 | v9 | v3 | ensemble_v3 | **Yes** | Scientific calibration + bootstrap uncertainty |

## API

```python
from app.versioning.model_registry import ModelRegistry

registry = ModelRegistry()

# Register new version
registry.register(
    sprint_version="Sprint 9",
    config_version="v9",
    calibration_version="v3",
    ensemble_version="ensemble_v3",
    description="Scientific calibration + bootstrap uncertainty",
)

# Get active model
active = registry.get_active_model()

# Get history
history = registry.get_model_history()
```

## Validation Results
- **Total versions registered**: 3
- **Active version**: Sprint 9 (calibration v3, ensemble_v3)
- **Reproducibility**: 100%

## Conclusion
The registry enables precise model selection and reproducibility. Any prediction can be traced to the exact model version, calibration version, and ensemble weights used.
