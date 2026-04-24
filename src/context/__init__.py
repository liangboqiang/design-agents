"""Context engineering layer for runtime prompt/message assembly."""

from .assembler import ContextAssembler, PromptAssembler
from .history import HistoryCompressor, build_summary, micro_compact
from .knowledge import KnowledgePicker, KnowledgeSelection
from .packet import ContextPacket, PromptPacket
from .surface_assembler import SurfaceAssembler

__all__ = [
    "ContextAssembler",
    "ContextPacket",
    "HistoryCompressor",
    "KnowledgePicker",
    "KnowledgeSelection",
    "PromptAssembler",
    "PromptPacket",
    "SurfaceAssembler",
    "build_summary",
    "micro_compact",
]
