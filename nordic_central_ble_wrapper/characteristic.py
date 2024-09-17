#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
BLE Characteristic object
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging

from pc_ble_driver_py import ble_driver as NordicDriver


if TYPE_CHECKING:
    from central_ble_driver import CentralBleDriver
    from service import Service


class Characteristic:
    """Characteristic interface for handling specific characteristic"""

    uuid = None  # type: (NordicDriver.BLEUUID | None)

    def __init__(self, nrf: CentralBleDriver, service: Service) -> None:
        self.nrf = nrf
        self.service = service
        self.logger = logging.getLogger(self.__class__.__name__)

        self.status = None
        self.tx_bytes = bytes()
        self.rx_bytes = bytes()
        self.data = dict()

    def read(self) -> bool:
        """Perform GATT READ on characteristic and stores the read bytes in characteristic object's rx_bytes variable.

        :return: Boolean indicating if the GATT status was success or not
        """
        # self.nrf.adapter.service_discovery(self.nrf.conn_handle, self.service.uuid)

        # By default, don't use service (mainly for custom services with same Characteristic UUIDs)
        self.status, self.rx_bytes = self.nrf.characteristic_read(characteristic=self.uuid, service=None)

        if self.status is not NordicDriver.BLEGattStatusCode.success:
            self.logger.error(str(self.status))
            return False

        return True

    def write_request(self, *args, **kwargs) -> None:
        """Perform GATT WRITE_REQ on characteristic

        :param args:
        :param kwargs:
        :return: None
        """
        del args  # unused

        # By default, don't use service (mainly for custom services with same Characteristic UUIDs)
        if "payload" in kwargs:
            self.nrf.characteristic_write_request(characteristic=self.uuid, payload=kwargs["payload"], service=None)

    def write_command(self, *args, **kwargs) -> None:
        """Perform GATT WRITE_CMD on characteristic

        :param args:
        :param kwargs:
        :return:
        """
        del args  # unused

        # By default, don't use service (mainly for custom services with same Characteristic UUIDs)
        if "payload" in kwargs:
            self.nrf.characteristic_write_command(characteristic=self.uuid, payload=kwargs["payload"], service=None)

    def enable_notification(self) -> None:
        self.nrf.enable_notification(characteristic=self.uuid)

    def disable_notification(self) -> None:
        self.nrf.disable_notification(characteristic=self.uuid)

    def enable_indication(self) -> None:
        self.nrf.enable_indication(characteristic=self.uuid)

    def disable_indication(self) -> None:
        self.nrf.disable_indication(characteristic=self.uuid)

    def on_notification(self, payload: bytes):
        pass

    def on_indication(self, payload: bytes):
        pass
