"""Synthetic tests for phase wrapping, Touchstone ports and comparison deltas."""
from pathlib import Path
import csv
import importlib.util
import json
import tempfile
import unittest
import numpy as np
import skrf as rf

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ethernet_compare',HERE/'compare.py')
compare=importlib.util.module_from_spec(spec);spec.loader.exec_module(compare)


class CompareTests(unittest.TestCase):
    def test_wrapped_phase_delta(self):
        expected=np.exp(1j*np.deg2rad([179,-179]))
        actual=expected*np.exp(1j*np.deg2rad(3))
        np.testing.assert_allclose(compare.phase_delta(actual,expected),[3,3],atol=1e-12)

    def test_delay_line_and_reference(self):
        frequency=np.array([1e6,50e6,100e6,200e6])
        value=10**(-2/20)*np.exp(-2j*np.pi*frequency*2e-9)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);s=np.zeros((4,2,2),complex);s[:,1,0]=s[:,0,1]=value
            for z0 in [50,75]:
                name=root/('delay'+str(z0))
                rf.Network(frequency=rf.Frequency.from_f(frequency,unit='Hz'),s=s,z0=z0).write_touchstone(str(name))
            np.testing.assert_allclose(compare.read_measured(root/'delay50.s2p',frequency,1,0),value,atol=1e-12)
            with self.assertRaisesRegex(ValueError,'50 ohm'):compare.read_measured(root/'delay75.s2p',frequency,1,0)
            with self.assertRaisesRegex(ValueError,'1601'):compare.read_measured(root/'delay50.s2p',frequency[:2],1,0)

    def test_known_magnitude_and_phase_offset(self):
        with (compare.PRED/'predicted-observables.csv').open() as handle:rows=list(csv.DictReader(handle))
        f=np.array([float(r['frequency_hz']) for r in rows]);key='matched_a_s11'
        source=np.array([complex(float(r[key+'_real']),float(r[key+'_imag'])) for r in rows])
        shifted=source*10**(-.25/20)*np.exp(1j*np.deg2rad(3))
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);raw=root/'synthetic';raw.mkdir()
            rf.Network(frequency=rf.Frequency.from_f(f,unit='Hz'),s=shifted[:,None,None],z0=50).write_touchstone(str(raw/'03_load_A_J2'))
            (raw/'receipt.json').write_text(json.dumps({'classification':'SYNTHETIC','board_unit_id':'SYNTHETIC','instrument':'SYNTHETIC','acquired_at_kst':'SYNTHETIC'}))
            report=compare.compare(raw,root/'comparison')
            self.assertEqual(report['classification'],'SYNTHETIC_COMPARISON_CHECK')
            result=report['cases'][key]
            self.assertAlmostEqual(result['near_100mhz']['difference_db'],-.25,places=10)
            self.assertAlmostEqual(result['near_100mhz']['phase_difference_deg'],3,places=10)
            self.assertAlmostEqual(result['max_abs_difference_db_on_time_stable_points'],.25,places=10)
            self.assertAlmostEqual(result['max_abs_phase_difference_deg_on_time_stable_points'],3,places=10)
            with self.assertRaisesRegex(ValueError,'new comparison'):compare.compare(raw,root/'comparison')


if __name__=='__main__':unittest.main()
