"""Config flow for IEC Power Meter integration."""
import logging

import voluptuous as vol
from voluptuous import Required, All, Length, Range
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries, core, exceptions

from .const import DOMAIN, CONF_TRANSPORT, CONF_HOSTNAME, CONF_PORT, CONF_SOFTPARITY
from .const import CONF_BAUDRATE, CONF_DEVICE, CONF_PARITY, CONF_FLOWCTRL # pylint:disable=unused-import 
from homeassistant.const import (
    CONF_NAME,
)
_LOGGER = logging.getLogger(__name__)

async def validate_net(transport: str, hostname: str, port: int):
    if transport == "TCP":
        return None
    elif transport == "UDP":
        return None
    else:
        raise ValueError

async def validate_serial(transport:str, baudrate:int, parity: str, flow: str):
    return None
   
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IEC Power Meter."""

    VERSION = 1
    # TODO pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL


    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        data_schema  = {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_TRANSPORT): vol.In(["TCP","UDP","Serial"]),
        }
        errors = {}
        if user_input is not None:

            self.data = user_input
            # Return the form of the next step.
            if user_input[CONF_TRANSPORT] in ["TCP","UDP"]:
                return await self.async_step_net_trans()
            elif user_input[CONF_TRANSPORT] == "Serial":
                return await self.async_step_serial_trans() 
            else:
                errors["base"] = "value_error"

        return self.async_show_form(
                step_id="user", data_schema=vol.Schema(data_schema),errors = errors
            )
        
    async def async_step_serial_trans(self, user_input=None):
        data_schema  = {
            vol.Required(CONF_DEVICE, description={"suggested_value": "/dev/ttyUSB0"}): str,
            vol.Required(CONF_BAUDRATE, description={"suggested_value": "/dev/ttyUSB0"}): vol.In([110,300,600,1200,2400,4800,9600,19200,38400,57600,115200,230400,460800,921600]),
            vol.Required(CONF_PARITY, default="7E1"): vol.In(["8N1","7E1"]),
            vol.Required(CONF_FLOWCTRL, default="Off"): vol.In(["Off","RTS","DTR"]),
        }
            
        errors = {}
            
        if user_input is not None:
            try:
                info = await validate_serial(self.data[CONF_TRANSPORT], user_input[CONF_BAUDRATE], user_input[CONF_PARITY], user_input[CONF_FLOWCTRL] )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "value_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
                
            if not errors:
                _LOGGER.info("Serial accepted")
                self.data.update(user_input)
                _LOGGER.info(self.data)
                return self.async_create_entry(title = self.data[CONF_NAME], data=self.data)
        return self.async_show_form(
            step_id="serial_trans", data_schema=vol.Schema(data_schema), errors=errors
        )
        
    async def async_step_net_trans(self, user_input=None):
        data_schema  = {
            vol.Required(CONF_HOSTNAME, description={"suggested_value": "127.0.0.1"}): str,
            vol.Required(CONF_PORT, description={"suggested_value": "12345"}): All(int,Range(min=1)),
            vol.Required(CONF_SOFTPARITY, default = True): cv.boolean,
        }
        
        errors = {}
        if user_input is not None:
            try:
                info = await validate_net(self.data[CONF_TRANSPORT], user_input[CONF_HOSTNAME], user_input[CONF_PORT] )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "Value error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
                
            if not errors:
                _LOGGER.info("Net accepted")
                self.data.update(user_input)
                _LOGGER.info(self.data)
                return self.async_create_entry(title = self.data[CONF_NAME], data=self.data)
                
        return self.async_show_form(
            step_id="net_trans", data_schema=vol.Schema(data_schema), errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
