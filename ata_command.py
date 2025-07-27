
from enum import Enum, auto
from dataclasses import dataclass

class xfer_protocol(Enum):
    non_data = auto()
    read_pio = auto()
    write_pio = auto()
    read_dma = auto()
    write_dma = auto()
    read_fpdma = auto()
    write_fpdma = auto()
    pio = auto()
    dma = auto()
    fpdma = auto()

@dataclass
class ATA_COMMAND_28:
    feature: int = 0
    count: int = 0
    lba: int = 0
    device: int = 0
    command: int = 0
    protocol: xfer_protocol = xfer_protocol.non_data
    transfer_length: int = 0
    is_512_block: bool = False
    ext_command: bool = False
    def __post_init__(self):
        if not (0 <= self.feature <= 0xFF):
            raise ValueError(f"feature must be in range 0-255, got {self.feature}")
        if not (0 <= self.count <= 0xFFFF):
            raise ValueError(f"count must be in range 0-255, got {self.count}")
        if not (0 <= self.lba <= 0x0FFF_FFFF):
            raise ValueError(f"lba must be in range 28 bit, got {self.lba}")
        if not (0 <= self.device <= 0xFF):
            raise ValueError(f"device must be in range 0-255, got {self.device}")
        if not (0 <= self.command <= 0xFF):
            raise ValueError(f"command must be in range 0-255, got {self.command}")
        if not (self.protocol == xfer_protocol.pio or
                self.protocol == xfer_protocol.dma or
                self.protocol == xfer_protocol.fpdma):
            raise ValueError(f"protocol must be specified xfer direction, got {self.protocol}")
        if not (self.ext_command is False):
            raise ValueError(f"ext_command must be True for 28 bit LBA, got {self.ext_command}")
@dataclass
class ATA_COMMAND_48:
    feature: int = 0
    count: int = 0
    lba: int = 0
    icc: int = 0
    auxiliary: int = 0
    device: int = 0
    command: int = 0
    protocol: xfer_protocol = xfer_protocol.non_data
    transfer_length: int = 0
    is_512_block: bool = False
    ext_command: bool = True
    def __post_init__(self):
        if not (0 <= self.feature <= 0xFFFF):
            raise ValueError(f"feature must be in range 0-65535, got {self.feature}")
        if not (0 <= self.count <= 0xFFFF):
            raise ValueError(f"count must be in range 0-65535, got {self.count}")
        if not (0 <= self.lba <= 0xFFFF_FFFF_FFFF):
            raise ValueError(f"lba must be in range 48 bit, got {self.lba}")
        if not (0 <= self.icc <= 0xFF):
            raise ValueError(f"icc must be in range 0-255, got {self.icc}")
        if not (0 <= self.auxiliary <= 0xFFFFFFFF):
            raise ValueError(f"auxiliary must be in range 32 bit, got {self.auxiliary}")
        if not (0 <= self.device <= 0xFF):
            raise ValueError(f"device must be in range 0-255, got {self.device}")
        if not (0 <= self.command <= 0xFF):
            raise ValueError(f"command must be in range 0-255, got {self.command}")
        if not (self.protocol == xfer_protocol.pio or
                self.protocol == xfer_protocol.dma or
                self.protocol == xfer_protocol.fpdma):
            raise ValueError(f"protocol must be specified xfer direction, got {self.protocol}")
        if not (self.ext_command is True):
            raise ValueError(f"ext_command must be True for 48 bit LBA, got {self.ext_command}")
if __name__ == "__main__":
    pass