"""The IEC Power Meter integration."""
import asyncio
import time
import voluptuous as vol

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from IEC61107.IEC61107 import IEC61107, TCP_transport, Serial_transport

from .const import DOMAIN, CONF_TRANSPORT, CONF_HOSTNAME, CONF_PORT, CONF_SOFTPARITY
from .const import CONF_BAUDRATE, CONF_DEVICE, CONF_PARITY, CONF_FLOWCTRL # pylint:disable=unused-import 
from .const import DOMAIN

from homeassistant.const import (
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
)

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
    myhub.setup()
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

        self.generic_params = {}
        self.named_params = {}

        self.has_wid = False
        self.has_noid = False

        self._name = config[CONF_NAME]
        self._transport_name = config[CONF_TRANSPORT]
        self.poll_perod = 30.0
        
        self.last_readout = False

        try:
            if(config[CONF_TRANSPORT] == "Serial"):
                self._serialdev = config[CONF_DEVICE]
                self._baudrate = config[CONF_BAUDRATE]
                self._parity   = config[CONF_PARITY]
                self._flowctrl = config[CONF_FLOWCTRL]
            else:
                self._hostname = config[CONF_HOSTNAME]
                self._softparity = config[CONF_SOFTPARITY]
                self._port = config[CONF_PORT]
        except KeyError:
            _LOGGER.error("HUB config error")
        
            
    @property
    def name(self):
        """Return the name of this hub."""
        return self._name  

    def setup(self):
        if(self._transport_name == "TCP"):
            self.transport = TCP_transport(self._hostname, int(self._port), emulateparity = bool(self._softparity))
        elif(self._transport_name == "UDP"):
            self.transport = None
        elif(self._transport_name == "Serial"):
            self.transport = Serial_transport(self._serialdev,self.baudrate,self._parity)
        else:
            assert false
        self.IEC_device = IEC61107(self.transport)

    def close(self):
        """Disconnect client."""
        with self._lock:
            #self._client.close()
            _LOGGER.warning("IEC close")

    def connect(self):
        """Connect client."""
        with self._lock:
            self.IEC_device = IEC61107(self.transport)
            _LOGGER.warning("IEC connect")

    def update_needed(self):
        
        if self.last_readout is None:
            return True

        curtime = time.time()
        if (curtime - self.last_readout) > self.poll_perod:
            return True
        return False

    def perform_readout(self):

        _LOGGER.warning("IEC perform readout")
        #update named parameters
        for meter in self.named_params:
            if meter == 0: #use broadcast address (only one device on a bus)
                self.IEC_device.init_session()
            else: #address meter by its ID
                self.IEC_device.init_session(meter)

            for param in self.named_params[meter]: #go through all requested parameter names
                values = self.IEC_device.read_param(param)
                    
                for idx, value in enumerate(values): #save requested values
                    if self.named_params[meter][param].get(idx):
                        self.named_params[meter][param][idx] = value

            self.IEC_device.end_session()

        #update generic read
        for meter in self.generic_params:
            if meter == 0: #use broadcast address (only one device on a bus)
                self.IEC_device.init_session()
            else: #address meter by its ID
                self.IEC_device.init_session(meter)
            
            generic_data = self.IEC_device.general_read()

            for idx, value in enumerate(generic_data):
                if self.generic_params[meter].get(idx):
                    self.generic_params[meter][idx] = value

            self.IEC_device.end_session()

        self.last_readout = time.time()

        return

    def read_named(self,id, name, index):
        _LOGGER.info("Param "+ name + str(index))

        if self.update_needed():
            self.perform_readout()

        return self.named_params[id][name][index]
        

    def read_generic(self,id,index):
        _LOGGER.info("Generic " + str(index))
        if self.update_needed():
            self.perform_readout()
        return self.generic_params[id][index]

    def add_named(self,id,name,index):
        if id:
            if self.has_noid:
                _LOGGER.error("Can not mix parameters with ID and ones with no ID")
                return False
        else:
            id = 0
            if self.has_wid:
                _LOGGER.error("Can not mix parameters with ID and ones with no ID")
                return False

        if self.named_params.get(id) is None:
            self.named_params[id] = {}

        if self.named_params[id].get(name) is None:
            self.named_params[id][name] = {}

        self.named_params[id][name][index] = None

        return True
    
    def add_generic(self,id,index):
        if id:
            if self.has_noid:
                _LOGGER.error("Can not mix parameters with ID and ones with no ID")
                return False
        else:
            if self.has_wid:
                _LOGGER.error("Can not mix parameters with ID and ones with no ID")
                return False
        if self.named_params.get(id) is None:
            self.named_params[id] = []

        self.generic_params[id][index] = None
        return True
           

