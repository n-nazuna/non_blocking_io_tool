import ctypes
import fcntl
import os
import random

SG_IO = 0x2285
SG_DXFER_FROM_DEV = -3  # Device → Host

class SG_IO_HDR(ctypes.Structure):
    _fields_ = [
        ("interface_id", ctypes.c_int),
        ("dxfer_direction", ctypes.c_int),
        ("cmd_len", ctypes.c_ubyte),
        ("mx_sb_len", ctypes.c_ubyte),
        ("iovec_count", ctypes.c_ushort),
        ("dxfer_len", ctypes.c_uint),
        ("dxferp", ctypes.c_void_p),
        ("cmdp", ctypes.c_void_p),
        ("sbp", ctypes.c_void_p),
        ("timeout", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("pack_id", ctypes.c_int),
        ("usr_ptr", ctypes.c_void_p),
        ("status", ctypes.c_ubyte),
        ("masked_status", ctypes.c_ubyte),
        ("msg_status", ctypes.c_ubyte),
        ("sb_len_wr", ctypes.c_ubyte),
        ("host_status", ctypes.c_ushort),
        ("driver_status", ctypes.c_ushort),
        ("resid", ctypes.c_int),
        ("duration", ctypes.c_uint),
        ("info", ctypes.c_uint),
    ]

class ATA_PASS_THROUGH_16:
    def __init__(self):
        self.operation_code = 0x85  # ATA PASS-THROUGH (16)
        self.multiple_count = 0
        self.protocol = 0
        self.extend = 0
        self.off_line = 0
        self.ck_cond = 0
        self.reserved = 0
        self.t_dir = 0
        self.byt_blok = 0
        self.t_length = 0

        self.features = 0
        self.sector_count = 0
        self.lba = 0

        self.device = 0
        self.command = 0
        self.control = 0

    def to_bytes(self):
        byte1 = (self.multiple_count & 0b111) << 5 | ((self.protocol & 0b1111) << 1) | (self.extend & 0x1)
        byte2 = ((self.off_line & 0b11) << 6) | ((self.ck_cond & 0b1) << 5) | ((self.reserved & 0b1) << 4) | \
                ((self.t_dir & 0b1) << 3) | ((self.byt_blok & 0b1) << 2) | (self.t_length & 0b11)
        features_low = self.features & 0xFF
        features_high = (self.features >> 8) & 0xFF
        sector_count = self.sector_count & 0xFF
        sector_count_ext = (self.sector_count >> 8) & 0xFF
        lba_low = self.lba & 0xFF
        lba_low_ext = (self.lba >> 8) & 0xFF
        lba_mid = (self.lba >> 16) & 0xFF
        lba_mid_ext = (self.lba >> 24) & 0xFF
        lba_high = (self.lba >> 32) & 0xFF
        lba_high_ext = (self.lba >> 40) & 0xFF

        return bytes([
            self.operation_code,
            byte1,
            byte2,
            features_high,
            features_low,
            sector_count_ext,
            sector_count,
            lba_low,
            lba_low_ext,
            lba_mid,
            lba_mid_ext,
            lba_high,
            lba_high_ext,
            self.device,
            self.command,
            self.control,
        ])

def send_ata_pass_through(dev_path):
    cdb_obj = ATA_PASS_THROUGH_16()
    cdb_obj.protocol = 12 # FPDMA
    cdb_obj.extend = 1
    cdb_obj.ck_cond = 1  # Check condition
    cdb_obj.t_dir = 1  # Device -> Host
    cdb_obj.byt_blok = 1
    cdb_obj.t_length = 2  # Transfer length in 512-byte blocks

    cdb_obj.features = 0x8
    cdb_obj.sector_count = 0
    cdb_obj.lba = 0x100

    cdb_obj.device = 0x00
    cdb_obj.command = 0x60
    cdb_obj.control = 0

    cdb_bytes = cdb_obj.to_bytes()
    print_cdb(cdb_bytes)
    cdb = (ctypes.c_ubyte * 16)(*cdb_bytes)

    sense = (ctypes.c_ubyte * 32)()
    data = (ctypes.c_ubyte * 512)()  # 実際の転送先（未使用の場合あり）

    hdr = SG_IO_HDR()
    hdr.interface_id = ord('S')
    hdr.dxfer_direction = SG_DXFER_FROM_DEV
    hdr.cmd_len = 16
    hdr.mx_sb_len = 32
    hdr.dxfer_len = 512
    hdr.dxferp = ctypes.cast(data, ctypes.c_void_p)
    hdr.cmdp = ctypes.cast(cdb, ctypes.c_void_p)
    hdr.sbp = ctypes.cast(sense, ctypes.c_void_p)
    hdr.timeout = 2000  # ms
    hdr.flags = 0

    fd = os.open(dev_path, os.O_RDONLY | os.O_DIRECT)
    try:
        for _ in range(1000):
            fcntl.ioctl(fd, SG_IO, hdr)
            print("Command sent.")
            print("Status:", hdr.status)
            print("Sense:", bytes(sense).hex())
            print("Data (first 64 bytes):", bytes(data[:64]).hex())
            print("Data (ASCII) :", ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[:64]))
    except Exception as e:
        print("Error:", e)
    finally:
        os.close(fd)

def print_cdb(cdb_bytes: bytes | bytearray):
    if len(cdb_bytes) != 16:
        print(f"Warning: CDB length is {len(cdb_bytes)}, expected 16 bytes")

    hex_str = ' '.join(f"{b:02X}" for b in cdb_bytes)
    print(f"CDB (16 bytes): {hex_str}")

send_ata_pass_through("/dev/sda")  # 適宜変更してください