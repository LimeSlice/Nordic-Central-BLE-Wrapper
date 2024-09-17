#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Device Information service's Firmware Revision characteristic object
"""

import nordic_central_ble_wrapper as Ble

from services import uuids


class SoftwareRevisionCharacteristic(Ble.Characteristic):
    """Software Revision characteristic handling.

    The Software Revision characteristic string value shall represent the software revision for the software within the
    device.
    """

    uuid = uuids.DIS_SOFTWARE_REVISION_CUUID

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
            self.logger.info(f"Software Revision: {self.value}")
            return self.value

        return None
