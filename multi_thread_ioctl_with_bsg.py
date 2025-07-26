import ctypes
import fcntl
import os

SG_IO = 0x2285
ATA_PASS_THROUGH_16 = [
    0x85, 0x0D, 0x2D, 0x00,
    0x00, 0x00, 0x01, 0x00,
    0x01, 0x00, 0x00, 0x00,
    0x00, 0x40, 0x25, 0x00
]

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

def send_ata_pt_via_bsg(dev_path):
    fd = os.open(dev_path, os.O_RDONLY)

    # CDBの準備
    cdb_buf = (ctypes.c_ubyte * 16)(*ATA_PASS_THROUGH_16)
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

    os.close(fd)

send_ata_pt_via_bsg("/dev/bsg/1:0:0:0")  # bsgデバイスのパスは環境に応じて
