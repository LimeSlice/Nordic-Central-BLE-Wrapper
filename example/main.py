import argparse
import logging
import sys

from collections import UserDict

import nordic_central_ble_wrapper as Ble  # needs to come before ble_driver import to set the config type
from pc_ble_driver_py import ble_driver as NordicDriver

from services import uuids
from services.device_information import DeviceInformationService
from services.opcodes import (
    OpCodesService,
    OpCodesTxCharacteristic,
    OpCodesRxCharacteristic,
)
from services.opcodes.handlers import *


TARGET_MAC_ADDRESS = "FCAE017C78CE"


def main(args: argparse.Namespace):
    # Setup logging output to stdout
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger().setLevel(logging.INFO)

    # Initialize BLE driver
    nrf = Ble.CentralBleDriver(
        log_severity_level=logging.INFO,
        driver_log_severity_level=logging.INFO,
        rcp_log_severity_level=NordicDriver.RpcLogSeverity.info,
    )
    try:
        nrf.open(com=args.com_port, auto_flash=True)
    except Exception as e:
        print(f"Failed to connect to Nordic device on {args.com}.")
        print("Detectable Nordic devices:")
        print(nrf.enumerate_ports())
        raise e

    if args.mac_address is not None:
        connect(nrf, args.mac_address)
    else:
        nrf.scan()


def connect(nrf: Ble.CentralBleDriver, target_mac_address: str):
    # Add service handlers to BLE driver
    svc_dis = DeviceInformationService(nrf=nrf)
    nrf.add_service_handler(svc_dis)

    svc_opcodes = OpCodesService(nrf=nrf)
    opcode_tx_char = svc_opcodes.characteristics[OpCodesTxCharacteristic.uuid.value]
    opcode_rx_char = svc_opcodes.characteristics[OpCodesRxCharacteristic.uuid.value]
    nrf.add_service_handler(svc_opcodes)

    # Create an OpCode dictionary object for calling opcodes by a string
    opcode_dict = UserDict(
        {
            "ping": PingOpCode(
                opcode_tx_char=opcode_tx_char,
                opcode_rx_char=opcode_rx_char,
                log_severity_level=logging.DEBUG,
            ),
            "counter": CounterOpCode(
                opcode_tx_char=opcode_tx_char,
                opcode_rx_char=opcode_rx_char,
                log_severity_level=logging.DEBUG,
            ),
            "delay": DelayOpCode(
                opcode_tx_char=opcode_tx_char,
                opcode_rx_char=opcode_rx_char,
                log_severity_level=logging.DEBUG,
            ),
        }
    )

    # Connect ot targeted BLE peripheral
    try:
        nrf.connect(target_mac_address=target_mac_address)
        logging.info(nrf.get_discovered_services_string())

        # Read device information characteristics' values
        svc_dis.characteristics[uuids.DIS_MANUFACTURE_NAME_CUUID.value].read()
        svc_dis.characteristics[uuids.DIS_MODEL_NAME_CUUID.value].read()
        svc_dis.characteristics[uuids.DIS_SERIAL_NUMBER_CUUID.value].read()
        svc_dis.characteristics[uuids.DIS_FIRMWARE_REVISION_CUUID.value].read()
        svc_dis.characteristics[uuids.DIS_HARDWARE_REVISION_CUUID.value].read()
        svc_dis.characteristics[uuids.DIS_SOFTWARE_REVISION_CUUID.value].read()
        svc_dis.characteristics[uuids.DIS_PNP_ID_CUUID.value].read()

        # Zephyr doesn't support these characteristics in SDK v0.16.8 (untested)
        # svc_dis.characteristics[uuids.DIS_SYSTEM_ID_CUUID.value].read()
        # svc_dis.characteristics[
        #     uuids.DIS_IEEE_REGULATORY_CERTIFICATION_DATA_LIST_CUUID.value
        # ].read()

        # Execute Custom OpCodes
        opcode_dict["ping"].write()
        opcode_dict["counter"].write()
        opcode_dict["delay"].write()
        opcode_dict["counter"].write()
        opcode_dict["counter"].write()
        opcode_dict["ping"].write()
    except Exception as e:
        raise e

    # Return created objects
    return nrf, svc_dis, svc_opcodes, opcode_dict


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):

        ports = Ble.CentralBleDriver.enumerate_ports()
        if len(ports) == 0:
            sys.stdout.write("No Nordic devices detected.\n\n")
        else:
            sys.stdout.write("Detected Nordic devices:\n\n")
            patt = "{:<15} {:<15}\n"
            sys.stdout.write(patt.format("Port", "Serial Number"))
            for desc in ports:
                sys.stdout.write(patt.format(desc.port, desc.serial_number))
            sys.stdout.write("\n")
        self.print_usage(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="\n\n".join(
            [
                "Connection to NRF52 dev kit central device, connect to a peripheral NRF52 and validate "
                "characteristic read/write functionality.",
                "Provide a mac address to connect to device and validate characteristic functionality. "
                "If no mac address is provided, the Central BLE will scan for available devices.",
            ]
        )
    )
    parser.add_argument(
        "com_port",
        type=str,
        help="Central BLE NRF52 dev kit's COM port (ex. Windows: COMx, Linux: /dev/ttyACMx)",
    )
    parser.add_argument(
        "-m" "--mac-address",
        dest="mac_address",
        type=str,
        help=f"Peripheral BLE mac address to connect to (default: {TARGET_MAC_ADDRESS}",
    )

    main(parser.parse_args())
    sys.exit(0)
