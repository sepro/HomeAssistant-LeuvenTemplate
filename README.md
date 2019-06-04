# HomeAssistant-LeuvenTemplate
Home-Assistant component to get weather data from weather-stations that use meteobridge with the Leuven Template 

## Installation

## Configuration

You need to find the URL to *yowindowRT.php* for the desired website, in the config below the example is given for 
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
  * [MeteoBridge](https://www.meteobridge.com/wiki/index.php/Home)