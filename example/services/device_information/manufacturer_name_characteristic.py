#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Device Information service's Manufacturer Name characteristic object
"""

from pc_ble_driver_py import ble_driver as NordicDriver

import nordic_central_ble_wrapper as Ble
from services import uuids


class ManufactureNameCharacteristic(Ble.Characteristic):
    """Manufacture Name characteristic handling.

    The Manufacturer Name characteristic string value shall represent the name of the manufacturer of the device.
    """

    uuid = uuids.DIS_MANUFACTURE_NAME_CUUID

    def __init__(self, nrf: Ble.CentralBleDriver, service: Ble.Service):
        """Initialize characteristic object for reading and storing values from the DIS characteristic

        :param nrf: Central BLE Driver object used for BLE READ operations
        :param service: DIS Service object
        """
        super().__init__(nrf=nrf, service=service)

        self.value: str | None = None

    def read(self) -> str | None:
        """Read characteristic value. Stores value in object as well as returns it.

        :return: Characteristic value
        """
        if super().read():
            self.value = self.rx_bytes.decode("utf-8")
            self.logger.info(f"Manufacturer: {self.value}")
            return self.value

        return None
