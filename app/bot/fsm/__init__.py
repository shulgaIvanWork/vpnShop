"""
FSM (Finite State Machine) for MAX VPN Bot.

Used to store user state during multi-step processes like payment flow.
"""

from .states import PaymentStates
from .storage import FSMStorage, RedisFSMStorage, MemoryFSMStorage

__all__ = [
    "PaymentStates",
    "FSMStorage",
    "RedisFSMStorage",
    "MemoryFSMStorage",
]
