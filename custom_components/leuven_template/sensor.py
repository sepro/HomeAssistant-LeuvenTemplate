"""Leuven Template component for Home Assistant"""
import asyncio
import async_timeout
import aiohttp
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import TEMP_CELSIUS, DEGREE, PRESSURE_HPA, UV_INDEX, IRRADIATION_WATTS_PER_SQUARE_METER, PERCENTAGE, SPEED_KILOMETERS_PER_HOUR, PRECIPITATION_MILLIMETERS_PER_HOUR, LENGTH_MILLIMETERS
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'leuven_template'

# Schedule next call after (minutes): Should be 10
SCHEDULE_OK = 10
# When an error occurred, new call after (minutes): Should be 2
SCHEDULE_NOK = 2

CONF_URL = 'url'
CONF_PREFIX = 'prefix'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_PREFIX, default='lt_'): cv.string,
    vol.Required(CONF_URL): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    _LOGGER.debug("Initializing Leuven Template")
    print("Initializing Leuven Template")

    url = config.get(CONF_URL)
    prefix = config.get(CONF_PREFIX)

    devices = [
        LeuvenTemplateSensor('Humidity', PERCENTAGE, 'mdi:water-percent', prefix),
        LeuvenTemplateSensor('Temperature', TEMP_CELSIUS, 'mdi:thermometer', prefix),
        LeuvenTemplateSensor('Pressure', PRESSURE_HPA, 'mdi:gauge', prefix),

        LeuvenTemplateSensor('Wind speed', SPEED_KILOMETERS_PER_HOUR, 'mdi:weather-windy', prefix),
        LeuvenTemplateSensor('Wind gust', SPEED_KILOMETERS_PER_HOUR, 'mdi:weather-windy', prefix),
        LeuvenTemplateSensor('Wind direction', DEGREE, 'mdi:compass-outline', prefix),

        LeuvenTemplateSensor('Precipitation rate', PRECIPITATION_MILLIMETERS_PER_HOUR, 'mdi:weather-pouring', prefix),
        LeuvenTemplateSensor('Precipitation total', LENGTH_MILLIMETERS, 'mdi:weather-pouring', prefix),

        LeuvenTemplateSensor('UV', UV_INDEX, 'mdi:sunglasses', prefix),
        LeuvenTemplateSensor('Solar radiation', IRRADIATION_WATTS_PER_SQUARE_METER, 'mdi:sunglasses', prefix)
    ]

    async_add_entities(devices)

    data = LeuvenTemplateData(hass, devices, url)
    await data.schedule_update(1)


def process_xml(xml_data):
    import xmltodict

    output = {}

    parsed_data = xmltodict.parse(xml_data)

    try:
        output['Humidity'] = parsed_data['response']['current_weather']['humidity']['@value']
    except Exception as _:
        pass

    try:
        output['Temperature'] = parsed_data['response']['current_weather']['temperature']['current']['@value']
    except Exception as _:
        pass

    try:
        output['Pressure'] = parsed_data['response']['current_weather']['pressure']['@value']
    except Exception as _:
        pass

    try:
        output['Wind speed'] = parsed_data['response']['current_weather']['wind']['speed']['@value']
    except Exception as _:
        pass

    try:
        output['Wind gust'] = parsed_data['response']['current_weather']['wind']['gusts']['@value']
    except Exception as _:
        pass

    try:
        output['Wind direction'] = parsed_data['response']['current_weather']['wind']['direction']['@value']
    except Exception as _:
        pass

    try:
        output['Precipitation rate'] = parsed_data['response']['current_weather']['sky']['precipitation']['rain']['rate']['@value']
    except Exception as _:
        pass

    try:
        output['Precipitation total'] = parsed_data['response']['current_weather']['sky']['precipitation']['rain']['daily_total']['@value']
    except Exception as _:
        pass

    try:
        output['UV'] = parsed_data['response']['current_weather']['uv']['@value']
    except Exception as _:
        pass

    try:
        output['Solar radiation'] = parsed_data['response']['current_weather']['solar']['@radiation']
    except Exception as _:
        pass

    return output


class LeuvenTemplateData:

    def __init__(self, hass, devices, url):
        self.hass = hass
        self.devices = devices
        self.data = {}
        self.url = url

    async def update_devices(self):
        """Update all devices/sensors."""
        if self.devices:
            tasks = []
            # Update all devices
            for dev in self.devices:
                if dev.load_data(self.data):
                    tasks.append(dev.async_write_ha_state())


            loop = asyncio.get_event_loop()
            task_list = [loop.create_task(task) for task in tasks if task is not None]
            
            if task_list:
                await asyncio.wait(task_list)

    async def schedule_update(self, minute=1):
        """Schedule an update after minute minutes."""
        _LOGGER.debug("Scheduling next update in %s minutes.", minute)
        print("Scheduling next update in %s minutes." % minute)
        nxt = dt_util.utcnow() + timedelta(minutes=minute)
        async_track_point_in_utc_time(self.hass, self.async_update,
                                      nxt)

    async def get_data(self, url):
        """Load data from specified url."""
        _LOGGER.debug("Calling url: %s...", url)
        result = {'SUCCESS': False, 'MESSAGE': None}
        resp = None
        try:
            websession = async_get_clientsession(self.hass)
            with async_timeout.timeout(10):
                resp = await websession.get(url)

                result['STATUS_CODE'] = resp.status
                result['CONTENT'] = await resp.text()
                if resp.status == 200:
                    result['SUCCESS'] = True
                else:
                    result['MESSAGE'] = "Got http statuscode: %d" % (resp.status)

                return result
        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            result['MESSAGE'] = "%s" % err
            return result
        finally:
            if resp is not None:
                await resp.release()

    async def async_update(self, *_):
        """Update the data from a website using the Leuven Template."""
        lt_content = await self.get_data(self.url)

        if lt_content.get('SUCCESS') is not True:
            # unable to get the data
            _LOGGER.warning("Unable to retrieve data from Leuven Template."
                            "(Msg: %s, status: %s,)",
                            lt_content.get('MESSAGE'),
                            lt_content.get('STATUS_CODE'),)
            # schedule new call
            await self.schedule_update(SCHEDULE_NOK)
            return

        self.data = process_xml(lt_content.get('CONTENT'))

        await self.update_devices()
        await self.schedule_update(SCHEDULE_OK)


class LeuvenTemplateSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, name, unit, icon, prefix):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._unit = unit
        self._icon = icon
        self._prefix = prefix

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._prefix + self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    def load_data(self, data):
        if self._name in data:
            self._state = data[self._name]
        else:
            self._state = None

        return True

    @property
    def force_update(self):
        """Return true for continuous sensors, false for discrete sensors."""
        return True
