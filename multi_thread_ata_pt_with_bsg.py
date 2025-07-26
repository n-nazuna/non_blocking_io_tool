import ctypes
import fcntl
import os
import threading

SG_IO = 0x2285

# ATA_PASS_THROUGH_32 = [
#     # 16
#     0x7F, 0x00, 0x00, 0x00,
#     0x00, 0x00, 0x00, 0x18,
#     0x1F, 0xF0, 0x00, 0x19,
#     0x2E, 0x40, 0x60, 0x00,
#     # 32
#     0x00, 0x00, 0x00, 0x00,
#     0x01, 0x00, 0x00, 0x00,
#     0x40, 0x60, 0x00, 0x00,
#     0x00, 0x00, 0x00, 0x00,
# ]

from dataclasses import dataclass

@dataclass
class ATA_PASS_THROUGH_32:
    operation_code: int = 0x7F
    control: int = 0x00
    additional_cdb_length: int = 0x18
    service_action: int = 0x1FF0
    protocol: int = 0
    extend: bool = False
    off_line: int = 0
    ck_cond: bool = False
    t_type: bool = False
    t_dir: bool = False
    byt_blok: bool = False
    t_length: int = 0
    features: int = 0
    sector_count: int = 0
    lba: int = 0
    device: int = 0
    command: int = 0
    icc: int = 0
    auxiliary: int = 0

    def __post_init__(self):
        if not self.operation_code == 0x7F:
            raise ValueError(f"operation_code must be 0x7F, got {self.operation_code}")
        if not self.additional_cdb_length == 0x18:
            raise ValueError(f"additional_cdb_length must be 0x18, got {self.additional_cdb_length}")
        if not self.service_action == 0x1FF0:
            raise ValueError(f"service_action must be 0x1FF0, got {self.service_action}")
        if not ( 0 <= self.protocol <= 0xF):
            raise ValueError(f"protocol must be in range 0-15, got {self.protocol}")
        if not ( 0 <= self.off_line <= 0x3):
            raise ValueError(f"off_line must be in range 0-3, got {self.off_line}")
        if not ( 0 <= self.t_length <= 0x3):
            raise ValueError(f"t_length must be in range 0-3, got {self.t_length}")
        if not (0 <= self.features <= 0xFFFF):
            raise ValueError(f"features must be in range 0-65535, got {self.features}")
        if not (0 <= self.sector_count <= 0xFFFF):
            raise ValueError(f"sector_count must be in range 0-65535, got {self.sector_count}")
        if not (0 <= self.lba <= 0xFFFF_FFFF_FFFF):
            raise ValueError(f"lba must be in range 48 bit, got {self.lba}")
        if not (0 <= self.device <= 0xFF):
            raise ValueError(f"device must be in range 0-255, got {self.device}")
        if not (0 <= self.command <= 0xFF):
            raise ValueError(f"command must be in range 0-255, got {self.command}")

    def cdb(self):
        operation_code = self.operation_code
        control = self.control
        reserved_0 = 0  # Reserved byte, can be set to 0
        reserved_1 = 0  # Reserved byte, can be set to 0
        reserved_2 = 0  # Reserved byte, can be set to 0
        reserved_3 = 0  # Reserved byte, can be set to 0
        reserved_4 = 0  # Reserved byte, can be set to 0
        additional_cdb_length = self.additional_cdb_length
        service_action_MSB = (self.service_action >> 8) & 0xFF
        service_action_LSB = self.service_action & 0xFF
        byte1 = ((self.protocol & 0b1111) << 1) | (self.extend & 0x1)
        byte2 = ((self.off_line & 0b11) << 6) | ((self.ck_cond & 0b1) << 5) | ((self.t_type & 0b1) << 4) | \
                ((self.t_dir & 0b1) << 3) | ((self.byt_blok & 0b1) << 2) | (self.t_length & 0b11)
        reserved_5 = 0  # Reserved byte, can be set to 0
        reserved_6 = 0  # Reserved byte, can be set to 0
        lba_47_40 = (self.lba >> 40) & 0xFF
        lba_39_32 = (self.lba >> 32) & 0xFF
        lba_31_24 = (self.lba >> 24) & 0xFF
        lba_23_16 = (self.lba >> 16) & 0xFF
        lba_15_8 = (self.lba >> 8) & 0xFF
        lba_7_0 = self.lba & 0xFF
        features_15_8 = (self.features >> 8) & 0xFF
        features_7_0 = self.features & 0xFF
        count_15_8 = (self.sector_count >> 8) & 0xFF
        count_7_0 = self.sector_count & 0xFF
        device = self.device & 0xFF
        command = self.command & 0xFF
        reserved_7 = 0  # Reserved byte, can be set to 0
        icc = self.icc & 0xFF
        auxiliary_31_24 = (self.auxiliary >> 24) & 0xFF
        auxiliary_23_16 = (self.auxiliary >> 16) & 0xFF
        auxiliary_15_8 = (self.auxiliary >> 8) & 0xFF
        auxiliary_7_0 = self.auxiliary & 0xFF
        return bytes([
            operation_code,
            control,
            reserved_0,
            reserved_1,
            reserved_2,
            reserved_3,
            reserved_4,
            additional_cdb_length,
            service_action_MSB,
            service_action_LSB,
            byte1,
            byte2,
            reserved_5,
            reserved_6,
            lba_47_40,
            lba_39_32,
            lba_31_24,
            lba_23_16,
            lba_15_8,
            lba_7_0,
            features_15_8,
            features_7_0,
            count_15_8,
            count_7_0,
            device,
            command,
            reserved_7,
            icc,
            auxiliary_31_24,
            auxiliary_23_16,
            auxiliary_15_8,
            auxiliary_7_0,
        ])

