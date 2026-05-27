import pytest
from app.core.math_engine import calculate_outcome_float, get_wear_name

def test_calculate_outcome_float_basic():
    inputs = [
        {'float': 0.10, 'min_float': 0.0, 'max_float': 1.0} for _ in range(10)
    ]
    result = calculate_outcome_float(inputs, 0.0, 1.0)
    # the exact float32 value of 0.10 might be slightly different, but since outcome_min=0, outcome_max=1,
    # and all inputs are 0.10 with range 0 to 1, normalized sum is 1.0 (approx), avg is 0.10.
    # We should expect pytest.approx(0.10)
    assert result == pytest.approx(0.10, abs=1e-5)

def test_get_wear_name():
    assert get_wear_name(0.01) == "Factory New"
    assert get_wear_name(0.069) == "Factory New"
    assert get_wear_name(0.07) == "Minimal Wear"
    assert get_wear_name(0.149) == "Minimal Wear"
    assert get_wear_name(0.15) == "Field-Tested"
    assert get_wear_name(0.379) == "Field-Tested"
    assert get_wear_name(0.38) == "Well-Worn"
    assert get_wear_name(0.449) == "Well-Worn"
    assert get_wear_name(0.45) == "Battle-Scarred"
    assert get_wear_name(0.99) == "Battle-Scarred"
