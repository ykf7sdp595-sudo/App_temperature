import sys
import unittest
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook
from data_io import active_columns, derating, read_recording


def sample(name='Enregistrement', base=2, missing=None):
    w = Workbook()
    s = w.active
    s.title = name
    s.append(['Temps', 'Courant', 'T amb'] + [None]*12 + ['Marqueur'])
    s.append([None, 'Off', 'On'])
    s.append([datetime(2030,1,1), 999, 999])
    for i, temp in enumerate((20,40,60,80,100,120)):
        s.append([datetime(2026,1,1)+timedelta(seconds=i), base+i, 0] + [None]*12 + [None if temp == missing else f'palier_{temp:03d}'])
    s.append([datetime(2026,1,1), 999, 1])  # doublon
    out=BytesIO(); w.save(out)
    return out.getvalue()


class DataTests(unittest.TestCase):
    def test_read_and_derating(self):
        a = read_recording(sample(base=2), 'a.xlsm')
        b = read_recording(sample(base=1, missing=40), 'b.xlsm')
        self.assertEqual(len(a.times), 6)
        self.assertEqual(active_columns(a), [1])
        curves, result, diagnostics = derating([a,b], [1,1])
        self.assertEqual(curves['a.xlsm'][20], 2)
        self.assertEqual(result[20], (0.8, 2))
        self.assertAlmostEqual(result[40][0], 2.4)
        self.assertEqual(result[40][1], 1)
        self.assertTrue(any('40 °C' in message for message in diagnostics))

    @unittest.skipUnless((Path(__file__).resolve().parents[1] / 'Forme_data.xlsm').exists(), 'Modèle privé non fourni')
    def test_real_model(self):
        model = Path(__file__).resolve().parents[1] / 'Forme_data.xlsm'
        rec = read_recording(model.read_bytes(), model.name)
        self.assertEqual(len(rec.times), 4)
        self.assertIn(1, active_columns(rec))
        self.assertFalse(rec.markers)

    def test_zero_current_is_valid_for_calculation(self):
        rec = read_recording(sample(base=0), 'zero.xlsm')
        _, result, _ = derating([rec], [1])
        self.assertEqual(result[20], (0, 1))

    def test_requires_sheet(self):
        with self.assertRaisesRegex(ValueError, 'Enregistrement'):
            read_recording(sample(name='Autre'), 'essai.xlsm')


if __name__ == '__main__':
    unittest.main()