class sg_io_v4(ctypes.Structure):
    _fields_ = [
        ('guard', ctypes.c_int32),
        ('protocol', ctypes.c_uint32),
        ('subprotocol', ctypes.c_uint32),
        ('request_len', ctypes.c_uint32),
        ('request', ctypes.c_uint64),
        ('request_tag', ctypes.c_uint64),
        ('request_attr', ctypes.c_uint32),
        ('request_priority', ctypes.c_uint32),
        ('request_extra', ctypes.c_uint32),
        ('max_response_len', ctypes.c_uint32),
        ('response', ctypes.c_uint64),
        ('dout_iovec_count', ctypes.c_uint32),
        ('dout_xfer_len', ctypes.c_uint32),
        ('din_iovec_count', ctypes.c_uint32),
        ('din_xfer_len', ctypes.c_uint32),
        ('dout_xferp', ctypes.c_uint64),
        ('din_xferp', ctypes.c_uint64),
        ('timeout', ctypes.c_uint32),
        ('flags', ctypes.c_uint32),
        ('usr_ptr', ctypes.c_uint64),
        ('spare_in', ctypes.c_uint32),
        ('driver_status', ctypes.c_uint32),
        ('transport_status', ctypes.c_uint32),
        ('device_status', ctypes.c_uint32),
        ('retry_delay', ctypes.c_uint32),
        ('info', ctypes.c_uint32),
        ('duration', ctypes.c_uint32),
        ('response_len', ctypes.c_uint32),
        ('din_resid', ctypes.c_int32),
        ('dout_resid', ctypes.c_int32),
        ('generated_tag', ctypes.c_uint64),
        ('spare_out', ctypes.c_uint32),
        ('padding', ctypes.c_uint32),
    ]

def print_hex_dump(data: bytes, width: int = 4):
    for i in range(0, len(data), width):
        line = data[i:i+width]
        hex_part = ' '.join(f'{b:02X}' for b in line)
        print(hex_part)

def executer(fd,tag):
        # CDBの準備
        ata_pt = ATA_PASS_THROUGH_32()
        ata_pt.protocol = 0xC # FPDMA
        ata_pt.extend = True  # 48 bit LBA Command
        ata_pt.off_line = 0  # オフラインモードは無効
        ata_pt.ck_cond = False  # チェックコンディションは無効
        ata_pt.t_type = True  # Block長はSector長に合わせる
        ata_pt.t_dir = True  # 読み取り方向
        ata_pt.byt_blok = True  # ブロックモードを有効にする
        ata_pt.t_length = 2 # FEATURES Fieldを転送長として使用

        ata_pt.features = 0x01  # 例: 1セクタ読み取り
        ata_pt.sector_count = tag << 3 # タグを設定
        ata_pt.lba = 0x1 + tag
        ata_pt.device = 0x40 # 規格に書いてあるから
        ata_pt.command = 0x60  # ATA READ FPDMA QUEUED

        print_hex_dump(ata_pt.cdb(), width=4)
        cdb_buf = (ctypes.c_ubyte * 32)(*ata_pt.cdb())
        sense_buf = (ctypes.c_ubyte * 32)()
        data_buf = (ctypes.c_ubyte * 512)()  # 例: 512バイト読み取り

        io = sg_io_v4()
        io.guard = ord('Q')
        io.protocol = 0  # BSG_PROTOCOL_SCSI
        io.subprotocol = 0  # BSG_SUB_PROTOCOL_SCSI_COMMAND
        io.request_len = 16
        io.request = ctypes.addressof(cdb_buf)
        io.max_response_len = 32
        io.response = ctypes.addressof(sense_buf)
        io.din_xfer_len = 512
        io.din_xferp = ctypes.addressof(data_buf)
        io.timeout = 5000
        io.flags = 0

        # ioctl呼び出し
        fcntl.ioctl(fd, SG_IO, io)

        print(f"driver_status: {io.driver_status}")
        print(f"device_status: {io.device_status}")
        print(f"transport_status: {io.transport_status}")
        print(f"response data (ascii): {''.join(chr(b) if 32 <= b < 127 else '.' for b in data_buf[:512])}")

def send_ata_pt_via_bsg(dev_path):
    fd = os.open(dev_path, os.O_RDONLY|os.O_NONBLOCK)

    threads = []
    for tag in range(32):
        t = threading.Thread(target=executer, args=(fd,tag,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    os.close(fd)

send_ata_pt_via_bsg("/dev/bsg/0:0:0:0")  # bsgデバイスのパスは環境に応じて
