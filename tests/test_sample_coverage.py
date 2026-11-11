"""P1 coverage report fixture: missing packs or wrong key range must fail."""
import tempfile,unittest
from pathlib import Path
from tools.audit_sample_coverage import audit_assets


class SampleCoverage(unittest.TestCase):
    def test_empty_asset_root_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises((FileNotFoundError,AssertionError)):
                audit_assets(Path(tmp))

if __name__=='__main__':unittest.main()
