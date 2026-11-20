"""Check phase wrapping and weak-response stability classification independently."""
from pathlib import Path
import json
import numpy as np
from review_numerics import trace_review

f=np.array([1,100,200])*1e6
nominal=np.full(3,np.exp(1j*np.deg2rad(179)))
crossed=np.full(3,np.exp(1j*np.deg2rad(-179)))
phase=trace_review(f,nominal,crossed,nominal,.1)
np.testing.assert_allclose(phase['at_100mhz']['max_time_window_phase_change_deg'],2,atol=1e-10)
assert phase['resolved_fraction']==1
weak=np.full(3,1e-5,dtype=complex)
changed=weak.copy();changed[1]*=.8
stability=trace_review(f,weak,changed,weak,.1)
assert stability['at_100mhz']['resolved'] is False
assert stability['unresolved_bands_mhz']==[[100.,100.]]
unchanged=trace_review(f,weak,weak,weak,.1)
assert unchanged['resolved_fraction']==1
report={'classification':'SYNTHETIC_CHECK','wrapped_phase_difference_2deg':'passed',
        'weak_response_relative_change_20percent':'detected','unchanged_weak_response':'passed'}
(Path(__file__).resolve().parent/'review-helper-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
