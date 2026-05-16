import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *

MANUFACTURER = "Lemcke Solutions"


class SaltSentryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        self._host = ""

    async def async_step_zeroconf(self, discovery_info):
        """Handle zeroconf discovery."""
        host = discovery_info.host
        device_id = discovery_info.properties.get("id")

        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._host = host
        self.context["title_placeholders"] = {
            "host": host,
            "name": MANUFACTURER,
        }

        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None):
        """Bevestigingsstap na zeroconf discovery."""
        if user_input is not None:
            return await self.async_step_user()

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={
                "host": self._host,
                "name": MANUFACTURER,
            },
        )

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._unit = user_input[CONF_UNIT]
            self._softeners = await async_load_softeners(self.hass)
            self._softener_type = user_input["softener_type"]
            return await self.async_step_distances()

        softeners = await async_load_softeners(self.hass)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=getattr(self, "_host", "")): str,
                vol.Required(CONF_UNIT, default=UNIT_CM): vol.In([UNIT_CM, UNIT_INCH]),
                vol.Required("softener_type"): vol.In({
                    k: v["name"] for k, v in softeners.items()
                }),
            }),
        )

    async def async_step_distances(self, user_input=None):
        errors = {}
        preset = self._softeners[self._softener_type]

        default_full = cm_to_unit(preset["full_cm"], self._unit) or 0
        default_empty = cm_to_unit(preset["empty_cm"], self._unit) or 0

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
                    }
                )

        return self.async_show_form(
            step_id="distances",
            data_schema=vol.Schema({
                vol.Required(CONF_FULL, default=default_full): vol.Coerce(float),
                vol.Required(CONF_EMPTY, default=default_empty): vol.Coerce(float),
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
            }),
            errors=errors,
            description_placeholders={
                "model": self._softeners[self._softener_type]["name"]
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SaltSentryOptionsFlow(config_entry)


class SaltSentryOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        current = {**self._config_entry.data, **self._config_entry.options}
        softeners = await async_load_softeners(self.hass)

        if user_input is not None:
            self._unit = user_input[CONF_UNIT]
            self._softener_type = user_input["softener_type"]
            return await self.async_step_distances()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_UNIT, default=current.get(CONF_UNIT, UNIT_CM)): vol.In([UNIT_CM, UNIT_INCH]),
                vol.Required("softener_type", default=current.get("softener_type", "other")): vol.In({
                    k: v["name"] for k, v in softeners.items()
                }),
            }),
        )

    async def async_step_distances(self, user_input=None):
        errors = {}
        current = {**self._config_entry.data, **self._config_entry.options}
        softeners = await async_load_softeners(self.hass)

        preset = softeners[self._softener_type]

        default_full = current.get(CONF_FULL) or cm_to_unit(preset["full_cm"], self._unit) or 0
        default_empty = current.get(CONF_EMPTY) or cm_to_unit(preset["empty_cm"], self._unit) or 0

        if user_input is not None:
            full = float(user_input[CONF_FULL])
            empty = float(user_input[CONF_EMPTY])

            if empty <= full:
                errors["full_distance"] = "error_full_gt_empty"
            else:
                new_options = {
                    **current,
                    CONF_UNIT: self._unit,
                    "softener_type": self._softener_type,
                    CONF_FULL: full,
                    CONF_EMPTY: empty,
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                }
                return self.async_create_entry(title="", data=new_options)

        return self.async_show_form(
            step_id="distances",
            data_schema=vol.Schema({
                vol.Required(CONF_FULL, default=default_full): vol.Coerce(float),
                vol.Required(CONF_EMPTY, default=default_empty): vol.Coerce(float),
                vol.Required(CONF_SCAN_INTERVAL, default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.Coerce(int),
            }),
            errors=errors,
            description_placeholders={
                "model": softeners[self._softener_type]["name"]
            },
        )