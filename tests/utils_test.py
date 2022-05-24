import numpy as np
import pytest

from deepatlas.utils import Remapper


class TestRemapper:
    def test_invalid_input(self):

        with pytest.raises(ValueError, match="No volume provided"):
            Remapper()

        with pytest.raises(TypeError, match="numpy arrays"):
            Remapper([3423])

        with pytest.raises(TypeError, match="needs to be uint32"):
            array_1 = np.array([2, 5], dtype=np.int32)
            array_2 = np.array([2, 3], dtype=np.uint32)
            Remapper(array_1, array_2)

    def test_overall(self):
        volume_0 = np.array(
            [
                [10, 30],
                [5, 79],
                [10, 5],
            ],
            dtype=np.uint32,
        )
        volume_1 = np.array(
            [
                [35, 30],
                [52, 10],
                [10, 5],
            ],
            dtype=np.uint32,
        )
        remapper = Remapper(volume_0, volume_1)

        assert remapper.old2new == {
            5: 0,
            10: 1,
            30: 2,
            35: 3,
            52: 4,
            79: 5,
        }
        assert remapper.new2old == {
            0: 5,
            1: 10,
            2: 30,
            3: 35,
            4: 52,
            5: 79,
        }

        with pytest.raises(IndexError):
            remapper.remap_old_to_new(-1)

        with pytest.raises(IndexError):
            remapper.remap_old_to_new(2)

        # Test remapping
        new_volume_0 = remapper.remap_old_to_new(0)
        new_volume_0_expected = np.array(
            [
                [1, 2],
                [0, 5],
                [1, 0],
            ],
            dtype=np.uint32,
        )
        assert new_volume_0.dtype == np.uint32
        np.testing.assert_array_equal(new_volume_0, new_volume_0_expected)

        new_volume_1 = remapper.remap_old_to_new(1)
        new_volume_1_expected = np.array(
            [
                [3, 2],
                [4, 1],
                [1, 0],
            ],
            dtype=np.uint32,
        )
        assert new_volume_1.dtype == np.uint32
        np.testing.assert_array_equal(new_volume_1, new_volume_1_expected)

        # Undo remapping
        result = remapper.remap_new_to_old(
            np.array([5, 1, 3], dtype=np.uint32)
        )
        expected_result = np.array([79, 10, 35], dtype=np.uint32)

        np.testing.assert_array_equal(expected_result, result)
