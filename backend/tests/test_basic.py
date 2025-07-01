"""
Basic test to verify pytest setup.
"""
import pytest


def test_basic_math():
    """Basic test to verify pytest is working."""
    assert 1 + 1 == 2


def test_fixtures_work(sample_teacher_data):
    """Test that fixtures are working."""
    assert sample_teacher_data["code"] == "T001"
    assert sample_teacher_data["first_name"] == "John" 