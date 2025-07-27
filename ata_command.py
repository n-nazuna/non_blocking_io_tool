
from enum import Enum, auto
from dataclasses import dataclass, field

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
    def is_read_xfer(self):
        return self in (xfer_protocol.read_pio, xfer_protocol.read_dma, xfer_protocol.read_fpdma)
    def get_protocol(self):
        if self == xfer_protocol.non_data:
            return xfer_protocol.non_data
        elif self in ( xfer_protocol.read_pio , xfer_protocol.write_pio):
            return xfer_protocol.pio
        elif self in ( xfer_protocol.read_dma , xfer_protocol.write_dma):
            return xfer_protocol.dma
        elif self in ( xfer_protocol.read_fpdma , xfer_protocol.write_fpdma):
            return xfer_protocol.fpdma

@dataclass
class ATA_COMMAND:
    feature: int = 0
    count: int = 0
    lba: int = 0
    icc: int = 0
    auxiliary: int = 0
    device: int = 0
    command: int = 0
    protocol: xfer_protocol = xfer_protocol.non_data
    transfer_length: int = 0
    transfer_data: bytes = field(default_factory=list)
    is_512_block: bool = False
    ext_command: bool = True
    def __post_init__(self):
        if self.ext_command is True:
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
        else:
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
            if not (self.icc or self.auxiliary):
                raise ValueError(f"icc and auxiliary must be 0 when ext_command is False, got icc={self.icc}, auxiliary={self.auxiliary}")
        if      self.protocol in ( xfer_protocol.pio , xfer_protocol.dma , xfer_protocol.fpdma):
            raise ValueError(f"protocol must be specified xfer direction, got {self.protocol}")
if __name__ == "__main__":
    pass