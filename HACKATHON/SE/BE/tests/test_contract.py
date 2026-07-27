import json
import math

import pytest
from pydantic import ValidationError

from app.domain.schemas.ai_contract import AITrip


def test_ai_payload_round_trip_preserves_source_fields(sample_ai_payload):
    trip = AITrip.model_validate(sample_ai_payload)
    serialized = json.loads(trip.model_dump_json())

    assert math.isinf(trip.frames[0].min_ttc)
    assert serialized["frames"][0]["min_ttc"] == "Infinity"
    assert serialized["frames"][0]["headway_sec"] == "Infinity"
    assert serialized["frames"][0]["risk"] == sample_ai_payload["frames"][0]["risk"]
    assert serialized["frames"][0]["targets"] == [{"id": "motorcycle-1"}]
    assert serialized["frames"][0]["ego"]["world_frame"] == 123
    assert serialized["metadata"]["metadata_extra"] == {"weather": "clear"}
    assert serialized["trip_extra"] == "preserved"


def test_mismatched_trip_ids_are_rejected(sample_ai_payload):
    sample_ai_payload["metadata"]["trip_id"] = "T02d"
    with pytest.raises(ValidationError):
        AITrip.model_validate(sample_ai_payload)


@pytest.mark.parametrize(
    ("field_path", "invalid_value"),
    [
        (("frames", 0, "driver", "state"), "unknown"),
        (("frames", 0, "driver", "alertness_score"), 1.1),
        (("frames", 0, "ego", "speed_kmh"), -1),
        (("frames", 0, "risk", "final_risk_score"), 101),
        (("frames", 0, "min_ttc"), math.nan),
        (("frames", 0, "headway_sec"), -math.inf),
    ],
)
def test_invalid_ai_values_are_rejected(sample_ai_payload, field_path, invalid_value):
    target = sample_ai_payload
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = invalid_value

    with pytest.raises(ValidationError):
        AITrip.model_validate(sample_ai_payload)
