import unittest

import numpy as np
from astropy.time import Time, TimeDelta

from asteroid_brightness.config import OrbitParams
from asteroid_brightness.geometry import observation_geometry
from asteroid_brightness.orbit_kepler import orbital_period_days, position_au
from asteroid_brightness.photometry import magnitude


class ModelTests(unittest.TestCase):
    def test_zero_phase_and_distance(self):
        self.assertAlmostEqual(magnitude(1, 1, 0, 20, .5), 20, places=7)

    def test_distance_scaling(self):
        difference = magnitude(2, 1, 0, 20, .5) - magnitude(1, 1, 0, 20, .5)
        self.assertAlmostEqual(difference, 5 * np.log10(2))

    def test_period_closes(self):
        params = OrbitParams(2.2, .15, 20, "2026-01-01T00:00:00Z")
        t = Time(params.t0) + TimeDelta(orbital_period_days(params), format="jd")
        np.testing.assert_allclose(position_au(params.t0, params),
                                   position_au(t.isot + "Z", params), atol=1e-8)

    def test_bad_params(self):
        for a, e in [(-1, 0), (1, 1)]:
            with self.subTest(a=a, e=e), self.assertRaises(ValueError):
                position_au("2026-01-01T00:00:00Z",
                            OrbitParams(a, e, 0, "2026-01-01T00:00:00Z"))

    def test_phase_angle_matches_cosine_law(self):
        ast = np.array([2.1, .4, 0.0])
        earth = np.array([.3, 1.0, 0.0])
        result = observation_geometry(ast, earth)
        r, delta = result["r_au"], result["delta_au"]
        earth_sun = np.linalg.norm(earth)
        cosine = (r*r + delta*delta - earth_sun*earth_sun) / (2*r*delta)
        expected = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        self.assertAlmostEqual(result["alpha_deg"], expected, places=10)

    def test_collinear_phase_angles(self):
        earth = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(observation_geometry([2.0, 0, 0], earth)["alpha_deg"], 0)
        self.assertAlmostEqual(observation_geometry([.5, 0, 0], earth)["alpha_deg"], 180)


if __name__ == "__main__":
    unittest.main()
