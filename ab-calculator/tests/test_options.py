"""Tests for engine/options.py: v1 accepts only PM defaults (SPEC Step 0)."""

import pytest

from engine import options


@pytest.mark.parametrize(
    "name,value",
    [("ci_method", "wald"), ("alternative", "two-sided"), ("ni_method", "standard")],
)
def test_defaults_are_allowed(name, value):
    options.require_v1(name, value)


@pytest.mark.parametrize(
    "name,value",
    [("ci_method", "newcombe"), ("alternative", "greater"), ("ni_method", "advanced")],
)
def test_expert_options_raise(name, value):
    with pytest.raises(NotImplementedError, match="Expert-mode option"):
        options.require_v1(name, value)
