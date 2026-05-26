"""
项目名称: forklift-monitoring-yolo-uwb
技术领域: 02-computer-vision
模块说明: protocol.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class GNMFrame:
    cmd_type: int
    seq: int
    payload: bytes
    checksum: int


class GNMProtocolParser:
    HEADER = b"\x59\x4D"

    def feed(self, buffer: bytes) -> List[GNMFrame]:
        frames: List[GNMFrame] = []
        idx = 0
        while idx + 8 <= len(buffer):
            if buffer[idx : idx + 2] != self.HEADER:
                idx += 1
                continue
            cmd_type = buffer[idx + 2]
            seq = int.from_bytes(buffer[idx + 3 : idx + 5], "little")
            cmd_len = int.from_bytes(buffer[idx + 5 : idx + 7], "little")
            total_len = 2 + 1 + 2 + 2 + cmd_len + 1
            if idx + total_len > len(buffer):
                break
            frame_bytes = buffer[idx : idx + total_len]
            checksum = frame_bytes[-1]
            expected = sum(frame_bytes[:-1]) & 0xFF
            if checksum == expected:
                frames.append(GNMFrame(cmd_type=cmd_type, seq=seq, payload=frame_bytes[7:-1], checksum=checksum))
            idx += total_len
        return frames

    @staticmethod
    def describe(frame: GNMFrame) -> Dict[str, object]:
        return {"cmd_type": frame.cmd_type, "seq": frame.seq, "payload_len": len(frame.payload)}
