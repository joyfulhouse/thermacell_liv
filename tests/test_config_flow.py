#!/usr/bin/env python3
"""Unit tests for config_flow module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pythermacell import AuthenticationError, ThermacellClient, ThermacellConnectionError

from custom_components.thermacell_liv.config_flow import (
    CannotConnect,
    ConfigFlow,
    InvalidAuth,
    ThermacellLivOptionsFlow,
    validate_input,
)
from custom_components.thermacell_liv.const import CONF_PASSWORD, CONF_USERNAME, DOMAIN


def create_mock_client(devices=None, auth_error=False, connection_error=False):
    """Create a mock ThermacellClient."""
    mock_client = AsyncMock(spec=ThermacellClient)

    async def mock_aenter(*args, **kwargs):
        if auth_error:
            raise AuthenticationError("Invalid credentials")
        if connection_error:
            raise ThermacellConnectionError("Connection failed")
        return mock_client

    mock_client.__aenter__ = mock_aenter
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get_devices = AsyncMock(return_value=devices or [])

    return mock_client


class TestValidateInput:
    """Test validate_input function."""

    @pytest.mark.asyncio
    async def test_validate_input_success(self):
        """Test successful validation."""
        hass = MagicMock()
        data = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        mock_device = MagicMock()
        mock_client = create_mock_client(devices=[mock_device])

        with (
            patch("custom_components.thermacell_liv.config_flow.async_get_clientsession"),
            patch("custom_components.thermacell_liv.config_flow.ThermacellClient", return_value=mock_client),
        ):
            result = await validate_input(hass, data)

            assert result == {"title": "Thermacell LIV (test@example.com)"}
            mock_client.get_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_input_invalid_auth(self):
        """Test validation with invalid credentials."""
        hass = MagicMock()
        data = {CONF_USERNAME: "bad@example.com", CONF_PASSWORD: "wrongpass"}

        mock_client = create_mock_client(auth_error=True)

        with (
            patch("custom_components.thermacell_liv.config_flow.async_get_clientsession"),
            patch("custom_components.thermacell_liv.config_flow.ThermacellClient", return_value=mock_client),
            pytest.raises(InvalidAuth),
        ):
            await validate_input(hass, data)

    @pytest.mark.asyncio
    async def test_validate_input_cannot_connect(self):
        """Test validation when connection test fails."""
        hass = MagicMock()
        data = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        mock_client = create_mock_client(connection_error=True)

        with (
            patch("custom_components.thermacell_liv.config_flow.async_get_clientsession"),
            patch("custom_components.thermacell_liv.config_flow.ThermacellClient", return_value=mock_client),
            pytest.raises(CannotConnect),
        ):
            await validate_input(hass, data)

    @pytest.mark.asyncio
    async def test_validate_input_no_devices(self):
        """Test validation when no devices found."""
        hass = MagicMock()
        data = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        mock_client = create_mock_client(devices=[])  # No devices

        with (
            patch("custom_components.thermacell_liv.config_flow.async_get_clientsession"),
            patch("custom_components.thermacell_liv.config_flow.ThermacellClient", return_value=mock_client),
            pytest.raises(CannotConnect),
        ):
            await validate_input(hass, data)


class TestConfigFlow:
    """Test ConfigFlow class."""

    @pytest.mark.asyncio
    async def test_async_step_user_show_form(self):
        """Test showing the user form."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert "data_schema" in result

    @pytest.mark.asyncio
    async def test_async_step_user_success(self):
        """Test successful user step."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {}

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch(
            "custom_components.thermacell_liv.config_flow.validate_input",
            return_value={"title": "Thermacell LIV (test@example.com)"},
        ):
            # Mock unique_id methods
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == "create_entry"
            assert result["title"] == "Thermacell LIV (test@example.com)"
            assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_async_step_user_invalid_auth(self):
        """Test user step with invalid auth."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {}

        user_input = {CONF_USERNAME: "bad@example.com", CONF_PASSWORD: "wrongpass"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=InvalidAuth):
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == "form"
            assert result["errors"] == {"base": "invalid_auth"}

    @pytest.mark.asyncio
    async def test_async_step_user_cannot_connect(self):
        """Test user step when cannot connect."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {}

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=CannotConnect):
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == "form"
            assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_async_step_user_unknown_error(self):
        """Test user step with unknown error."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {}

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=Exception("Unknown")):
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == "form"
            assert result["errors"] == {"base": "unknown"}

    @pytest.mark.asyncio
    async def test_async_step_reauth(self):
        """Test reauth step returns confirm form."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        result = await flow.async_step_reauth({})

        # Should redirect to reauth_confirm
        assert result["type"] == "form"
        assert result["step_id"] == "reauth_confirm"

    @pytest.mark.asyncio
    async def test_async_step_reauth_confirm_show_form(self):
        """Test reauth confirm shows form."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        result = await flow.async_step_reauth_confirm(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "reauth_confirm"

    @pytest.mark.asyncio
    async def test_async_step_reauth_confirm_success(self):
        """Test successful reauth."""
        hass = MagicMock()
        hass.config_entries.async_get_entry.return_value = MagicMock()
        hass.config_entries.async_update_entry = MagicMock()
        hass.config_entries.async_reload = AsyncMock()

        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        user_input = {CONF_USERNAME: "new@example.com", CONF_PASSWORD: "newpass"}

        with patch(
            "custom_components.thermacell_liv.config_flow.validate_input",
            return_value={"title": "Thermacell LIV (new@example.com)"},
        ):
            result = await flow.async_step_reauth_confirm(user_input=user_input)

            assert result["type"] == "abort"
            assert result["reason"] == "reauth_successful"

    @pytest.mark.asyncio
    async def test_async_step_reauth_confirm_invalid_auth(self):
        """Test reauth with invalid credentials."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry"}

        user_input = {CONF_USERNAME: "bad@example.com", CONF_PASSWORD: "wrongpass"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=InvalidAuth):
            result = await flow.async_step_reauth_confirm(user_input=user_input)

            assert result["type"] == "form"
            assert result["errors"] == {"base": "invalid_auth"}

    def test_async_get_options_flow(self):
        """Test getting options flow."""
        config_entry = MagicMock()
        config_entry.options = {}

        options_flow = ConfigFlow.async_get_options_flow(config_entry)

        assert isinstance(options_flow, ThermacellLivOptionsFlow)


class TestOptionsFlow:
    """Test ThermacellLivOptionsFlow class."""

    @pytest.mark.asyncio
    async def test_async_step_init_show_form(self):
        """Test showing options form."""
        config_entry = MagicMock()
        config_entry.options = {"scan_interval": 60}

        flow = ThermacellLivOptionsFlow(config_entry)

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"
        assert "data_schema" in result

    @pytest.mark.asyncio
    async def test_async_step_init_save_options(self):
        """Test saving options."""
        config_entry = MagicMock()
        config_entry.options = {"scan_interval": 60}

        flow = ThermacellLivOptionsFlow(config_entry)

        user_input = {"scan_interval": 120}

        result = await flow.async_step_init(user_input=user_input)

        assert result["type"] == "create_entry"
        assert result["data"] == {"scan_interval": 120}

    @pytest.mark.asyncio
    async def test_async_step_init_default_values(self):
        """Test default values in options."""
        config_entry = MagicMock()
        config_entry.options = {}  # No existing options

        flow = ThermacellLivOptionsFlow(config_entry)

        result = await flow.async_step_init(user_input=None)

        # Should use default scan_interval of 60
        assert result["type"] == "form"


class TestExceptions:
    """Test exception classes."""

    def test_cannot_connect_exception(self):
        """Test CannotConnect exception."""
        exc = CannotConnect()
        assert isinstance(exc, Exception)

    def test_invalid_auth_exception(self):
        """Test InvalidAuth exception."""
        exc = InvalidAuth()
        assert isinstance(exc, Exception)


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        """Run tests manually."""
        print("🧪 Running Config Flow Tests")
        print("=" * 50)

        # Test validate input
        validate_tests = TestValidateInput()
        try:
            await validate_tests.test_validate_input_success()
            print("✅ Validate input success test passed")
        except Exception as e:
            print(f"❌ Validate input success test failed: {e}")

        try:
            await validate_tests.test_validate_input_invalid_auth()
            print("✅ Validate input invalid auth test passed")
        except Exception as e:
            print(f"❌ Validate input invalid auth test failed: {e}")

        # Test config flow
        flow_tests = TestConfigFlow()
        try:
            await flow_tests.test_async_step_user_show_form()
            print("✅ Show form test passed")
        except Exception as e:
            print(f"❌ Show form test failed: {e}")

        try:
            await flow_tests.test_async_step_user_success()
            print("✅ User step success test passed")
        except Exception as e:
            print(f"❌ User step success test failed: {e}")

        print("\n🎉 Config flow tests completed!")

    asyncio.run(run_tests())
