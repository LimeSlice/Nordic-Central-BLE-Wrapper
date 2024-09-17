#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Device Information service's System ID characteristic object
"""

from pc_ble_driver_py import ble_driver as NordicDriver

import nordic_central_ble_wrapper as Ble

from services import uuids


class SystemIDCharacteristic(Ble.Characteristic):
    """System ID characteristic handling.

    The System ID characteristic value shall represent a structure containing an Organizationally Unique Identifier (OUI)
    followed by a manufacturer-defined identifier and is unique for each individual instance of the product.
    """

    uuid = uuids.DIS_SYSTEM_ID_CUUID

    def __init__(self, nrf: Ble.CentralBleDriver, service: Ble.Service):
        """Initialize characteristic object for reading and storing values from the DIS characteristic

        :param nrf: Central BLE Driver object used for BLE READ operations
        :param service: DIS Service object
        """
        super().__init__(nrf=nrf, service=service)
