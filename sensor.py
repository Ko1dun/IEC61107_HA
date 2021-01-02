"""Platform for sensor integration."""
import logging
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity
import re
from typing import Any, Callable, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_PARAMETERS, 
    CONF_HUB, DOMAIN, 
    CONF_PARAM, 
    CONF_INDEX,
    CONF_ID,
)
    

from homeassistant.const import (
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
)

from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PARAMETERS): [
            {
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_HUB): cv.string,
                vol.Optional(CONF_ID): cv.string,
                vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
                vol.Optional(CONF_PARAM): cv.string,
                vol.Optional(CONF_INDEX,default=0): cv.positive_int,
            }
        ]
    }
)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.warning("IEC sensor setup")
    _LOGGER.warning(config)
    
    sensors = []

    for parameter in config[CONF_PARAMETERS]:
        hub_name = parameter[CONF_HUB]
        try:
            hub = hass.data[DOMAIN][hub_name]
        except KeyError:
            _LOGGER.error("Hub " + hub_name + " not found")
            continue
        
        _LOGGER.warning("param")
        _LOGGER.warning(parameter)
        _LOGGER.warning(hub.name)


        #add parameter to hub request list
        added = hub.add_named(id = parameter.get(CONF_ID),
                        name = parameter.get(CONF_PARAM),
                        index= parameter[CONF_INDEX])

        if added :
            #create sensor
            sensor = IEC_sensor(
                name = parameter[CONF_NAME],
                unit_of_measurement = parameter.get(CONF_UNIT_OF_MEASUREMENT),
                hub = hub,
                id = parameter.get(CONF_ID),
                param= parameter.get(CONF_PARAM),
                index= parameter[CONF_INDEX]
                )
            sensors.append(sensor)        

    if not sensors:
        return False
    async_add_entities(sensors)

# def setup_platform(hass, config, add_entities, discovery_info=None):
#     """Set up the Modbus sensors."""
#     sensors = []
#     _LOGGER.info("IEC sensor setup")
#     _LOGGER.info(config)
#     add_entities([ExampleSensor()])


class IEC_sensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, unit_of_measurement, hub,id, param,index):
        """Initialize the sensor."""
        self._state = None
        self._hub = hub
        self._id = id
        self._name = name
        self._param = param
        self._index = index
        self._unit = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    def update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._param is not None:
            value = self._hub.read_named(self._id, self._param,self._index)
        else:
            value = self._hub.read_generic(self._id, self._index)
        self._state = value