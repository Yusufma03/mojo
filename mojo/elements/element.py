from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from dm_control import mjcf

if TYPE_CHECKING:
    from mojo import Mojo


class MujocoElement(ABC):
    def __init__(self, mojo: Mojo, mjcf_elem: mjcf.RootElement):
        self._mojo = mojo
        self._mjcf_elem = mjcf_elem

    @property
    def mjcf(self):
        return self._mjcf_elem