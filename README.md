# Slimmelezer+ to DSMR Reader

This tool enables the transfor of smart meter data from [Marcel Zuidwijk](https://github.com/zuidwijk)'s [Slimmelezer+](https://www.zuidwijk.com/product/slimmelezer-plus/) running ESPHome to [DSMR Reader](https://github.com/dsmrreader/dsmr-reader).

The tool subscribes to the meter values using the same API that Home Assistant uses ([ESPHome Native API](https://esphome.io/components/api.html)) and subsequently posts the results to the DSMR Reader API. It can be used concurrently with Home Assistant.

Alternatively, you could install [esp-link firmware](https://www.zuidwijk.com/using-esp-link/) instead of ESPHome, allowing DSMR Reader to retrieve the raw data over a network stocket.

## Disclaimer

This tool was made for my personal use and is by no means complete. I'm using it with the Fluvius DSMR5 meter in Belgium (without gas meter for now). Feel free to use and modify as needed.

## Configuration

- API endpoints are set in the included config file. Rename example **config.example.yml** to **config.yml**.
- To enable the API go to "DSMR-reader API" in the DSMR Configuration, check "Enable DSMR-reader API" and copy the auth key into `config.yml`.
- By default, the Slimmemeter+ ESPHome Native API listens on port 6053, and no password is set.
- Disable the built-in datalogger of DSMR Reader. With the docker installation from [xirixiz](https://github.com/xirixiz/dsmr-reader-docker), this can be done  by adding the environment variable `DSMRREADER_OPERATION_MODE=api_server` in the `docker-compose.yml` file.
