"""Config flow for the Salt Sentry integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

if TYPE_CHECKING:
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pysaltsentry import SaltSentryDevice, SaltSentryError

from .coordinator import SaltSentryConfigEntry

from .const import (
    CONF_CORRECTION,
    CONF_EMPTY,
    CONF_FULL,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_UNIT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    UNIT_CM,
    UNIT_INCH,
    async_load_softeners,
    cm_to_unit,
)

MANUFACTURER = "Lemcke Solutions"


class SaltSentryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Salt Sentry."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str = ""
        self._unit: str = UNIT_CM
        self._softener_type: str = ""
        self._softeners: dict[str, Any] = {}

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a device discovered via zeroconf."""
        host: str = discovery_info.host
        device_id: str | None = discovery_info.properties.get("id")

        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host}, reload_on_update=True)

        self._host = host
        self.context["title_placeholders"] = {"host": host, "name": MANUFACTURER}

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user to confirm a zeroconf-discovered device."""
        if user_input is not None:
            return await self.async_step_user()

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"host": self._host, "name": MANUFACTURER},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step."""
        errors: dict[str, str] = {}
        softeners = await async_load_softeners(self.hass)

        if user_input is not None:
            host: str = user_input[CONF_HOST]
            try:
                status = await SaltSentryDevice(host, async_get_clientsession(self.hass)).get_status()
                await self.async_set_unique_id(status.unique_id)
                self._abort_if_unique_id_configured()
            except SaltSentryError:
                errors["base"] = "cannot_connect"

            if not errors:
                self._host = host
                self._unit = user_input[CONF_UNIT]
                self._softeners = softeners
                self._softener_type = user_input["softener_type"]
                return await self.async_step_distances()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=self._host): str,
                vol.Required(CONF_UNIT, default=UNIT_CM): vol.In([UNIT_CM, UNIT_INCH]),
                vol.Required("softener_type"): vol.In({k: v["name"] for k, v in softeners.items()}),
            }),
            errors=errors,
        )

    async def async_step_distances(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the distance configuration step."""
        errors: dict[str, str] = {}
        preset = self._softeners[self._softener_type]

        default_full: float = cm_to_unit(preset["full_cm"], self._unit) or 0.0
        default_empty: float = cm_to_unit(preset["empty_cm"], self._unit) or 0.0

        if user_input is not None:
            full = float(user_input[CONF_FULL])
            empty = float(user_input[CONF_EMPTY])

            if empty <= full:
                errors["full_distance"] = "error_full_gt_empty"
            else:
                return self.async_create_entry(
                    title=f"Salt Sentry ({self._host})",
                    data={
                        CONF_HOST: self._host,
                        CONF_UNIT: self._unit,
                        "softener_type": self._softener_type,
                        CONF_FULL: full,
                        CONF_EMPTY: empty,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="distances",
            data_schema=vol.Schema({
                vol.Required(CONF_FULL, default=default_full): vol.Coerce(float),
                vol.Required(CONF_EMPTY, default=default_empty): vol.Coerce(float),
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
            }),
            errors=errors,
            description_placeholders={"model": self._softeners[self._softener_type]["name"]},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the device IP address."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            host: str = user_input[CONF_HOST]
            try:
                await SaltSentryDevice(host, async_get_clientsession(self.hass)).get_status()
            except SaltSentryError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data_updates={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=reconfigure_entry.data.get(CONF_HOST, "")): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: SaltSentryConfigEntry) -> SaltSentryOptionsFlow:
        """Return the options flow handler."""
        return SaltSentryOptionsFlow(config_entry)


class SaltSentryOptionsFlow(config_entries.OptionsFlow):
    """Handle the options flow for Salt Sentry."""

    def __init__(self, config_entry: SaltSentryConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry
        self._unit: str = UNIT_CM
        self._softener_type: str = ""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial options step."""
        current: dict[str, Any] = {**self._config_entry.data, **self._config_entry.options}
        softeners = await async_load_softeners(self.hass)

        if user_input is not None:
            self._unit = user_input[CONF_UNIT]
            self._softener_type = user_input["softener_type"]
            return await self.async_step_distances()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_UNIT, default=current.get(CONF_UNIT, UNIT_CM)): vol.In([UNIT_CM, UNIT_INCH]),
                vol.Required("softener_type", default=current.get("softener_type", "other")): vol.In(
                    {k: v["name"] for k, v in softeners.items()}
                ),
            }),
        )

    async def async_step_distances(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the distance options step."""
        errors: dict[str, str] = {}
        current: dict[str, Any] = {**self._config_entry.data, **self._config_entry.options}
        softeners = await async_load_softeners(self.hass)
        preset = softeners[self._softener_type]

        default_full: float = current.get(CONF_FULL) or cm_to_unit(preset["full_cm"], self._unit) or 0.0
        default_empty: float = current.get(CONF_EMPTY) or cm_to_unit(preset["empty_cm"], self._unit) or 0.0

        if user_input is not None:
            full = float(user_input[CONF_FULL])
            empty = float(user_input[CONF_EMPTY])

            if empty <= full:
                errors["full_distance"] = "error_full_gt_empty"
            else:
                return self.async_create_entry(title="", data={
                    **current,
                    CONF_UNIT: self._unit,
                    "softener_type": self._softener_type,
                    CONF_FULL: full,
                    CONF_EMPTY: empty,
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                })

        return self.async_show_form(
            step_id="distances",
            data_schema=vol.Schema({
                vol.Required(CONF_FULL, default=default_full): vol.Coerce(float),
                vol.Required(CONF_EMPTY, default=default_empty): vol.Coerce(float),
                vol.Required(CONF_SCAN_INTERVAL, default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.Coerce(int),
            }),
            errors=errors,
            description_placeholders={"model": softeners[self._softener_type]["name"]},
        )
