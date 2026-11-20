import unittest
from unittest.mock import patch

import numpy as np

from asteroid_brightness import (
    OrbitParams, magnitude_at, magnitude_from_geometry, magnitude_from_positions,
)
from asteroid_brightness.ephemeris_jpl import JplGeometry


class ApiTests(unittest.TestCase):
    def test_geometry_scalar_and_batch(self):
        self.assertAlmostEqual(magnitude_from_geometry(20, .5, 1, 1, 0), 20, places=7)
        values = magnitude_from_geometry(20, .5, [1, 2], 1, 0)
        np.testing.assert_allclose(values - values[0], [0, 5*np.log10(2)])
        mixed = magnitude_from_geometry(20, [0.2, 0.5], 1, 1, [10, 10])
        self.assertEqual(mixed.shape, (2,))
        self.assertNotAlmostEqual(mixed[0], mixed[1])

    def test_positions_scalar_and_batch_with_offset_sun(self):
        # Translating the entire system cannot change geometry or brightness.
        base = magnitude_from_positions([2, 0, 0], [1, 0, 0], 20, .5)
        shifted = magnitude_from_positions([12, 0, 0], [11, 0, 0], 20, .5,
                                           sun_pos_au=[10, 0, 0])
        self.assertAlmostEqual(base, shifted)
        batch = magnitude_from_positions([[2, 0, 0], [.5, 0, 0]], [1, 0, 0], 20, .5)
        self.assertEqual(batch.shape, (2,))
        self.assertAlmostEqual(batch[0], base)
        self.assertGreater(batch[1], batch[0])

    def test_kepler_scalar_and_batch(self):
        orbit = OrbitParams(2.2, .15, 20, "2026-01-01T00:00:00Z")
        instant = "2026-11-20T00:00:00Z"
        result = magnitude_at("demo", instant, 20, .5, source="kepler",
                              asteroid_orbit=orbit)
        batch = magnitude_at("demo", [instant, "2026-11-22T00:00:00Z"], 20, .5,
                             source="kepler", asteroid_orbit=orbit)
        self.assertEqual(len(batch), 2)
        self.assertAlmostEqual(batch[0].v_mag, result.v_mag)

    def test_jpl_api_uses_geometry_not_reference_magnitude(self):
        sample = JplGeometry("2026-11-20T00:00:00Z", 2, 1, 0, 99, 10, .1)
        with patch("asteroid_brightness.ephemeris_jpl.query_jpl_geometry",
                   return_value=[sample, sample]) as query:
            result = magnitude_at(433, "2026-11-20T00:00:00Z", 20, .5)
            self.assertAlmostEqual(result.v_mag, magnitude_from_geometry(20, .5, 2, 1, 0))
            self.assertEqual(result.jpl_v_mag, 99)
            batch = magnitude_at(433, ["2026-11-20T00:00:00Z", "2026-11-22T00:00:00Z"], 20, .5)
            self.assertEqual(len(batch), 2)
            self.assertEqual(query.call_count, 2)


if __name__ == "__main__":
    unittest.main()
