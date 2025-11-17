#!/usr/bin/env python3
"""Unit tests for config_flow module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.thermacell_liv.config_flow import (
    CannotConnect,
    ConfigFlow,
    InvalidAuth,
    ThermacellLivOptionsFlow,
    validate_input,
)
from custom_components.thermacell_liv.const import CONF_PASSWORD, CONF_USERNAME, DOMAIN


class TestValidateInput:
    """Test validate_input function."""

    @pytest.mark.asyncio
    async def test_validate_input_success(self):
        """Test successful validation."""
        hass = MagicMock()
        data = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch("custom_components.thermacell_liv.config_flow.ThermacellLivAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.authenticate.return_value = True
            mock_api.test_connection.return_value = True
            mock_api_class.return_value = mock_api

            result = await validate_input(hass, data)

            assert result == {"title": "Thermacell LIV"}
            mock_api.authenticate.assert_called_once()
            mock_api.test_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_input_invalid_auth(self):
        """Test validation with invalid credentials."""
        hass = MagicMock()
        data = {CONF_USERNAME: "bad@example.com", CONF_PASSWORD: "wrongpass"}

        with patch("custom_components.thermacell_liv.config_flow.ThermacellLivAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.authenticate.return_value = False
            mock_api_class.return_value = mock_api

            with pytest.raises(InvalidAuth):
                await validate_input(hass, data)

    @pytest.mark.asyncio
    async def test_validate_input_cannot_connect(self):
        """Test validation when connection test fails."""
        hass = MagicMock()
        data = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch("custom_components.thermacell_liv.config_flow.ThermacellLivAPI") as mock_api_class:
            mock_api = AsyncMock()
            mock_api.authenticate.return_value = True
            mock_api.test_connection.return_value = False
            mock_api_class.return_value = mock_api

            with pytest.raises(CannotConnect):
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

        with patch("custom_components.thermacell_liv.config_flow.validate_input", return_value={"title": "Thermacell LIV"}):
            # Mock unique_id methods
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()
            flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

            result = await flow.async_step_user(user_input=user_input)

            assert result["type"] == "create_entry"
            flow.async_create_entry.assert_called_once_with(title="Thermacell LIV", data=user_input)

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
            flow.async_show_form = MagicMock(return_value={"type": "form"})

            await flow.async_step_user(user_input=user_input)

            flow.async_show_form.assert_called_once()
            call_args = flow.async_show_form.call_args
            assert call_args[1]["errors"]["base"] == "invalid_auth"

    @pytest.mark.asyncio
    async def test_async_step_user_cannot_connect(self):
        """Test user step with connection error."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {}

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=CannotConnect):
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()
            flow.async_show_form = MagicMock(return_value={"type": "form"})

            await flow.async_step_user(user_input=user_input)

            flow.async_show_form.assert_called_once()
            call_args = flow.async_show_form.call_args
            assert call_args[1]["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_async_step_user_unknown_error(self):
        """Test user step with unexpected error."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {}

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "password123"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=Exception("Unexpected error")):
            flow.async_set_unique_id = AsyncMock(return_value=None)
            flow._abort_if_unique_id_configured = MagicMock()
            flow.async_show_form = MagicMock(return_value={"type": "form"})

            await flow.async_step_user(user_input=user_input)

            flow.async_show_form.assert_called_once()
            call_args = flow.async_show_form.call_args
            assert call_args[1]["errors"]["base"] == "unknown"

    @pytest.mark.asyncio
    async def test_async_step_reauth(self):
        """Test reauth step redirects to reauth_confirm."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.async_step_reauth_confirm = AsyncMock(return_value={"type": "form"})

        await flow.async_step_reauth({})

        flow.async_step_reauth_confirm.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_step_reauth_confirm_show_form(self):
        """Test showing reauth confirm form."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry_id", "unique_id": "test@example.com"}

        result = await flow.async_step_reauth_confirm(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "reauth_confirm"

    @pytest.mark.asyncio
    async def test_async_step_reauth_confirm_success(self):
        """Test successful reauthentication."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry_id"}

        # Mock existing entry
        existing_entry = MagicMock()
        existing_entry.entry_id = "test_entry_id"
        hass.config_entries.async_get_entry.return_value = existing_entry
        hass.config_entries.async_update_entry = MagicMock()
        hass.config_entries.async_reload = AsyncMock()

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "newpassword"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", return_value={"title": "Thermacell LIV"}):
            flow.async_abort = MagicMock(return_value={"type": "abort"})

            result = await flow.async_step_reauth_confirm(user_input=user_input)

            assert result["type"] == "abort"
            hass.config_entries.async_update_entry.assert_called_once()
            hass.config_entries.async_reload.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_step_reauth_confirm_invalid_auth(self):
        """Test reauth with invalid credentials."""
        hass = MagicMock()
        flow = ConfigFlow()
        flow.hass = hass
        flow.context = {"entry_id": "test_entry_id"}

        existing_entry = MagicMock()
        hass.config_entries.async_get_entry.return_value = existing_entry

        user_input = {CONF_USERNAME: "test@example.com", CONF_PASSWORD: "wrongpass"}

        with patch("custom_components.thermacell_liv.config_flow.validate_input", side_effect=InvalidAuth):
            flow.async_show_form = MagicMock(return_value={"type": "form"})

            await flow.async_step_reauth_confirm(user_input=user_input)

            flow.async_show_form.assert_called_once()
            call_args = flow.async_show_form.call_args
            assert call_args[1]["errors"]["base"] == "invalid_auth"

    def test_async_get_options_flow(self):
        """Test getting options flow."""
        config_entry = MagicMock()
        options_flow = ConfigFlow.async_get_options_flow(config_entry)

        assert isinstance(options_flow, ThermacellLivOptionsFlow)
        assert options_flow.config_entry is config_entry


