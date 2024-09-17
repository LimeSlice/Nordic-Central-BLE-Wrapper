#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Device Information service's PnP ID characteristic object
"""

import struct

from dataclasses import dataclass
from enum import IntEnum
from pc_ble_driver_py import ble_driver as NordicDriver

import nordic_central_ble_wrapper as Ble


class PNPVendorIdSource(IntEnum):
    BluetoothSIG = 0x01
    USBImplementorsForum = 0x02


@dataclass
class PNPID:

    vendor_id_source: PNPVendorIdSource | int
    """The Vendor ID Source field designates which organization assigned the value used in the Vendor ID field value"""

    vendor_id: int
    """The Vendor ID field is intended to uniquely identify the vendor of the device. This field is used in conjunction 
  with the Vendor ID Source field. NOTE: The Bluetooth Special Interest Group assigns Device ID Vendor ID, and the USB 
  Implementer's Forum assigns Vendor IDs, either of which can be used for the Vendor ID field value. Device providers 
  should procure the Vendor ID from the USB Implementer's Forum or the Company Identifier from the Bluetooth SIG"""

    product_id: int
    """The Product ID field is intended to distinguish between different products made by the vendor identified with 
  the Vendor ID field."""

    product_version: int
    """The Product Version field is a numeric expression identifying the device release number in Binary-Coded Decimal. 
  This is a vendor-assigned value, which defines the version of the product identified by the Vendor ID and Product ID
  fields. This field is intended to differentiate between version of products with identical Vendor IDs and Product 
  IDs. The value of the field value is 0xJJMN for version JJ.M.N (JJ - major version number, M - minor version number,
  N - sub-minor version number); e.g., version 2.1.3 is represented with value 0x0213 and version 2.0.0 is represented 
  with a value of 0x0200. When upward-compatible changes are made to the device, it is recommended that the minor 
  version number be incremented. If incompatible changes are made to the device, it is recommended that the major 
  version number be incremented. The sub-minor version is incremented for bug-fixes. 

  The vendors themselves manage Product Version field values."""

    @classmethod
    def parse_bytes(cls, payload: bytes):
        c = cls(*struct.unpack("<BHHH", payload))
        if c.vendor_id_source in iter(PNPVendorIdSource):
            c.vendor_id_source = PNPVendorIdSource(c.vendor_id_source)
        return c

    def __str__(self) -> str:
        if isinstance(self.vendor_id_source, PNPVendorIdSource):
            vendor_id_source_str = self.vendor_id_source.name
        else:
            vendor_id_source_str = "Reserved"

        return "\n".join(
            [
                "Vendor ID Source.....{} (0x{:02X})".format(vendor_id_source_str, self.vendor_id_source),
                "Vendor ID............0x{:02X}".format(self.vendor_id),
                "Product ID...........0x{:04X}".format(self.product_id),
                "Product Version......0x{:04X}".format(self.product_version),
            ]
        )


class PNPIDCharacteristic(Ble.Characteristic):
    """PnP ID characteristic handling

    The PnP ID characteristic is a set of values that shall be used to create a device ID
    value that is unique for this device. Included in the characteristic are a Vendor ID source
    field, a Vendor ID field, a Product ID field, and a Product Version field. These values are
    used to identify all devices of a given type/model/version using numbers.
    """

    uuid = NordicDriver.BLEUUID(0x2A50)

    def __init__(self, nrf: Ble.CentralBleDriver, service: Ble.Service):
        """Initialize characteristic object for reading and storing values from the DIS characteristic

        :param nrf: Central BLE Driver object used for BLE READ operations
        :param service: DIS Service object
        """
        super().__init__(nrf=nrf, service=service)
        self.value: PNPID | None = None

    def read(self) -> PNPID | None:
        """Read characteristic value. Stores value in object as well as returns it.

        :return: Characteristic value
        """
        if super().read():
            self.value = PNPID.parse_bytes(self.rx_bytes)
            self.logger.info(str(self.value))
            return self.value

        return None
