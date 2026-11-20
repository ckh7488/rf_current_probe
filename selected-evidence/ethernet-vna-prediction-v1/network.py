"""Connect EM PCB terminals to independently specified component/fixture blocks."""
from pathlib import Path
import json
import numpy as np
import skrf as rf

HERE = Path(__file__).resolve().parent
C0 = 299792458.0


def eliminate(s, kept, gamma):
    """Load the remaining terminals with b_load=gamma*a_load (all Zref=50)."""
    other = [i for i in range(s.shape[-1]) if i not in kept]
    aa = s[:, kept][:, :, kept]
    al = s[:, kept][:, :, other]
    la = s[:, other][:, :, kept]
    ll = s[:, other][:, :, other]
    return aa + al @ gamma @ np.linalg.solve(np.eye(len(other))-ll @ gamma, la)


def floating_branch(z):
    """Two-terminal floating impedance, referenced to 50 ohms at each end."""
    z = np.asarray(z, dtype=complex)
    diagonal, cross = z/(z+100), 100/(z+100)
    result = np.empty((*z.shape, 2, 2), dtype=complex)
    result[..., 0, 0] = result[..., 1, 1] = diagonal
    result[..., 0, 1] = result[..., 1, 0] = cross
    return result


def balun(frequency):
    source = rf.Network(str(HERE/'input/ADT2-1T+___Plus25degC.s4p'))
    sampled = source.interpolate(rf.Frequency.from_f(frequency, unit='Hz'))
    # Keep physical pins [3,4,6], short pin 1 to the ideal reference.
    grounded = eliminate(sampled.s, [1, 3, 2], np.full((len(frequency), 1, 1), -1, dtype=complex))
    transform = np.array([[1, 0, 0], [0, 1/np.sqrt(2), -1/np.sqrt(2)],
                          [0, 1/np.sqrt(2), 1/np.sqrt(2)]])
    modal = transform @ grounded @ transform.T
    balanced = np.zeros_like(modal)
    balanced[:, :2, :2] = modal[:, :2, :2]
    balanced[:, 2, 2] = 1
    return transform.T @ balanced @ transform, modal


def fixture(frequency, mode, parameters):
    p = parameters
    omega = 2*np.pi*frequency
    count = len(frequency)
    jack_delay = p['rj45']['jack_contact_path_mm']*1e-3/(C0*p['rj45']['velocity_factor'])
    delay = np.full(8, jack_delay)
    load = np.broadcast_to(np.eye(8, dtype=complex), (count, 8, 8)).copy()
    if mode in ['match', 'loopback']:
        delay += p['plug']['internal_path_mm']*1e-3/(C0*p['plug']['internal_velocity_factor'])
    if mode == 'match':
        q = p['plug']['matched_pair']
        delay[:2] += q['external_path_per_leg_mm']*1e-3/(C0*q['external_velocity_factor'])
        resistance = q['resistance_ohm']
        capacitor = q['parallel_capacitance_pf']*1e-12
        z = 1/(1/resistance+1j*omega*capacitor)+1j*omega*q['series_inductance_nh']*1e-9
        load[:, :2, :2] = floating_branch(z)
    elif mode == 'loopback':
        q = p['plug']['loopback']
        for a, b in q['connections']:
            ia, ib = a-1, b-1
            delay[[ia, ib]] += q['external_path_per_leg_mm']*1e-3/(C0*q['external_velocity_factor'])
            z = q['series_resistance_per_join_ohm']+1j*omega*q['series_inductance_per_join_nh']*1e-9
            block = floating_branch(z)
            load[:, ia, ia] = block[:, 0, 0]
            load[:, ib, ib] = block[:, 1, 1]
            load[:, ia, ib] = block[:, 0, 1]
            load[:, ib, ia] = block[:, 1, 0]
    elif mode != 'open':
        raise ValueError(mode)
    travel = np.exp(-1j*omega[:, None]*delay)
    return travel[:, :, None]*load*travel[:, None, :]


def assembled(pcb_s, frequency, mode, parameters):
    gamma = np.zeros((len(frequency), 20, 20), dtype=complex)
    component, _ = balun(frequency)
    for i in range(4):
        gamma[:, i*3:i*3+3, i*3:i*3+3] = component
    gamma[:, 12:, 12:] = fixture(frequency, mode, parameters)
    result = eliminate(pcb_s, [0, 1, 2, 3], gamma)
    sma = parameters['sma']
    delay = sma['nominal_length_mm']*1e-3/(C0*sma['velocity_factor'])
    return result*np.exp(-2j*2*np.pi*frequency[:, None, None]*delay)


def self_checks():
    frequency = np.array([1e6, 100e6, 200e6])
    branch = floating_branch(np.full(3, 100.0))
    np.testing.assert_allclose(branch, np.full((3, 2, 2), .5))
    np.testing.assert_allclose(floating_branch(np.zeros(3)), np.tile([[0, 1], [1, 0]], (3, 1, 1)))
    for reflection in [0, 1, -1, .3+.1j]:
        phase = np.exp(-1j*2*np.pi*frequency*1e-9)
        s = np.zeros((3, 2, 2), complex)
        s[:, 0, 1] = s[:, 1, 0] = phase
        gamma = np.full((3, 1, 1), reflection, complex)
        np.testing.assert_allclose(eliminate(s, [0], gamma)[:, 0, 0], reflection*phase**2)
    # An ideal 50-to-100-ohm balun must match a floating 100-ohm load.
    u = np.array([[1, 0, 0], [0, 1/np.sqrt(2), -1/np.sqrt(2)], [0, 1/np.sqrt(2), 1/np.sqrt(2)]])
    modal = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
    ideal = np.broadcast_to(u.T @ modal @ u, (3, 3, 3))
    np.testing.assert_allclose(eliminate(ideal, [0], branch), 0, atol=1e-12)
    parameters = json.loads((HERE/'electrical-assumptions.json').read_text())
    for mode in ['open', 'match', 'loopback']:
        term = fixture(frequency, mode, parameters)
        np.testing.assert_allclose(term, term.transpose(0, 2, 1), atol=1e-12)
        assert np.linalg.svd(term, compute_uv=False).max() <= 1+1e-12
    component, _ = balun(frequency)
    assert np.linalg.svd(component, compute_uv=False).max() <= 1.001
    print(json.dumps({'analytical_load_and_delay_checks': 'passed', 'fixture_passivity_and_reciprocity': 'passed',
                      'vendor_differential_block_max_singular_value': float(np.linalg.svd(component, compute_uv=False).max())}))


if __name__ == '__main__':
    self_checks()
