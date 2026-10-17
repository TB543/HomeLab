import asyncio
from asyncio import run_coroutine_threadsafe
from sys import argv
from json import load, dump
from RPi.GPIO import setmode, BCM, setup, IN, add_event_detect, BOTH, input
from kasa import Credentials, Discover
from kasa.deviceconfig import DeviceConfig
from kasa.protocols import IotProtocol
from kasa.transports.klaptransport import KlapTransportV2
from kasa.iot import IotPlug


async def create_device(ip, username, password):
    """
    Creates the Kasa device.

    :param ip: The IP address of the device.
    :param username: The username for the Kasa account.
    :param password: The password for the Kasa account.

    :return: The created device object.
    """

    credentials = Credentials(username, password)
    config = DeviceConfig(host=ip, credentials=credentials)
    protocol = IotProtocol(transport=KlapTransportV2(config=config))
    return IotPlug(host=ip, protocol=protocol)


async def set_plugs(state, devices):
    """
    Sets the state of all plugs.

    :param state: The desired state of the plugs (True for on, False for off).
    :param devices: The list of devices to set the state for.
    """

    for device in devices:
        if state:
            await device.turn_on()
        else:
            await device.turn_off()


async def main():
    """
    the main entry point of the program
    """

    # loads saved user settings
    try:
        with open("settings.json", "r") as f:
            settings = load(f)
    except:
        with open("settings.json", "w") as f:
            devices = await Discover.discover()
            dump({"username": argv[1] if len(argv) > 1 else "user@example.com", "password": argv[2] if len(argv) > 2 else "password", "device_ips": list(devices.keys())}, f, indent=4)
            print("config file created, edit before running again")
            exit(0)

    # creates the smart plug devices
    devices = []
    for device in settings["device_ips"]:
        devices.append(await create_device(device, settings["username"], settings["password"]))

    # setup gpio
    setmode(BCM)
    setup(16, IN)
    loop = asyncio.get_event_loop()
    add_event_detect(16, BOTH, lambda e: run_coroutine_threadsafe(set_plugs(input(16), devices), loop))
    run_coroutine_threadsafe(set_plugs(input(16), devices), loop)
    await asyncio.Event().wait()


asyncio.run(main())
