"""Sensor for Home Assistant analytics."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AnalyticsInsightsData
from .const import DOMAIN
from .coordinator import AnalyticsData, HomeassistantAnalyticsDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class AnalyticsSensorEntityDescription(SensorEntityDescription):
    """Analytics sensor entity description."""

    value_fn: Callable[[AnalyticsData], StateType]


def get_core_integration_entity_description(
    domain: str, name: str
) -> AnalyticsSensorEntityDescription:
    """Get core integration entity description."""
    return AnalyticsSensorEntityDescription(
        key=f"core_{domain}_active_installations",
        translation_key="core_integrations",
        name=name,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="active installations",
        value_fn=lambda data: data.core_integrations.get(domain),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize the entries."""

    analytics_data: AnalyticsInsightsData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HomeassistantAnalyticsSensor(
            analytics_data.coordinator,
            get_core_integration_entity_description(
                integration_domain, analytics_data.names[integration_domain]
            ),
        )
        for integration_domain in analytics_data.coordinator.data.core_integrations
    )


class HomeassistantAnalyticsSensor(
    CoordinatorEntity[HomeassistantAnalyticsDataUpdateCoordinator], SensorEntity
):
    """Home Assistant Analytics Sensor."""

    _attr_has_entity_name = True

    entity_description: AnalyticsSensorEntityDescription

    def __init__(
        self,
        coordinator: HomeassistantAnalyticsDataUpdateCoordinator,
        entity_description: AnalyticsSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = entity_description.key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, DOMAIN)},
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
