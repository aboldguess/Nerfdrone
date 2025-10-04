"""Mini README: Tests for the drone provider registry.

Ensures that providers register correctly and instantiation works as
expected, providing a quick regression suite for the plugin system.
"""

from nerfdrone.drone_control import REGISTRY, DroneControlProvider


def test_registry_contains_dji_provider():
    assert "dji" in REGISTRY.available_providers()


def test_registry_instantiates_provider():
    provider = REGISTRY.create("dji")
    assert isinstance(provider, DroneControlProvider)
    assert provider.provider_name == "dji"
