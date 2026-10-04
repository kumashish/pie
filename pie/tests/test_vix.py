import unittest
import polars as pl

from pie.market.indicators.vix import RealizedVIX
from pie.market.vix import OptionContract, calculate_cboe_vix, calculate_realized_vix


class TestVIX(unittest.TestCase):
    def test_calculate_cboe_vix_basic(self):
        options = [
            OptionContract(strike=100.0, option_type="call", bid=5.0, ask=5.2),
            OptionContract(strike=100.0, option_type="put", bid=5.0, ask=5.2),
            OptionContract(strike=95.0, option_type="put", bid=2.5, ask=2.7),
            OptionContract(strike=105.0, option_type="call", bid=2.5, ask=2.7),
        ]

        res = calculate_cboe_vix(options, time_to_expiration_years=30 / 365, risk_free_rate=0.05)
        self.assertTrue(res.valid)
        self.assertGreater(res.vix, 0)
        self.assertGreater(res.forward_price, 0)
        self.assertEqual(res.strike_k0, 100.0)

    def test_calculate_cboe_vix_invalid_inputs(self):
        res = calculate_cboe_vix([], time_to_expiration_years=0.1, risk_free_rate=0.05)
        self.assertFalse(res.valid)
        self.assertEqual(res.reason, "No options data provided.")

        res_expired = calculate_cboe_vix([OptionContract(100.0, "call", 1.0, 1.2)], time_to_expiration_years=0.0, risk_free_rate=0.05)
        self.assertFalse(res_expired.valid)

    def test_calculate_realized_vix(self):
        prices = [100.0 + (i * 0.5 if i % 2 == 0 else -i * 0.3) for i in range(40)]
        df = pl.DataFrame({"close": prices})

        vix_val = calculate_realized_vix(df, window=30)
        self.assertIsNotNone(vix_val)
        self.assertGreater(vix_val, 0.0)

        # Indicator test
        ind = RealizedVIX(window=30)
        res = ind.calculate(df)
        self.assertTrue(res.valid)
        self.assertEqual(res.value, vix_val)
        self.assertEqual(res.name, "RealizedVIX(30)")


if __name__ == "__main__":
    unittest.main()

