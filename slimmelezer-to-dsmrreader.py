#!/usr/bin/env python3
from datetime import datetime, timezone
import math
import aioesphomeapi
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import asyncio
import config

# Ignore warnings when using self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Translates the Entity names in the ESPHome API to the DSMR Reader fields
entities_dsmr = {
    'Energy Consumed Luxembourg': None,
    'Energy Consumed Tariff 1': 'electricity_delivered_1',
    'Energy Consumed Tariff 2': 'electricity_delivered_2',
    'Energy Produced Luxembourg': None,
    'Energy Produced Tariff 1': 'electricity_returned_1',
    'Energy Produced Tariff 2': 'electricity_returned_2',
    'Power Consumed': 'electricity_currently_delivered',
    'Power Produced': 'electricity_currently_returned',
    'Electricity Failures': None,
    'Long Electricity Failures': None,
    'Voltage Phase 1': 'phase_voltage_l1',
    'Voltage Phase 2': 'phase_voltage_l2',
    'Voltage Phase 3': 'phase_voltage_l3',
    'Current Phase 1': 'phase_power_current_l1',
    'Current Phase 2': 'phase_power_current_l2',
    'Current Phase 3': 'phase_power_current_l3',
    'Power Consumed Phase 1': 'phase_currently_delivered_l1',
    'Power Consumed Phase 2': 'phase_currently_delivered_l2',
    'Power Consumed Phase 3': 'phase_currently_delivered_l3',
    'Power Produced Phase 1': 'phase_currently_returned_l1',
    'Power Produced Phase 2': 'phase_currently_returned_l2',
    'Power Produced Phase 3': 'phase_currently_returned_l3',
    'Gas Consumed': None,
    'Gas Consumed Belgium': 'extra_device_delivered',
    'SlimmeLezer Uptime': None,
    'SlimmeLezer Wi-Fi Signal': None,
    'DSMR Identification': None,
    'DSMR Version': None,
    'DSMR Version Belgium': None,
    'SlimmeLezer IP Address': None,
    'SlimmeLezer Wi-Fi SSID': None,
    'SlimmeLezer Wi-Fi BSSID': None,
    'ESPHome Version': None
}


class DSMR_reading:

    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.electricity_delivered_1 = None
        self.electricity_returned_1 = None
        self.electricity_delivered_2 = None
        self.electricity_returned_2 = None
        self.electricity_currently_delivered = None
        self.electricity_currently_returned = None
        self.phase_currently_delivered_l1 = None
        self.phase_currently_delivered_l2 = None
        self.phase_currently_delivered_l3 = None
        self.extra_device_timestamp = None
        self.extra_device_delivered = None
        self.phase_currently_returned_l1 = None
        self.phase_currently_returned_l2 = None
        self.phase_currently_returned_l3 = None
        self.phase_voltage_l1 = None
        self.phase_voltage_l2 = None
        self.phase_voltage_l3 = None
        self.phase_power_current_l1 = None
        self.phase_power_current_l2 = None
        self.phase_power_current_l3 = None

    def __str__(self):
        attrs = vars(self)
        return '\n'.join("%s: %s" % item for item in attrs.items())

    def jsonreading(self):
        # Only return json if all mandatory fields are present
        if (self.timestamp is not None
                and self.electricity_delivered_1 is not None
                and self.electricity_returned_1 is not None
                and self.electricity_delivered_2 is not None
                and self.electricity_returned_2 is not None
                and self.electricity_currently_delivered is not None
                and self.electricity_currently_returned is not None):
            # Remove None
            out = {key: value for key, value in vars(self).items() if value is not None}
            # Format according to API specs
            for v in ['electricity_delivered_1', 'electricity_returned_1',
                      'electricity_delivered_2', 'electricity_returned_2',
                      'electricity_currently_delivered', 'electricity_currently_returned', 'exta_device_delivered',
                      'phase_currently_delivered_l1', 'phase_currently_delivered_l2', 'phase_currently_delivered_l3',
                      'phase_currently_returned_l1', 'phase_currently_returned_l2', 'phase_returned_delivered_l3']:
                if v in out:
                    out[v] = str(round(out[v], 3))

            for v in ['phase_voltage_l1', 'phase_voltage_l2', 'phase_voltage_l3']:
                if v in out:
                    out[v] = str(round(out[v], 1))

            for v in ['phase_power_current_l1', 'phase_power_current_l2', 'pphase_power_current_l3']:
                if v in out:
                    out[v] = int(round(out[v], 0))

            return out
        else:
            return False


def create_dsmr_reading(reading):
    # Maybe switch to aiohttp in the future, but simple requests seems to work fine for now
    headers = {'X-AUTHKEY': f'{config.API_KEY}',
               'Content-type': 'application/json'}
    try:
        response = requests.post(config.API_URL, json=reading, headers=headers, verify=False, timeout=10)
        return response
    except Exception as e:
        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(f"{ts} Error writing to DSMR: {e}")
        return None


async def main():
    attempt = 0
    attempt_timeout = config.ATTEMPT_TIMEOUT
    max_attempts = config.MAX_ATTEMPTS

    while attempt < max_attempts:
        try:
            cli = aioesphomeapi.APIClient(config.ESPHOME_HOST, config.ESPHOME_PORT, config.ESPHOME_PASSWORD)
            await asyncio.wait_for(cli.connect(login=True), timeout=attempt_timeout)
            sensors, services = await cli.list_entities_services()
            sensor_by_keys = dict((sensor.key, sensor.name) for sensor in sensors)

            def cb(state):
                global r
                if isinstance(state, aioesphomeapi.SensorState):
                    entity = sensor_by_keys[state.key]
                    dsmr_ent = entities_dsmr[entity]
                    if dsmr_ent is not None:
                        ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                        if r.timestamp != ts:
                            # Write previous reading to DSMR-reader
                            j = r.jsonreading()
                            if j is not None:
                                result = str(create_dsmr_reading(j))
                                print(f"{r.timestamp} Success! {result}")

                            # Start new reading
                            r = DSMR_reading(ts)
                        if not math.isnan(state.state):
                            setattr(r, entities_dsmr[sensor_by_keys[state.key]], state.state)

            await asyncio.wait_for(cli.subscribe_states(cb), timeout=60)
            return

        except asyncio.TimeoutError as e:
            ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f"{ts} Connection problem: {e}, retrying... (attempt {attempt + 1} of {max_attempts})")
            attempt += 1
        except Exception as e:
            ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f"{ts} Unknown error: {e}")
            break

    print(f"Maximum number of attempts {max_attempts} reached. Ending program.")

r = DSMR_reading(None)
loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(main())
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.close()
