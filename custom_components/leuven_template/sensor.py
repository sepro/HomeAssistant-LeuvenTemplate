"""Leuven Template component for Home Assistant"""
import asyncio
import async_timeout
import aiohttp
import logging
from datetime import timedelta

from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'leuven_template'

# Schedule next call after (minutes): Should be 10
SCHEDULE_OK = 1
# When an error occurred, new call after (minutes): Should be 2
SCHEDULE_NOK = 1

CONF_URL = 'https://www.weerstation-herent.be/weather2/yowindowRT.php'


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    _LOGGER.debug("Initializing Leuven Template")
    print("Initializing Leuven Template")
    
    devices = [
        LeuvenTemplateSensor('Humidity', '%', 'mdi:water-percent'),
        LeuvenTemplateSensor('Temperature', TEMP_CELSIUS, 'mdi:thermometer'),
        LeuvenTemplateSensor('Pressure', 'hPa', 'mdi:gauge'),

        LeuvenTemplateSensor('Wind speed', 'kph', 'mdi:weather-windy'),
        LeuvenTemplateSensor('Wind gust', 'kph', 'mdi:weather-windy'),
        LeuvenTemplateSensor('Wind direction', None, 'mdi:compass-outline'),

        LeuvenTemplateSensor('Precipitation rate', 'mm', 'mdi:weather-pouring'),
        LeuvenTemplateSensor('Precipitation total', 'mm', 'mdi:weather-pouring'),

        LeuvenTemplateSensor('UV', None, 'mdi:sunglasses'),
        LeuvenTemplateSensor('Solar radiation', 'W/m2', 'mdi:sunglasses')
    ]

    async_add_entities(devices)

    data = LeuvenTemplateData(hass, devices)
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

    def __init__(self, hass, devices):
        self.hass = hass
        self.devices = devices
        self.data = {}

    async def update_devices(self):
        """Update all devices/sensors."""
        if self.devices:
            tasks = []
            # Update all devices
            for dev in self.devices:
                if dev.load_data(self.data):
                    tasks.append(dev.async_update_ha_state())

            if tasks:
                await asyncio.wait(tasks)

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
        lt_content = await self.get_data(CONF_URL)

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

    def __init__(self, name, unit, icon):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._unit = unit
        self._icon = icon

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'lt ' + self._name

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
