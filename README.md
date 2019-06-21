# HomeAssistant-LeuvenTemplate
Home-Assistant (HA) component to get weather data from weather-stations that use MeteoBridge with the Leuven Template 

## Installation

Find the HA configuration folder, the exact location depends on how you installed homeassistant. If you installed HA under linux as the user homeassistant, this will be in `/home/homeassistant/.homeassistant/` . Under windows by default this is in `%APPDATA%\.homeassistant`.

Copy the folder `custom_components`from this repository and **all** directories and files in there to the HA configuration folder.

The resulting directory structure should be:

```
.homeassistant/
|-- custom_components/
|   |-- leuven_template/
|       |-- __init__.py
|       |-- manifest.json
|       |-- sensor.py
|   |-- other custom components ... (if any were previously installed)
```

## Configuration

You need to find the URL to *yowindowRT.php* for the desired website (you can find the full list [here](https://support.leuven-template.eu/userlist.php?lang=en&users)), in the config below the example is given for 
a weather station located in Herent and in Sluispark Leuven, Belgium. By selecting a unique prefix, multiple sources
can be used. 

Add the code below to *configuration.yaml* in your .homeassistant directory
```yaml
sensor:
  - platform: leuven_template
    url: "https://www.weerstation-herent.be/weather2/yowindowRT.php"
    prefix: "herent"
    
    - platform: leuven_template
    url: "https://weer.sluispark.be/yowindowRT.php"
    prefix: "sluispark"
```


## Links & Further Reading

  * [Home-Assistant](https://www.home-assistant.io/)
  * [Leuven-Template](https://www.wxforum.net/index.php?topic=36504.0)
    * Examples
    * [Weerstation Herent](https://www.weerstation-herent.be/weather2/index.php)
    * [Weer Sluispark](https://weer.sluispark.be/)
    * [Full list](https://support.leuven-template.eu/userlist.php?lang=en&users)
  * [MeteoBridge](https://www.meteobridge.com/wiki/index.php/Home)
