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
        """Handle the manual/user step."""
        errors = {}
        host = (user_input.get(CONF_HOST) if user_input else None) or getattr(self, "_host", "")

        if user_input is not None and CONF_FULL in user_input and CONF_EMPTY in user_input:
            full = float(user_input[CONF_FULL])
            empty = float(user_input[CONF_EMPTY])
            if empty <= full:
                errors["full_distance"] = "error_full_gt_empty"
            else:
                return self.async_create_entry(
                    title=f"Salt Sentry ({host})",
                    data=user_input
                )

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_UNIT, default=user_input.get(CONF_UNIT, UNIT_CM) if user_input else UNIT_CM): vol.In([UNIT_CM, UNIT_INCH]),
            vol.Required(CONF_FULL, default=user_input.get(CONF_FULL, 0) if user_input else 0): vol.Coerce(float),
            vol.Required(CONF_EMPTY, default=user_input.get(CONF_EMPTY, 0) if user_input else 0): vol.Coerce(float),
            vol.Required(CONF_SCAN_INTERVAL, default=user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL) if user_input else DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"host": host},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SaltSentryOptionsFlow(config_entry)


class SaltSentryOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            full = float(user_input[CONF_FULL])
            empty = float(user_input[CONF_EMPTY])
            if empty <= full:
                errors["full_distance"] = "error_full_gt_empty"
            else:
                new_options = {**current, **user_input}
                return self.async_create_entry(title=self._config_entry.title, data=new_options)

        schema = vol.Schema({
            vol.Required(CONF_UNIT, default=current.get(CONF_UNIT, UNIT_CM)): vol.In([UNIT_CM, UNIT_INCH]),
            vol.Required(CONF_FULL, default=current.get(CONF_FULL, 0)): vol.Coerce(float),
            vol.Required(CONF_EMPTY, default=current.get(CONF_EMPTY, 0)): vol.Coerce(float),
            vol.Required(CONF_SCAN_INTERVAL, default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.Coerce(int),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )