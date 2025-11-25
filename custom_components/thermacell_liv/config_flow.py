"""Config flow for Thermacell LIV integration."""

from __future__ import annotations

import logging
from typing import Any

from pythermacell import AuthenticationError, ThermacellClient, ThermacellConnectionError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Test-before-setup validation (Bronze tier requirement):
    1. Authenticate with credentials to verify they are valid
    2. Test API connectivity by fetching user devices
    3. Only proceed to setup if both tests pass

    Raises:
        InvalidAuth: If credentials are invalid or authentication fails
        CannotConnect: If API is unreachable or user has no devices

    Returns:
        dict: Validation info with integration title
    """
    session = async_get_clientsession(hass)

    try:
        async with ThermacellClient(
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
            session=session,
        ) as client:
            # Test authentication and connection by fetching devices
            devices = await client.get_devices()

            if not devices:
                _LOGGER.error(
                    "Connection test failed - no devices found for user: %s",
                    data[CONF_USERNAME],
                )
                raise CannotConnect

            _LOGGER.info(
                "Validation successful for user: %s (%d devices)",
                data[CONF_USERNAME],
                len(devices),
            )
            return {"title": "Thermacell LIV"}

    except AuthenticationError as err:
        _LOGGER.error(
            "Authentication failed - invalid credentials for user: %s - %s",
            data[CONF_USERNAME],
            err,
        )
        raise InvalidAuth from err
    except ThermacellConnectionError as err:
        _LOGGER.error(
            "Connection test failed - unable to reach Thermacell API for user: %s - %s",
            data[CONF_USERNAME],
            err,
        )
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error(
            "Unexpected error during validation for user: %s - %s",
            data[CONF_USERNAME],
            err,
        )
        raise CannotConnect from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Thermacell LIV."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ThermacellLivOptionsFlow(config_entry)

    async def async_step_reauth(self, _entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauthentication request."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Confirm reauthentication with new credentials."""
        errors = {}

        if user_input is not None:
            # Get the existing entry
            existing_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

            # Validate new credentials
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reauth")
                errors["base"] = "unknown"
            else:
                # Update the config entry with new credentials
                self.hass.config_entries.async_update_entry(
                    existing_entry,
                    data=user_input,
                )
                await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        # Show the reauth form
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"account": self.context.get("unique_id", "Unknown")},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        errors = {}

        # Check for duplicate entries (unique-config-entry requirement)
        # Use username as unique identifier
        await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
        self._abort_if_unique_id_configured()

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)


class ThermacellLivOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Thermacell LIV."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options or use defaults
        options = {
            "scan_interval": self.config_entry.options.get("scan_interval", 60),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=options["scan_interval"],
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=300)),
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
