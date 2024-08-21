#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

"""
NRF52 central BLE driver wrapper
"""

from __future__ import annotations

import logging
import time

from enum import IntEnum
from queue import Queue, Empty
from typing import Literal, Any

# noinspection PyGlobalUndefined
from pc_ble_driver_py import config

config.__conn_ic_id__ = 'NRF52'
nrf_sd_ble_api_ver = config.sd_api_ver_get()

# noinspection PyUnresolvedReferences
from pc_ble_driver_py import (ble_driver as NordicDriver,
                              ble_adapter as NordicAdapter)

from service import Service


class ConnectionStatus(IntEnum):
  NoConnection = 0
  Scanning = 1
  Connecting = 2
  Connected = 3


class CentralBleDriver(NordicAdapter.BLEDriverObserver,
                       NordicAdapter.BLEAdapterObserver):
  """Generic Serial BLE object for Bluetooth communication.
  """

  TScanDataDict = dict[str, dict[(NordicDriver.BLEAdvData.Types | Literal['rssi', 'name']), Any]]
  TServicesDict = dict[NordicDriver.BLEUUID, Service]

  def __init__(self, log_severity_level: int = logging.DEBUG,
               driver_log_severity_level: int = logging.DEBUG,
               rcp_log_severity_level: NordicDriver.RpcLogSeverity = NordicDriver.RpcLogSeverity.info):
    """Initialize Tool object

    :param log_severity_level:
    :param driver_log_severity_level:
    :param rcp_log_severity_level:
    """
    super().__init__()

    self.logger = logging.getLogger(self.__class__.__name__)
    self.logger.setLevel(level=log_severity_level)

    self.adapter = None

    self.target_addr = None
    self.conn_handle = None
    self.bd_address = None

    self.driver_log_level = driver_log_severity_level
    self.rcp_log_level = rcp_log_severity_level

    self.scan_parameters = NordicDriver.BLEDriver.scan_params_setup()
    self.connection_parameters = NordicDriver.BLEDriver.conn_params_setup()

    self.connection_status = ConnectionStatus.NoConnection

    self.scan_data = dict()   # type: CentralBleDriver.TScanDataDict
    self.services = dict()    # type: CentralBleDriver.TServicesDict

    self.passkey_q = Queue()

    self.conn_q = Queue()

    self.actual_att_mtu = None
    self.actual_conn_params = None

  @staticmethod
  def enumerate_ports():
    return NordicDriver.BLEDriver.enum_serial_ports()

  def open(self, com: str,
           baud_rate: int = 1000000,
           auto_flash: bool = False,
           retransmission_interval: int = 300,
           response_timeout: int = 1500) -> None:
    """Open a connection with the nRF52 device

    :param com:                     COM port to open
    :param baud_rate:               baud rate to communicate through port with
    :param auto_flash:              automatically flash the device with hex firmware
    :param retransmission_interval:
    :param response_timeout:
    """
    self.logger.info(f'Opening nRF52 on {com}')

    ble_driver = NordicDriver.BLEDriver(
      serial_port=com,
      baud_rate=baud_rate,
      auto_flash=auto_flash,
      retransmission_interval=retransmission_interval,
      response_timeout=response_timeout,
      log_severity_level=self.rcp_log_level.name
    )
    self.adapter = NordicAdapter.BLEAdapter(ble_driver=ble_driver)

    logging.getLogger('pc_ble_driver_py.ble_adapter').setLevel(self.driver_log_level)
    logging.getLogger('pc_ble_driver_py.ble_driver').setLevel(self.driver_log_level)
    logging.getLogger('pc_ble_driver_py.observers').setLevel(self.driver_log_level)

    self.adapter.observer_register(self)
    self.adapter.driver.observer_register(self)
    self.adapter.default_mtu = 256

    try:
      self.adapter.driver.open()

      gatt_cfg = NordicDriver.BLEConfigConnGatt(self.adapter.default_mtu)
      gatt_cfg.tag = 1
      self.adapter.driver.ble_cfg_set(NordicDriver.BLEConfig.conn_gatt, gatt_cfg)
      self.adapter.driver.ble_enable()

    except NordicAdapter.NordicSemiException:
      self.logger.error('Error opening BLE driver! Restart dev board, check COM port, and rerun.')
      self.adapter = None
      # raise e

  def close(self) -> None:
    """Close connection with nRF52 device
    """
    self.logger.info('closing...')

    try:
      self.adapter.disconnect(self.conn_handle)
    except:
      pass
    finally:
      self.adapter.close()
      self.adapter = None
      self.connection_status = ConnectionStatus.NoConnection

  def add_service_handler(self, service_handler: Service):
    self.services[service_handler.uuid] = service_handler

  def scan(self, scan_params: NordicDriver.BLEGapScanParams = None):
    """
    :param scan_params:
    """
    self.logger.info('scanning...')
    self.scan_data = dict()

    if scan_params is not None:
      self.scan_parameters = scan_params

    if self.connection_status == ConnectionStatus.NoConnection:
      self.connection_status = ConnectionStatus.Scanning
      try:
        self.adapter.driver.ble_gap_scan_start(scan_params=self.scan_parameters)
      except:
        pass

    time.sleep(self.scan_parameters.timeout_s)

    if self.connection_status == ConnectionStatus.Scanning:
      try:
        self.adapter.driver.ble_gap_scan_stop()
      except:
        pass
      self.connection_status = ConnectionStatus.NoConnection
      self.get_scan_data()

  def get_scan_data(self) -> CentralBleDriver.TScanDataDict:
    """Retrieve dictionary of scan data
    """
    ret = dict()
    scan_data = self.scan_data.copy()

    for addr, data in scan_data.items():
      if NordicDriver.BLEAdvData.Types.complete_local_name in data:
        name = ''.join(chr(e) for e in data[NordicDriver.BLEAdvData.Types.complete_local_name])
      elif NordicDriver.BLEAdvData.Types.short_local_name in data:
        name = ''.join(chr(e) for e in data[NordicDriver.BLEAdvData.Types.short_local_name])
      else:
        name = 'N/A'

      self.logger.debug(f'Address: 0x{addr}, Device Name: {name} {", ".join([f"{repr(key)}: {val}" for key, val in data.items()])}')

      data['name'] = name
      ret[addr] = data

    return ret

  def connect(self, target_mac_address: str,
              connection_parameters: NordicDriver.BLEGapConnParams = None,
              scan_parameters: NordicDriver.BLEGapScanParams = None,
              uuid_base: NordicDriver.BLEUUIDBase = None,
              exchange_att_mcu_upon_connect: bool = True,
              discover_services_upon_connect: bool = True) -> None:
    """Request a connection to the target_mac_address

    :param target_mac_address:
    :param connection_parameters:
    :param scan_parameters:
    :param uuid_base:
    :param exchange_att_mcu_upon_connect:
    :param discover_services_upon_connect:
    """
    self.logger.info(f'scanning for 0x{target_mac_address}')

    self.target_addr = target_mac_address
    self.actual_conn_params = None
    self.actual_att_mtu = None

    if connection_parameters is not None:
      self.connection_parameters = connection_parameters

    if scan_parameters is not None:
      self.scan_parameters = scan_parameters

    if uuid_base is not None:
      self.add_base_uuid(uuid_base)

    # opting for more time rather than connect of same scan duration
    if self.connection_status is ConnectionStatus.Scanning:
      try:
        self.adapter.driver.ble_gap_scan_stop()
      except:
        pass

    try:
      self.connection_status = ConnectionStatus.Connecting
      self.adapter.driver.ble_gap_scan_start(scan_params=self.scan_parameters)

      self.conn_handle = self.conn_q.get(timeout=self.scan_parameters.timeout_s)
    except Empty:
      self.logger.error(f'timeout...target 0x{target_mac_address}')
      time.sleep(1)

      try:
        self.adapter.driver.ble_gap_scan_stop()
      except NordicAdapter.NordicSemiException as nse:
        self.logger.exception(nse)
        self.connection_status = ConnectionStatus.NoConnection
      finally:
        self.get_scan_data()

    except NordicAdapter.NordicSemiException:
      self.logger.error(f'error connecting to target 0x{target_mac_address}')
      time.sleep(1)
      # logger.exception(e)
      self.connection_status = ConnectionStatus.NoConnection

    try:
      if exchange_att_mcu_upon_connect:
        self.adapter.att_mtu_exchange(self.conn_handle, self.adapter.default_mtu)

      if discover_services_upon_connect:
        self.logger.debug('Discovering all services')
        self.adapter.service_discovery(self.conn_handle)
    except:
      pass

  def pair(self, bond=True, mitm=True, lesc=False, keypress=False, io_caps=NordicDriver.BLEGapIOCaps.none, oob=False,
           min_key_size=7, max_key_size=16, enc_own=True, id_own=False, sign_own=False, link_own=False, enc_peer=True,
           id_peer=False, sign_peer=False, link_peer=False) -> None:
    self.adapter.authenticate(conn_handle=self.conn_handle,
                              _role=None,
                              bond=bond,
                              mitm=mitm,
                              lesc=lesc,
                              keypress=keypress,
                              io_caps=io_caps,
                              oob=oob,
                              min_key_size=min_key_size,
                              max_key_size=max_key_size,
                              enc_own=enc_own,
                              id_own=id_own,
                              sign_own=sign_own,
                              link_own=link_own,
                              enc_peer=enc_peer,
                              id_peer=id_peer,
                              sign_peer=sign_peer,
                              link_peer=link_peer)

  def disconnect(self) -> None:
    self.adapter.disconnect(self.conn_handle)
    self.connection_status = ConnectionStatus.NoConnection

  def characteristic_read(self, characteristic: NordicDriver.BLEUUID,
                          service: Service = None) -> (NordicDriver.BLEGattStatusCode, bytes):
    """Perform GATT read on characteristic

    :param characteristic:  characteristic to read from
    :param service:         service containing characteristic

    :return:  Tuple (GATT response status,
                     return data payload)
    """
    if service is not None:
      handle = None   # find handle to read from
      for svc in self.adapter.db_conns[self.conn_handle].services:
        if svc.uuid.value == service.uuid.value:
          for char in svc.chars:
            if char.uuid.value == characteristic.value:
              handle = char.handle_value

      self.adapter.driver.ble_gattc_read(self.conn_handle, handle, 0)
      ret = self.adapter.evt_sync[self.conn_handle].wait(evt=NordicDriver.BLEEvtID.gattc_evt_write_rsp)
      return ret['status'], ret['data']

    if service is None:
      gatt_rsp, data = self.adapter.read_req(self.conn_handle, characteristic)
      return gatt_rsp, bytes(data)

  def characteristic_write(self, characteristic: NordicDriver.BLEUUID,
                           payload: bytes,
                           service: Service = None) -> None:
    """Perform GATT write on characteristic

    :param characteristic:  characteristic to write to
    :param payload:         data payload to write
    :param service:         service containing characteristic
    """
    handle = None   # find handle to write to

    if service is not None:
      for serv in self.adapter.db_conns[self.conn_handle].services:
        if serv.uuid.value == service.uuid.value:
          for char in serv.chars:
            if char.uuid.value == characteristic.value:
              handle = char.handle_value
    else:
      for serv in self.adapter.db_conns[self.conn_handle].services:
        for char in serv.chars:
          if char.uuid.value == characteristic.value:
            handle = char.handle_value

    if handle is None:
      raise NordicAdapter.NordicSemiException(f'Characteristic {str(characteristic)} not found')

    write_params = NordicDriver.BLEGattcWriteParams(
      write_op=NordicDriver.BLEGattWriteOperation.write_req,
      flags=NordicDriver.BLEGattExecWriteFlag.unused,
      handle=handle,
      data=payload,
      offset=0
    )

    self.adapter.driver.ble_gattc_write(self.conn_handle, write_params)
    self.adapter.evt_sync[self.conn_handle].wait(evt=NordicDriver.BLEEvtID.gattc_evt_write_rsp, timeout=10)

  def configure_client_characteristic_descriptor(self, characteristic: NordicDriver.BLEUUID,
                                                 en_ind: bool,
                                                 en_ntf: bool,
                                                 attr_handle: (int | None) = None):
    """Update the characteristic's CCCD value to enable/disable indications and/or notifications

    :param characteristic:  characteristic to update
    :param en_ind:          enable/disable indications for characteristic
    :param en_ntf:          enable/disable notifications for characteristic
    :param attr_handle:     attribute handle
    """
    self.logger.debug(f'Configuring client characteristic descriptor on {characteristic}')

    assert isinstance(characteristic, NordicDriver.BLEUUID), "Invalid argument type"

    if characteristic.base.base is not None and characteristic.base.type is None:
      self.adapter.driver.ble_uuid_decode(characteristic.base.base, characteristic)

    assert isinstance(characteristic, NordicDriver.BLEUUID), "Invalid argument type"

    if characteristic.base.base is not None and characteristic.base.type is None:
      self.adapter.driver.ble_uuid_decode(characteristic.base.base, characteristic)

    cccd_list = [0, 0]
    if en_ntf:
      cccd_list[0] |= 0x01
    if en_ind:
      cccd_list[0] |= 0x02

    cccd_handle: (int | None) = self.adapter.db_conns[self.conn_handle].get_cccd_handle(characteristic, attr_handle)
    if cccd_handle is None:
      raise NordicAdapter.NordicSemiException("CCCD not found")

    write_params = NordicDriver.BLEGattcWriteParams(
      NordicDriver.BLEGattWriteOperation.write_req,
      NordicDriver.BLEGattExecWriteFlag.unused,
      cccd_handle,
      cccd_list,
      0
    )
    self.adapter.driver.ble_gattc_write(self.conn_handle, write_params)
    result = self.adapter.evt_sync[self.conn_handle].wait(evt=NordicDriver.BLEEvtID.gattc_evt_write_rsp)
    return result['status']

  def enable_notification(self, characteristic: NordicDriver.BLEUUID) -> None:
    """Enable notifications on characteristic

    :param characteristic:  characteristic to enable notifications on
    """
    self.logger.debug(f'Enabling notifications on {characteristic}')
    # self.adapter.service_discovery(self.conn_handle, characteristic)
    self.adapter.enable_notification(self.conn_handle, characteristic)

  def disable_notification(self, characteristic: NordicDriver.BLEUUID) -> None:
    """Disable notifications on characteristic

    :param characteristic:  characteristics to disable notifications on
    """
    self.logger.debug(f'Disabling notifications on {characteristic}')
    self.adapter.disable_notification(self.conn_handle, characteristic)

  def on_notification(self, ble_adapter, conn_handle, uuid, data):
    self.logger.debug(f'conn_handle {conn_handle}: {uuid} = {data}')
    for svc in self.services.values():
      for char_uuid, char in svc.characteristics.items():
        if char_uuid == uuid:
          char.on_notification(payload=data)

  def enable_indication(self, characteristic: NordicDriver.BLEUUID) -> None:
    """Enable indications on characteristic

    :param characteristic:  characteristic to enable indications on
    """
    self.logger.debug(f'Enabling indications on {characteristic}')
    self.adapter.enable_indication(self.conn_handle, characteristic)

  def disable_indication(self, characteristic: NordicDriver.BLEUUID):
    """Disable notifications on characteristic

    :param characteristic:  characteristics to disable notifications on
    """
    self.logger.debug(f'Disabling indications on {characteristic}')
    self.adapter.disable_notification(self.conn_handle, characteristic)

  def on_indication(self, ble_adapter, conn_handle, uuid, data):
    self.logger.debug(f'conn_handle {conn_handle}: {uuid} = {data}')
    for svc in self.services.values():
      for char_uuid, char in svc.characteristics.items():
        if char_uuid == uuid:
          char.on_indication(payload=data)

  def add_base_uuid(self, base: NordicDriver.BLEUUIDBase) -> None:
    """Add base UUID to BLE driver for scanning and connecting

    :param base: base UUID to add
    """
    self.adapter.driver.ble_vs_uuid_add(base)

  def get_discovered_services(self) -> (dict[NordicDriver.BLEService, dict[NordicDriver.BLECharacteristic, NordicDriver.BLEDescriptor]] | None):
    try:
      if len(self.adapter.db_conns[self.conn_handle].services) > 0:
        for s in self.adapter.db_conns[self.conn_handle].services:
          self.logger.debug(f'[Service] {str(s)}')
          for c in s.chars:
            self.logger.debug(f'\t[Characteristic] {str(c)}')
            for d in c.descs:
              self.logger.debug(f'\t\t[Descriptor] {str(d)}')
      else:
        self.logger.warning('No services discovered')
      return self.adapter.db_conns[self.conn_handle].services
    except KeyError:
      self.logger.error('No conn_handle')
      return None

  def on_gap_evt_connected(self, ble_driver, conn_handle, peer_addr, role, conn_params):
    self.bd_address = peer_addr.addr.copy()
    self.bd_address.reverse()

    addr = ''.join('{0:02X}'.format(b) for b in peer_addr.addr)
    self.logger.info(f'Connected to 0x{addr}')

    self.actual_conn_params = conn_params
    self.conn_q.put(conn_handle)

  def on_gap_evt_disconnected(self, ble_driver, conn_handle, reason):
    self.logger.warning(f'Disconnected: {conn_handle} {reason}')
    self.conn_handle = None
    self.actual_conn_params = None
    self.actual_att_mtu = None
    self.connection_status = ConnectionStatus.NoConnection

  def on_gap_evt_sec_params_request(self, ble_driver, conn_handle, peer_params):
    self.logger.info(peer_params)

  def on_gap_evt_sec_info_request(self, ble_driver, conn_handle, peer_addr, master_id, enc_info, id_info, sign_info):
    self.logger.info(f'peer_addr={peer_addr}, master_id={master_id}, enc_info={enc_info}, '
                     f'id_info={id_info}, sign_info={sign_info}')

  def on_gap_evt_sec_request(self, ble_driver, conn_handle, bond, mitm, lesc, keypress):
    self.logger.info(f'bond={bond}, mitm={mitm}, lesc={lesc}, keypress={keypress}')

  def on_gap_evt_passkey_display(self, ble_driver, conn_handle, passkey):
    self.logger.info(f'passkey={passkey}')

  def on_gap_evt_timeout(self, ble_driver, conn_handle, src):
    self.logger.info(f'src={src}')
    if src in [NordicDriver.BLEGapTimeoutSrc.scan,
               NordicDriver.BLEGapTimeoutSrc.conn]:
      ble_driver.ble_gap_scan_start()

  def on_gap_evt_adv_report(self, ble_driver, conn_handle, peer_addr, rssi, adv_type, adv_data):
    addr_str = ''.join('{0:02X}'.format(b) for b in peer_addr.addr)

    if addr_str not in self.scan_data:
      self.scan_data[addr_str] = dict()

    for key, val in adv_data.records.items():
      if key not in self.scan_data[addr_str]:
        self.scan_data[addr_str][key] = []
      self.scan_data[addr_str][key] = val

    if NordicDriver.BLEAdvData.Types.complete_local_name in adv_data.records:
      name = f'{"".join(chr(e) for e in adv_data.records[NordicDriver.BLEAdvData.Types.complete_local_name])}, '
    elif NordicDriver.BLEAdvData.Types.short_local_name in adv_data.records:
      name = f'{"".join(chr(e) for e in adv_data.records[NordicDriver.BLEAdvData.Types.short_local_name])}, '
    else:
      name = 'N/A'

    self.scan_data[addr_str]['rssi'] = rssi

    self.logger.debug(
      f'Address: 0x{addr_str}, Device Name: {name}: '
      f'{[key + ": " + str(val) if isinstance(key, str) else key.name + ": " + str(val) for key, val in self.scan_data[addr_str].items()]}'
    )

    if self.connection_status is ConnectionStatus.Connecting and self.target_addr == addr_str:
      self.logger.info(f'Connecting to 0x{addr_str}')
      try:
        self.adapter.connect(address=peer_addr, conn_params=self.connection_parameters, tag=1)
        self.connection_status = ConnectionStatus.Connected
      except NordicAdapter.NordicSemiException as e:
        self.logger.error(f'failed to connect to {peer_addr}')
        self.logger.exception(e)

  def on_gap_evt_conn_param_update_request(self, ble_driver, conn_handle, conn_params):
    self.logger.info(conn_params)

  def on_gap_evt_conn_param_update(self, ble_driver, conn_handle, conn_params):
    self.logger.info(conn_params)

  def on_gap_evt_lesc_dhkey_request(self, ble_driver, conn_handle, peer_public_key, oobd_req):
    del ble_driver  # unused
    del conn_handle  # unused
    self.logger.info(f'peer_public_key={peer_public_key}, oodb_req={oobd_req}')

  def on_gap_evt_auth_status(self, ble_driver, conn_handle, error_src, bonded,
                             sm1_levels, sm2_levels, kdist_own, kdist_peer, auth_status):
    self.logger.info(f'Authentication status: {str(auth_status)}')

  def on_gap_evt_auth_key_request(self, ble_driver, conn_handle, key_type):
    passkey = self.passkey_q.get(timeout=10)
    pk = NordicDriver.util.list_to_uint8_array(passkey)
    NordicDriver.driver.sd_ble_gap_auth_key_reply(ble_driver.rpc_adapter, conn_handle, key_type, pk.cast())

  def on_gap_evt_conn_sec_update(self, ble_driver, conn_handle, conn_sec):
    self.logger.info(f'conn_sec={conn_sec}')

  def on_gap_evt_rssi_changed(self, ble_driver, conn_handle, rssi):
    self.logger.info(f'rssi={rssi}')

  def on_gattc_evt_write_rsp(self, ble_driver, conn_handle, status, error_handle, attr_handle, write_op, offset, data):
    self.logger.info(f'status={status}, error_handle={error_handle}, attr_handle={attr_handle}, '
                     f'write_op={write_op}, offset={offset}, data={data}')

  def on_gattc_evt_read_rsp(self, ble_driver, conn_handle, status, error_handle, attr_handle, offset, data):
    self.logger.info(f'status={status}, error_handle={error_handle}, attr_handle={attr_handle}, '
                     f'offset={offset}, data={data}')

  def on_gattc_evt_hvx(self, ble_driver, conn_handle, status, error_handle, attr_handle, hvx_type, data):
    self.logger.info(f'status={status}, error_handle={error_handle}, attr_handle={attr_handle}, '
                     f'hvx_type={hvx_type}, data={data}')

  def on_gattc_evt_prim_srvc_disc_rsp(self, ble_driver, conn_handle, status, services):
    self.logger.info(f'status={status}, services={[str(s) for s in services]}')

  def on_gattc_evt_char_disc_rsp(self, ble_driver, conn_handle, status, characteristics):
    self.logger.info(f'status={status}, characteristics={[str(c) for c in characteristics]}')

  def on_gattc_evt_desc_disc_rsp(self, ble_driver, conn_handle, status, descriptors):
    self.logger.info(f'status={status}, descriptors={[str(d) for d in descriptors]}')

  def on_gatts_evt_hvc(self, ble_driver, conn_handle, attr_handle):
    self.logger.info(f'attr_handle={attr_handle}')

  def on_gatts_evt_write(self, ble_driver, conn_handle, attr_handle, uuid, op, auth_required, offset, length, data):
    self.logger.info(f'attr_handle={attr_handle}, uuid={uuid}, op={op}, auth_required={auth_required}, '
                     f'offset={offset}, length={length}, data={data}')

  def on_gatts_evt_sys_attr_missing(self, ble_driver, conn_handle, hint):
    self.logger.info(f'hint={hint}')

  def on_evt_tx_complete(self, ble_driver, conn_handle, count):
    self.logger.info(f'count={count}')

  def on_gattc_evt_write_cmd_tx_complete(self, ble_driver, conn_handle, count):
    self.logger.info(f'count={count}')

  def on_gatts_evt_hvn_tx_complete(self, ble_driver, conn_handle, count):
    self.logger.info(f'count={count}')

  def on_gatts_evt_exchange_mtu_request(self, ble_driver, conn_handle, client_mtu):
    self.logger.info(f'client_mtu={client_mtu}')

  def on_gattc_evt_exchange_mtu_rsp(self, ble_driver, conn_handle, status, att_mtu):
    self.logger.info(f'status={status}, att_mtu={att_mtu}')
    self.actual_att_mtu = att_mtu

  def on_gap_evt_data_length_update(self, ble_driver, conn_handle, data_length_params):
    self.logger.info(f'data_length_params={data_length_params}')

  def on_gap_evt_data_length_update_request(self, ble_driver, conn_handle, data_length_params):
    self.logger.info(f'data_length_params={data_length_params}')

  def on_gap_evt_phy_update_request(self, ble_driver, conn_handle, peer_preferred_phys):
    self.logger.info(f'peer_preferred_phys={peer_preferred_phys}')

  def on_gap_evt_phy_update(self, ble_driver, conn_handle, status, tx_phy, rx_phy):
    self.logger.info(f'status={status}, tx_phy={tx_phy}, rx_phy={rx_phy}')

