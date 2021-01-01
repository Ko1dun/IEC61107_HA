"""The IEC Power Meter integration."""
import asyncio

import voluptuous as vol

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_TRANSPORT, CONF_HOSTNAME, CONF_PORT, CONF_SOFTPARITY
from .const import CONF_BAUDRATE, CONF_DEVICE, CONF_PARITY, CONF_FLOWCTRL # pylint:disable=unused-import 
from .const import DOMAIN, CONF_NAME

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the IEC Power Meter component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up IEC Power Meter from a config entry."""
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)

    _LOGGER.warning("Setup main IEC_METER")
    _LOGGER.warning(hass_data)
    myhub = IEC_hub(hass_data)
    hass.data[DOMAIN][entry.title] = myhub
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class IEC_hub:

    

    def __init__(self, config):
        self.transport = None
        self.IEC_device = None

        self._name = config[CONF_NAME]
        self._transport_name = config[CONF_TRANSPORT]
        

        try:
            if(config[CONF_TRANSPORT] == "Serial"):
                self._serialdev = config[CONF_DEVICE]
                self._baudrate = config[CONF_BAUDRATE]
                self._parity   = config[CONF_PARITY]
                self._flowctrl = config[CONF_FLOWCTRL]
            else:
                self._hostname = config[CONF_HOSTNAME]
                self._softparity = config[CONF_SOFTPARITY]
        except KeyError:
            _LOGGER.error("HUB config error")
        
            
    @property
    def name(self):
        """Return the name of this hub."""
        return self._name  

    def setup(self):
        if(self._transport_name == "TCP"):
            self.transport = 1
        elif(self._transport_name == "UDP"):
            self.transport = 2
        elif(self._transport_name == "Serial"):
            self.transport = 3
        else:
            assert false

    def close(self):
        """Disconnect client."""
        with self._lock:
            #self._client.close()
            _LOGGER.warning("IEC close")

    def connect(self):
        """Connect client."""
        with self._lock:
            #self._client.connect()
            _LOGGER.warning("IEC connect")

    def read_named(self,name, index):
        return "Param "+ name + str(index)

    def read_generic(self,index):
        return "Generic " + str(index)
           

