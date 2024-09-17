#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Device Information service's IEEE 11073-20601 Regulatory Certification Data List characteristic object
"""

from pc_ble_driver_py import ble_driver as NordicDriver

import nordic_central_ble_wrapper as Ble

from services import uuids


class IEEERegulatoryCertificationDataList(Ble.Characteristic):
    """IEEE 11073-20601 Regulatory Certification Data List characteristic handling.

    The IEEE 11073-20601 Regulatory Certification Data List characteristic shall represent regulatory and certification
    information for the product in a list defined in IEEE 11073-20601
    """

    uuid = uuids.DIS_IEEE_REGULATORY_CERTIFICATION_DATA_LIST_CUUID

    def __init__(self, nrf: Ble.CentralBleDriver, service: Ble.Service):
        """Initialize characteristic object for reading and storing values from the DIS characteristic

        :param nrf: Central BLE Driver object used for BLE READ operations
        :param service: DIS Service object
        """
        super().__init__(nrf=nrf, service=service)
