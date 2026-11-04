"""Conservative 2-D fit envelope, not a measured connector tolerance certificate.

The outer/inner ground-stake dimensions share geometry: do not separately add
maximum width AND maximum pitch error. Evaluate the actual edge coordinates.
The published drawing has no GD&T true-position or pin-straightness callout;
nominal symmetry and a centred signal pin are explicitly conditional.
"""
from pathlib import Path
from itertools import product
import math, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reviews/design_closure_20260921/sma'
OUT.mkdir(parents=True, exist_ok=True)

def evaluate(centre_drill, ground_drill):
    centre_min, ground_min = centre_drill-.08, ground_drill-.08
    # JLC's +/-0.05 mm interpreted conservatively on BOTH Cartesian axes.
    position_radial = math.hypot(.05, .05)
    centre_margin = centre_min/2 - 1.37/2 - position_radial
    cases = []
    for outer_x, inner_x, outer_y, inner_y, hx, hy in product(
            [5.98,6.18], [3.98,4.18], [5.98,6.18], [3.98,4.18],
            [-.05,.05], [-.05,.05]):
        # Positive quadrant; the other three quadrants are its reflections.
        corners = list(product([inner_x/2, outer_x/2],
                               [inner_y/2, outer_y/2]))
        distance = max(math.hypot(x-(2.54+hx), y-(2.54+hy))
                       for x,y in corners)
        cases.append(ground_min/2-distance)
    return dict(centre_drill_mm=centre_drill, ground_drill_mm=ground_drill,
                finished_centre_range_mm=[centre_min,centre_drill+.13],
                finished_ground_range_mm=[ground_min,ground_drill+.13],
                centre_radial_margin_mm=centre_margin,
                ground_corner_radial_margin_mm=min(cases),
                evaluated_ground_extreme_cases=len(cases),
                centre_annulus_at_max_hole_minus_xy_offset_mm=
                    (2.5-(centre_drill+.13))/2-position_radial,
                ground_annulus_at_max_hole_minus_xy_offset_mm=
                    (2.8-(ground_drill+.13))/2-position_radial,
                passes_conditional_edge_envelope=centre_margin>0 and min(cases)>0)

old, new = evaluate(1.5,1.7), evaluate(1.7,1.9)
assert not old['passes_conditional_edge_envelope']
assert new['passes_conditional_edge_envelope']
# Independent closed form of the extreme ground corner; correlated edge
# coordinates rather than independently maximized pin width and pin centre.
assert math.isclose(new['ground_corner_radial_margin_mm'],
                    (1.9-.08)/2-math.sqrt(2)*.6, abs_tol=1e-12)
report = dict(
    data_kind='CALCULATED_NOT_MEASURED',
    drawing='GCT RFPC-SMA28-F Rev1.2 2025-05-12, local source retained',
    jlc_source='https://jlcpcb.com/capabilities/pcb-capabilities',
    retrieved_date='2026-09-21',
    inputs=dict(signal_pin_diameter_mm=[1.17,1.37],
                ground_outer_span_mm=[5.98,6.18],
                ground_inner_span_mm=[3.98,4.18],
                hole_size_error_mm=[-.08,.13],
                hole_position_per_axis_mm=[-.05,.05]),
    old=old, proposed=new,
    interpretation='Old holes do not provide a conservative simultaneous-fit envelope. Enlarge only centre 1.50->1.70 and ground 1.70->1.90; retain pad outside diameters, 5.08 pitch, connector and mounting positions.',
    limitations=[
        'The drawing is not a GD&T true-position certificate. Symmetry about the connector axis and a centred, straight signal pin are assumptions of this edge model.',
        'JLC public capability is not an accepted order-specific inspection report.',
        'Maximum finished holes exceed the manufacturer recommended layout tolerance; solder fill and mechanical retention need first-article inspection.',
        'No force-fit, pin bending or drilling is authorized. Dry-fit all five pins before soldering and reject an incompatible first article.',
        'Expanded holes do not validate the RF response; the fixture EM comparison must use the revised-hole geometry.',
    ],
    first_article_acceptance=dict(
        centre_finished_diameter_min_mm=1.62,
        ground_finished_diameter_min_mm=1.82,
        additional_signal_pin_radial_eccentricity_design_limit_mm=.03,
        residual_signal_margin_with_design_eccentricity_mm=
            new['centre_radial_margin_mm']-.03,
        note='0.03 mm is a design acceptance allocation, not a manufacturer specification. Five-pin free insertion and flat seating are required; inspect solder wetting/fill and avoid cable loads during assembly.'),
)
(OUT/'fit_result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'old':old,'proposed':new},indent=2))
