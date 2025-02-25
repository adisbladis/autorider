from autorider import pep517
import pytest


def test_get():
    assert pep517.get_build_systems(
        {
            "build-system": {
                "requires": ["flit-core"],
            },
        }
    ) == ["flit-core"]


def test_fallback():
    assert pep517.get_build_systems({}) == ["setuptools"]


def test_fallback_requires():
    assert pep517.get_build_systems(
        {
            "build-system": {},
        }
    ) == ["setuptools"]


def test_invalid_type():
    with pytest.raises(ValueError):
        assert pep517.get_build_systems(
            {
                "build-system": {
                    "requires": "flit-core",  # pyright: ignore[reportArgumentType]
                },
            }
        )