class TestOptionsFlow:
    """Test ThermacellLivOptionsFlow class."""

    @pytest.mark.asyncio
    async def test_async_step_init_show_form(self):
        """Test showing options form."""
        config_entry = MagicMock()
        config_entry.options.get.return_value = 60

        flow = ThermacellLivOptionsFlow(config_entry)

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "init"

    @pytest.mark.asyncio
    async def test_async_step_init_save_options(self):
        """Test saving options."""
        config_entry = MagicMock()
        config_entry.options.get.return_value = 60

        flow = ThermacellLivOptionsFlow(config_entry)
        user_input = {"scan_interval": 90}

        result = await flow.async_step_init(user_input=user_input)

        assert result["type"] == "create_entry"
        assert result["data"] == user_input

    @pytest.mark.asyncio
    async def test_async_step_init_default_values(self):
        """Test default option values."""
        config_entry = MagicMock()
        config_entry.options.get.side_effect = lambda key, default: default

        flow = ThermacellLivOptionsFlow(config_entry)

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == "form"
        # Default scan_interval should be 60
        config_entry.options.get.assert_called_with("scan_interval", 60)


class TestExceptions:
    """Test custom exception classes."""

    def test_cannot_connect_exception(self):
        """Test CannotConnect exception."""
        exc = CannotConnect("Test error")
        assert isinstance(exc, Exception)

    def test_invalid_auth_exception(self):
        """Test InvalidAuth exception."""
        exc = InvalidAuth("Test error")
        assert isinstance(exc, Exception)


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import asyncio

    test_validate = TestValidateInput()
    test_config = TestConfigFlow()
    test_options = TestOptionsFlow()
    test_exceptions = TestExceptions()

    print("🧪 Running Config Flow Tests")
    print("=" * 50)

    async def run_async_tests():
        """Run all async tests."""
        # Validate input tests
        try:
            await test_validate.test_validate_input_success()
            print("✅ Validate input success test passed")
        except Exception as e:
            print(f"❌ Validate input success test failed: {e}")

        try:
            await test_validate.test_validate_input_invalid_auth()
            print("✅ Validate input invalid auth test passed")
        except Exception as e:
            print(f"❌ Validate input invalid auth test failed: {e}")

        try:
            await test_validate.test_validate_input_cannot_connect()
            print("✅ Validate input cannot connect test passed")
        except Exception as e:
            print(f"❌ Validate input cannot connect test failed: {e}")

        # Config flow tests
        try:
            await test_config.test_async_step_user_show_form()
            print("✅ Config flow show form test passed")
        except Exception as e:
            print(f"❌ Config flow show form test failed: {e}")

        try:
            await test_config.test_async_step_user_success()
            print("✅ Config flow user success test passed")
        except Exception as e:
            print(f"❌ Config flow user success test failed: {e}")

        # Options flow tests
        try:
            await test_options.test_async_step_init_show_form()
            print("✅ Options flow show form test passed")
        except Exception as e:
            print(f"❌ Options flow show form test failed: {e}")

    asyncio.run(run_async_tests())

    # Exception tests
    try:
        test_exceptions.test_cannot_connect_exception()
        print("✅ CannotConnect exception test passed")
    except Exception as e:
        print(f"❌ CannotConnect exception test failed: {e}")

    try:
        test_exceptions.test_invalid_auth_exception()
        print("✅ InvalidAuth exception test passed")
    except Exception as e:
        print(f"❌ InvalidAuth exception test failed: {e}")

    print("\n🎉 Config flow tests completed!")
