#!/usr/bin/evn python3.10
# -*- coding: utf-8

"""
Custom OpCodes service object
"""

from pc_ble_driver_py import ble_driver as NordicDriver

import nordic_central_ble_wrapper as Ble

from services.opcodes import (
    OpCodesTxCharacteristic,
    OpCodesRxCharacteristic,
)
from services import uuids as UUID


class OpCodesService(Ble.Service):
    """Custom OpCodes Service and characteristic handling

    The OpCodes Service utilizing the Nordic UART Service (NUS) to write custom op codes and receive feedback to allow
    a custom interface for a developers custom usage.
    """

    def __init__(self, nrf: Ble.CentralBleDriver):
        """Initialize service object for reading and storing values from the service

        :param nrf: Central BLE Driver object user for BLE WRITE/READ/NTF operations
        """
        super().__init__(nrf=nrf)

        self.uuid = UUID.OPCODES_SUUID

        self.characteristics = {
            OpCodesTxCharacteristic.uuid.value: OpCodesTxCharacteristic(nrf=self.nrf, service=self),
            OpCodesRxCharacteristic.uuid.value: OpCodesRxCharacteristic(nrf=self.nrf, service=self),
        }  # type: dict[NordicDriver.BLEUUID, Ble.Characteristic]
