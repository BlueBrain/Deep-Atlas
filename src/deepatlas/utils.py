from __future__ import annotations

import numpy as np


class Remapper:
    """Utility class for remapping of labels."""

    def __init__(self, *volumes: list[np.ndarray]) -> None:
        # initial checks
        if not volumes:
            raise ValueError("No volume provided")

        for volume in volumes:
            if not isinstance(volume, np.ndarray):
                raise TypeError("The inputs need to be numpy arrays")
            if not volume.dtype == np.uint32:
                raise TypeError("The dtype of the arrays needs to be uint32")

        self.storage: list[tuple[np.ndarray, np.ndarray, tuple[int, ...]]] = [
            (*np.unique(volume, return_inverse=True), volume.shape)
            for volume in volumes
        ]
        unique_overall = set()
        for unique, _, _ in self.storage:
            unique_overall |= set(unique)

        self.old2new = {x: i for i, x in enumerate(sorted(unique_overall))}
        self.new2old = {v: k for k, v in self.old2new.items()}

    def __len__(self) -> int:
        return len(self.storage)

    @staticmethod
    def remap(
        shape: tuple[int, ...],
        mapping: dict[int, int],
        unique: np.ndarray,
        inv: np.ndarray,
    ) -> np.ndarray:
        runique = np.array([mapping[x] for x in unique], dtype=np.uint32)

        return runique[inv].reshape(shape)

    def remap_old_to_new(self, i: int) -> np.ndarray:
        if not (0 <= i < len(self)):
            raise IndexError

        unique, inv, shape = self.storage[i]
        return self.remap(shape, self.old2new, unique, inv)

    def remap_new_to_old(self, volume: np.ndarray) -> np.ndarray:
        unique, inv = np.unique(volume, return_inverse=True)

        return self.remap(volume.shape, self.new2old, unique, inv)
