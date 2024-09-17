#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
Device Information service object
"""

from pc_ble_driver_py import ble_driver as NordicDriver

import nordic_central_ble_wrapper as Ble

from services.device_information import (
    ManufactureNameCharacteristic,
    ModelNumberCharacteristic,
    SerialNumberCharacteristic,
    FirmwareRevisionCharacteristic,
    HardwareRevisionCharacteristic,
    SoftwareRevisionCharacteristic,
    SystemIDCharacteristic,
    IEEERegulatoryCertificationDataList,
    PNPIDCharacteristic,
)
from services import uuids as UUID


class DeviceInformationService(Ble.Service):
    """Device Information Service and characteristic handling

    The Device Information Service (DIS) exposes manufacturer and/or vendor information about a device. The DIS may expose
    one or more of the characteristics in @ref DeviceInformationService.characteristics.
    """

    def __init__(self, nrf: Ble.CentralBleDriver):
        """Initialize service object for reading and storing values from the DIS

        :param nrf: Central BLE Driver object used for BLE READ operations
        """
        super().__init__(nrf=nrf)

        self.uuid = UUID.DIS_SUUID

        self.characteristics = {
            ManufactureNameCharacteristic.uuid.value: ManufactureNameCharacteristic(nrf=self.nrf, service=self),
            ModelNumberCharacteristic.uuid.value: ModelNumberCharacteristic(nrf=self.nrf, service=self),
            SerialNumberCharacteristic.uuid.value: SerialNumberCharacteristic(nrf=self.nrf, service=self),
            FirmwareRevisionCharacteristic.uuid.value: FirmwareRevisionCharacteristic(nrf=self.nrf, service=self),
            HardwareRevisionCharacteristic.uuid.value: HardwareRevisionCharacteristic(nrf=self.nrf, service=self),
            SoftwareRevisionCharacteristic.uuid.value: SoftwareRevisionCharacteristic(nrf=self.nrf, service=self),
            SystemIDCharacteristic.uuid.value: SystemIDCharacteristic(nrf=self.nrf, service=self),
            IEEERegulatoryCertificationDataList.uuid.value: IEEERegulatoryCertificationDataList(
                nrf=self.nrf, service=self
            ),
            PNPIDCharacteristic.uuid.value: PNPIDCharacteristic(nrf=self.nrf, service=self),
        }  # type: dict[NordicDriver.BLEUUID, Ble.Characteristic]
