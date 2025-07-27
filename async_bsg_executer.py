import ctypes
import fcntl
import os
import threading

SG_IO = 0x2285

from dataclasses import dataclass
from ata_command import ATA_COMMAND, xfer_protocol

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
        reserved_0 = 0
        reserved_1 = 0
        reserved_2 = 0
        reserved_3 = 0
        reserved_4 = 0
        additional_cdb_length = self.additional_cdb_length
        service_action_MSB = (self.service_action >> 8) & 0xFF
        service_action_LSB = self.service_action & 0xFF
        byte1 = ((self.protocol & 0b1111) << 1) | (self.extend & 0x1)
        byte2 = ((self.off_line & 0b11) << 6) | ((self.ck_cond & 0b1) << 5) | ((self.t_type & 0b1) << 4) | \
                ((self.t_dir & 0b1) << 3) | ((self.byt_blok & 0b1) << 2) | (self.t_length & 0b11)
        reserved_5 = 0
        reserved_6 = 0
        if self.extend: # 48 bit LBA Command
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
            reserved_7 = 0
            icc = self.icc & 0xFF
            auxiliary_31_24 = (self.auxiliary >> 24) & 0xFF
            auxiliary_23_16 = (self.auxiliary >> 16) & 0xFF
            auxiliary_15_8 = (self.auxiliary >> 8) & 0xFF
            auxiliary_7_0 = self.auxiliary & 0xFF
        else: # 28 bit LBA Command
            lba_47_40 = 0
            lba_39_32 = 0
            lba_31_24 = 0
            lba_23_16 = (self.lba >> 16) & 0xFF
            lba_15_8 = (self.lba >> 8) & 0xFF
            lba_7_0 = self.lba & 0xFF
            features_15_8 = 0
            features_7_0 = self.features & 0xFF
            count_15_8 = 0
            count_7_0 = self.sector_count & 0xFF
            device = ((self.lba >> 24) & 0x0F) << 4
            device |= self.device & 0x0F
            command = self.command & 0xFF
            reserved_7 = 0  # Reserved byte, can be set to 0
            icc = 0
            auxiliary_31_24 = 0
            auxiliary_23_16 = 0
            auxiliary_15_8 = 0
            auxiliary_7_0 = 0
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

class bsg_with_ata_command_executor:
    def __init__(self, dev_path):
        self.dev_path = dev_path
        self.fd = os.open(dev_path, os.O_RDWR | os.O_NONBLOCK)
        self.io_thread = []

    def __del__(self):
        if hasattr(self, 'fd') and self.fd:
            os.close(self.fd)

    def _executer(self, command: ATA_COMMAND):
        ata_pt = ATA_PASS_THROUGH_32()
        ata_pt.protocol = command.protocol
        ata_pt.extend = command.ext_command  # 48 bit / 28 bit LBA Command
        ata_pt.off_line = 0  # オフラインモードは無効
        ata_pt.ck_cond = False  # チェックコンディションは無効
        ata_pt.t_type = True  # Block長はSector長に合わせる
        ata_pt.t_dir = command.protocol.is_read_xfer() # 転送方向
        ata_pt.byt_blok = not command.is_512_block # 512 bytes Block 転送かどうか
        ata_pt.t_length = 0b11 # TPSIUを転送長として使用(何？)

        if command.protocol.get_protocol() == xfer_protocol.non_data:
            ata_pt.protocol = 0x3 # Non-data command
        elif command.protocol.get_protocol() == xfer_protocol.pio:
            if command.protocol.is_read_xfer():
                ata_pt.protocol = 0x4 # PIO Data-In
            else:
                ata_pt.protocol = 0x5 # PIO Data-Out
        elif command.protocol.get_protocol() == xfer_protocol.dma:
            ata_pt.protocol = 0x6 # DMA
        elif command.protocol.get_protocol() == xfer_protocol.fpdma:
            ata_pt.protocol = 0xC # NCQ (FPDMA)
        else:
            raise ValueError(f"Unsupported transfer protocol: {command.protocol}")

        ata_pt.features = command.feature
        ata_pt.sector_count = command.count
        ata_pt.lba = command.lba
        ata_pt.device = command.device
        ata_pt.command = command.command

        if command.ext_command: # 48 bit LBA Command
            ata_pt.icc = command.icc
            ata_pt.auxiliary = command.auxiliary

        cdb_buf = (ctypes.c_ubyte * 32)(*ata_pt.cdb())
        sense_buf = (ctypes.c_ubyte * 32)()

        sg_io = sg_io_v4()
        sg_io.guard = ord('Q')
        sg_io.protocol = 0  # BSG_PROTOCOL_SCSI
        sg_io.subprotocol = 0  # BSG_SUB_PROTOCOL_SCSI_COMMAND
        sg_io.request_len = 32 # CDB length
        sg_io.request = ctypes.addressof(cdb_buf) # CDB buffer address
        sg_io.max_response_len = 32 # Sense buffer length
        sg_io.response = ctypes.addressof(sense_buf) # Sense buffer address
        sg_io.timeout = 5000
        sg_io.flags = 0

        if command.protocol.is_read_xfer:
            sg_io.din_xfer_len = command.transfer_length
            data_buf = (ctypes.c_ubyte * command.transfer_length)()
            sg_io.din_xferp = ctypes.addressof(data_buf)
            fcntl.ioctl(self.fd, SG_IO, sg_io) # 
            command.transfer_data = bytes(data_buf)
        else:
            print("Writing data to device...")
            sg_io.dout_xfer_len = command.transfer_length
            data_buf = (ctypes.c_ubyte * command.transfer_length).from_buffer_copy(command.transfer_data)
            sg_io.dout_xferp = ctypes.addressof(data_buf)
            fcntl.ioctl(self.fd, SG_IO, sg_io)

    def submit_command(self, command: ATA_COMMAND):
            io = threading.Thread(target=self._executer, args=(command,))
            print(hex(command.command) + " " + hex(command.command))
            self.io_thread.append(command)
            io.start()
            io.join()

def print_dwords_4_with_ascii(data):
    # 必要なら list → bytes に変換
    if isinstance(data, list):
        data = bytes(data)

    padded_data = data + b'\x00' * ((4 - len(data) % 4) % 4)

    dwords = [int.from_bytes(padded_data[i:i+4], 'little') for i in range(0, len(padded_data), 4)]

    for i in range(0, len(dwords), 4):
        dw_line = dwords[i:i+4]
        hex_part = ' '.join(f"{dw:08X}" for dw in dw_line)

        ascii_bytes = data[i*4:i*4+16]
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in ascii_bytes)

        print(f"{hex_part:<40} {ascii_part}")
if __name__ == "__main__":
    # Example usage
    dev_path = "/dev/bsg/1:0:0:0"  # Adjust the path as needed
    executer = bsg_with_ata_command_executor(dev_path)

    command = ATA_COMMAND(
        feature=0x8,
        lba=0x1,
        icc=0,
        auxiliary=0,
        device=0x40,
        command=0x60,
        protocol=xfer_protocol.read_fpdma,
        transfer_length=4096
    )
    executer.submit_command(command)
    print_dwords_4_with_ascii(command.transfer_data[:512])  # Print first 512 bytes of transfer data

