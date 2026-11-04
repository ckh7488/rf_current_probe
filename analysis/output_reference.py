"""Whitepaper 11.6: file-backed output-port current calibration.

All arrays are complex, dimensionless power-wave S/Gamma or K=Icore/Iout.
Evidence and uncertainty are supplied by a reviewer, never invented by the code.
"""
from pathlib import Path
import csv
import json
import math
import numpy as np

IDENTITY = ('head_id', 'head_revision', 'fixture_id', 'fixture_revision', 'configuration_id',
            'turns', 'shield_revision', 'included_chain_ids', 'primary_load_id')
UNCERTAINTY_COMPONENTS = {'vna', 'load_reflection', 'k_model_common_error', 'head_load_swap',
                          'repeatability', 'position', 'direct_pickup'}
REVIEW_NUMBERS = ('forward_through_snr_db', 'forward_transfer_snr_db', 'reverse_through_snr_db',
                  'reverse_transfer_snr_db', 'direct_pickup_db', 'repeatability_db', 'uncertainty_db')
REVIEW_FLAGS = ('valid', 'current_path_verified', 'head_load_swap_verified', 'phase_verified')
LIMITS = ('minimum_through_magnitude', 'minimum_k_magnitude', 'minimum_one_minus_gamma',
          'minimum_feedback_denominator', 'minimum_snr_db', 'maximum_direct_pickup_db',
          'maximum_repeatability_db', 'maximum_direction_error_db', 'maximum_direction_phase_deg')


def _evidence(value, name):
    from analysis.rfcp import require_evidence
    require_evidence(value, name)


def _grid(values):
    f = np.asarray(values, float)
    if f.ndim != 1 or len(f) < 2 or not np.all(np.isfinite(f)) or np.any(f <= 0) or np.any(np.diff(f) <= 0):
        raise ValueError('Positive strictly increasing grid with at least two samples required')
    return f


def _bool(value):
    if value in ('true', 'false'):
        return value == 'true'
    raise ValueError('CSV booleans must be literal true/false')


def _csv(path, kind):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        expected = {'frequency_hz', 'k_real', 'k_imag', 'valid'} if kind == 'k' else {'frequency_hz', *REVIEW_NUMBERS, *REVIEW_FLAGS}
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != expected:
            raise ValueError(f'{kind} CSV columns must be {sorted(expected)}')
        rows = list(reader)
    f = _grid([float(r['frequency_hz']) for r in rows])
    if kind == 'k':
        values = np.array([complex(float(r['k_real']), float(r['k_imag'])) for r in rows])
        if not np.all(np.isfinite(values)):
            raise ValueError('K must contain finite complex values')
        return f, values, np.array([_bool(r['valid']) for r in rows])
    values = {}
    for key in REVIEW_NUMBERS:
        vals = [None if key == 'uncertainty_db' and r[key] == '' else float(r[key]) for r in rows]
        if any(x is not None and not math.isfinite(x) for x in vals):
            raise ValueError(f'Nonfinite review data: {key}')
        if key == 'uncertainty_db' and any(x is not None and x <= 0 for x in vals):
            raise ValueError('Assessed uncertainty must be positive; leave unknown bounds blank')
        if key == 'repeatability_db' and any(x < 0 for x in vals):
            raise ValueError('Repeatability spread must be nonnegative')
        values[key] = vals
    values.update({key: [_bool(r[key]) for r in rows] for key in REVIEW_FLAGS})
    return f, values


def _source(base, spec, expected_kind, dependencies):
    from analysis.rfcp import sha256
    path = (base / spec['file']).resolve()
    if spec.get('data_kind') != expected_kind:
        raise ValueError('Source data_kind differs from the acquisition/bundle')
    if not isinstance(spec.get('sha256'), str) or sha256(path) != spec['sha256'].lower():
        raise ValueError(f'Source SHA-256 mismatch: {path.name}')
    text = path.read_text(encoding='utf-8-sig')
    if any(line.lstrip().upper().startswith('! SYNTHETIC') for line in text.splitlines()) and expected_kind != 'SYNTHETIC':
        raise ValueError('SYNTHETIC source cannot be relabelled')
    dependencies.append(path)
    return path


def _identity(actual, expected):
    if not isinstance(actual, dict):
        raise ValueError('Acquisition identity required')
    for key in IDENTITY:
        value = expected.get(key)
        if key not in ('turns', 'included_chain_ids'):
            _evidence(value, key)
        if value is None or actual.get(key) != value:
            raise ValueError(f'Acquisition configuration mismatch: {key}')


def load_bundle(input_path, metadata_path, meta):
    """Resolve only explicitly named, hash-bound files relative to bundle JSON."""
    from analysis.rfcp import read_s1p, read_s2p
    model = meta['current_model']
    _evidence(model.get('evidence'), 'current model')
    bundle_path = (Path(metadata_path).resolve().parent / model['bundle_file']).resolve()
    bundle = json.loads(bundle_path.read_text(encoding='utf-8-sig'))
    if bundle.get('schema_version') != 1 or bundle.get('data_kind') != meta['data_kind']:
        raise ValueError('Output-reference schema/data_kind mismatch')
    if meta.get('uncertainty_db') is not None:
        raise ValueError('output_reference requires per-frequency review uncertainty, not a global bound')
    plane=meta.get('output_reference_plane',{})
    if plane.get('verified') is not True or plane.get('impedance_ohm') != 50:
        raise ValueError('Reviewed 50 ohm probe output reference plane required')
    _evidence(plane.get('id'),'probe output plane ID')
    _evidence(plane.get('evidence'),'probe output plane')
    for name in ('current_path', 'head_load_swap', 'limits', 'uncertainty'):
        _evidence(bundle.get('evidence', {}).get(name), name)
    if set(bundle.get('uncertainty_components', [])) != UNCERTAINTY_COMPONENTS:
        raise ValueError('Uncertainty review must include all listed physical error sources')
    alignment = bundle.get('alignment', {})
    if alignment.get('method') not in ('exact', 'linear_complex'):
        raise ValueError('Explicit exact or linear_complex alignment required')
    if alignment['method'] == 'linear_complex':
        gap = alignment.get('maximum_gap_hz')
        if isinstance(gap, bool) or not isinstance(gap, (int,float)) or not math.isfinite(gap) or gap <= 0:
            raise ValueError('Positive maximum_gap_hz required for interpolation')
        _evidence(alignment.get('evidence'), 'interpolation')
    limits = bundle.get('limits', {})
    for key in LIMITS:
        x = limits.get(key)
        if isinstance(x, bool) or not isinstance(x, (int,float)) or not math.isfinite(x):
            raise ValueError(f'Explicit finite limit required: {key}')
        if (key == 'maximum_direct_pickup_db' and x >= 0) or (key != 'maximum_direct_pickup_db' and x <= 0):
            raise ValueError(f'Invalid limit: {key}')
    if limits['maximum_direction_phase_deg'] > 180:
        raise ValueError('Direction phase limit must not exceed 180 degrees')
    dependencies = [bundle_path]
    base = bundle_path.parent
    prepared = dict(bundle=bundle, directions={})
    for direction in ('forward', 'reverse'):
        group = bundle[direction]
        _identity(group.get('identity'), meta)
        for key in ('input_plane_id', 'fixture_output_plane_id', 'probe_output_plane_id', 'vna_calibration_id', 'setup_id'):
            _evidence(group.get(key), direction+':'+key)
        if group['probe_output_plane_id'] != meta.get('output_reference_plane', {}).get('id'):
            raise ValueError('Probe output reference plane differs from calibration metadata')
        if type(group.get('polarity')) is not int or group['polarity'] not in (-1,1) or (direction == 'forward' and group['polarity'] != 1):
            raise ValueError('Explicit direction polarity (+1 forward, +1/-1 reverse) required')
        if type(group.get('phase_validated')) is not bool:
            raise ValueError('Explicit acquisition phase_validated required')
        if type(group.get('reflection_phase_validated')) is not bool:
            raise ValueError('Explicit S22 reflection phase validation required')
        _evidence(group.get('evidence'), direction+' acquisition')
        arrays = {}
        for role in ('through', 'transfer'):
            spec = group[role]
            if spec.get('setup_id') != group['setup_id'] or spec.get('vna_calibration_id') != group['vna_calibration_id']:
                raise ValueError('Through/transfer acquisition or VNA calibration ID mismatch')
            expected_planes = [group['input_plane_id'], group['fixture_output_plane_id'] if role == 'through' else group['probe_output_plane_id']]
            if spec.get('reference_plane_ids') != expected_planes:
                raise ValueError('Through/transfer reference plane mismatch')
            path = _source(base,spec,meta['data_kind'],dependencies)
            if direction == 'forward' and role == 'transfer' and path != Path(input_path).resolve():
                raise ValueError('CLI transfer file differs from bundle forward transfer')
            arrays[role] = read_s2p(path)
        kspec = group['k']
        if kspec.get('units') != 'Icore/Iout' or kspec.get('output_plane_id') != group['fixture_output_plane_id']:
            raise ValueError('K unit or output plane mismatch')
        if kspec.get('applies_to_fixture_revision') != meta['fixture_revision']:
            raise ValueError('K applicability revision mismatch')
        _evidence(kspec.get('source_fixture_revision'), 'K source revision')
        _evidence(kspec.get('applicability_evidence'), 'K applicability')
        if kspec['source_fixture_revision'] != meta['fixture_revision'] and kspec.get('revision_change_assessed') is not True:
            raise ValueError('K from another PCB revision needs an explicit assessed applicability review')
        kind = kspec.get('data_kind')
        if kind not in ('CALCULATED','SIMULATED','MEASURED','SYNTHETIC') or (meta['data_kind'] != 'SYNTHETIC' and kind == 'SYNTHETIC'):
            raise ValueError('Invalid K provenance')
        arrays['k'] = _csv(_source(base,kspec,kind,dependencies),'k')
        if type(kspec.get('phase_validated')) is not bool:
            raise ValueError('Explicit K phase_validated required')
        prepared['directions'][direction] = arrays
    load = bundle['load']
    if load.get('load_id') != meta['primary_load_id']:
        raise ValueError('Different external load ID')
    for key in ('reference_plane_id','calibration_id','standards_model_id','evidence'):
        _evidence(load.get(key), 'load '+key)
    if load.get('connector') != 'SMA-F' or load.get('calibration_method') != 'SOL_AT_FEMALE_PLANE' or load.get('calibrated') is not True:
        raise ValueError('Load requires separately SOL-calibrated SMA-F reference plane')
    if load['calibration_id'] in {bundle[x]['vna_calibration_id'] for x in ('forward','reverse')}:
        raise ValueError('Separate load one-port and through/transfer two-port calibration IDs required')
    if load.get('standards_connector') != 'SMA-M':
        raise ValueError('Male SOL standards/models required at the female load reference plane')
    if type(load.get('phase_validated')) is not bool:
        raise ValueError('Explicit load phase_validated required')
    if load.get('applies_to_output_plane_ids') != [bundle[x]['fixture_output_plane_id'] for x in ('forward','reverse')]:
        raise ValueError('Load reference plane applicability mismatch')
    _evidence(load.get('reference_plane_transfer_evidence'), 'load mating-plane equivalence')
    prepared['load'] = read_s1p(_source(base,load,meta['data_kind'],dependencies))
    review = bundle['review']
    _evidence(review.get('evidence'),'frequency review')
    if review.get('configuration_id') != meta['configuration_id']:
        raise ValueError('Frequency review configuration mismatch')
    prepared['review'] = _csv(_source(base,review,meta['data_kind'],dependencies),'review')
    prepared['dependencies'] = dependencies
    return prepared, dependencies


def _brackets(target, source, alignment):
    """No extrapolation. Never jump over a missing/invalid source sample."""
    indices=[]
    for value in target:
        i=int(np.searchsorted(source,value))
        if i < len(source) and source[i] == value:
            indices.append((i,i,0.));continue
        if alignment['method']=='exact' or i==0 or i==len(source) or source[i]-source[i-1]>alignment['maximum_gap_hz']:
            indices.append(None);continue
        left,right=source[i-1],source[i]
        if ('valid_bands' in alignment and not any(lo<=left and right<=hi for lo,hi in alignment['valid_bands'])) or any(lo<=right and hi>=left for lo,hi in alignment.get('invalid_bands',[])):
            indices.append(None);continue
        indices.append((i-1,i,float((value-source[i-1])/(source[i]-source[i-1]))))
    return indices


def _align(target, source, values, valid, alignment):
    shape=(len(target),)+np.asarray(values).shape[1:]
    result=np.full(shape,np.nan+1j*np.nan,complex);good=np.zeros(len(target),bool)
    for i,pair in enumerate(_brackets(target,source,alignment)):
        if pair is None:continue
        a,b,w=pair
        if not valid[a] or not valid[b]:continue
        result[i]=(1-w)*values[a]+w*values[b];good[i]=True
    return result,good


def _align_review(target, source, values, alignment):
    out=[]
    for pair in _brackets(target,source,alignment):
        if pair is None:out.append(None);continue
        a,b,_=pair;row={key:values[key][a] and values[key][b] for key in REVIEW_FLAGS}
        for key in REVIEW_NUMBERS:
            ends=[values[key][a],values[key][b]]
            row[key]=None if None in ends else (min(ends) if key.endswith('snr_db') else max(ends))
        out.append(row)
    return out


def extract_output_reference(f, transfer, meta, prepared):
    from analysis.rfcp import COLUMNS, QUALITY_CHECKS, band_mask
    if prepared is None:
        raise ValueError('output_reference requires load_bundle / load_calibration with the raw dependencies')
    bundle=prepared['bundle'];limits=bundle['limits']
    alignment=dict(bundle['alignment'],valid_bands=meta['valid_frequency_bands_hz'],invalid_bands=meta.get('invalid_frequency_bands_hz',[]))
    lf,ls=prepared['load'];raw_gamma=ls[:,0,0]
    gamma,load_good=_align(f,lf,raw_gamma,(np.abs(raw_gamma)<1)&(np.abs(1-raw_gamma)>limits['minimum_one_minus_gamma']),alignment)
    # A passive load requires |Gamma|<1. Near-open loads are rejected separately.
    gamma_good=load_good & (np.abs(gamma)<1) & (np.abs(1-gamma)>limits['minimum_one_minus_gamma'])
    responses={};reasons=[[] for _ in f]
    phases=[]
    for direction in ('forward','reverse'):
        data=prepared['directions'][direction];group=bundle[direction]
        tf,ts=data['through'];pf,ps=data['transfer'];kf,kv,kvalid=data['k']
        through,tok=_align(f,tf,ts,np.abs(ts[:,1,0])>limits['minimum_through_magnitude'],alignment)
        probe,pok=_align(f,pf,ps,np.ones(len(pf),bool),alignment)
        k,kok=_align(f,kf,kv,kvalid & (np.abs(kv)>limits['minimum_k_magnitude']),alignment)
        if direction=='forward' and (not np.array_equal(pf,f) or not np.array_equal(ps,transfer)):
            raise ValueError('Prepared forward transfer differs from extraction input')
        denominator=1-through[:,1,1]*gamma
        good=gamma_good & tok & pok & kok
        through_ok=np.abs(through[:,1,0])>limits['minimum_through_magnitude']
        k_ok=np.abs(k)>limits['minimum_k_magnitude']
        feedback_ok=np.abs(denominator)>limits['minimum_feedback_denominator']
        good &= through_ok & k_ok & feedback_ok
        z=np.full(len(f),np.nan+1j*np.nan,complex)
        with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
            z[good]=group['polarity']*50*probe[good,1,0]*denominator[good]/(through[good,1,0]*(1-gamma[good])*k[good])
        for i in range(len(f)):
            if not group['reflection_phase_validated'] or not bundle['load']['phase_validated']:reasons[i].append('REFLECTION_PHASE_UNVERIFIED')
            if not (tok[i] and pok[i] and kok[i] and load_good[i]):reasons[i].append(direction.upper()+'_MISSING_OR_INVALID_SOURCE')
            if not gamma_good[i]:reasons[i].append('LOAD_NULL_OR_NONPASSIVE')
            if not through_ok[i]:reasons[i].append(direction.upper()+'_THROUGH_NULL')
            if not k_ok[i]:reasons[i].append(direction.upper()+'_K_NULL')
            if not feedback_ok[i]:reasons[i].append(direction.upper()+'_FEEDBACK_NULL')
            if not np.isfinite(z[i]) or abs(z[i])<=meta['minimum_zt_ohm']:reasons[i].append(direction.upper()+'_ZT_NULL')
        responses[direction]=z
        phases.append(group['phase_validated'] and group['k']['phase_validated'])
    review=_align_review(f,*prepared['review'],alignment)
    in_band=band_mask(f,meta['valid_frequency_bands_hz']) & ~band_mask(f,meta.get('invalid_frequency_bands_hz',[]))
    global_quality=all(meta.get('quality_review',{}).get(k) is True for k in QUALITY_CHECKS)
    phase_available=meta['phase_validated'] and all(phases) and bundle['load']['phase_validated']
    rows=[]
    for i,freq in enumerate(f):
        flags=reasons[i];q=review[i];uncertainty=None
        if not in_band[i]:flags.append('OUTSIDE_VALID_BAND')
        if not global_quality:flags.append('QUALITY_UNASSESSED_OR_FAILED')
        if meta['clipped']:flags.append('CLIPPED')
        if q is None:flags.append('MISSING_FREQUENCY_REVIEW')
        else:
            uncertainty=q['uncertainty_db']
            if not q['valid']:flags.append('REVIEW_REJECTED')
            if not q['current_path_verified']:flags.append('CURRENT_PATH_UNVERIFIED')
            if not q['head_load_swap_verified']:flags.append('HEAD_LOAD_SWAP_UNVERIFIED')
            if min(q[k] for k in REVIEW_NUMBERS if k.endswith('snr_db'))<limits['minimum_snr_db']:flags.append('LOW_SNR')
            if q['direct_pickup_db']>limits['maximum_direct_pickup_db']:flags.append('DIRECT_PICKUP')
            if q['repeatability_db']>limits['maximum_repeatability_db']:flags.append('REPEATABILITY')
        if uncertainty is None:flags.append('UNCERTAINTY_UNASSESSED')
        z=responses['forward'][i];reverse=responses['reverse'][i]
        if np.isfinite(z) and np.isfinite(reverse) and min(abs(z),abs(reverse))>meta['minimum_zt_ohm']:
            ratio=reverse/z
            if abs(20*math.log10(abs(ratio)))>limits['maximum_direction_error_db']:flags.append('DIRECTION_MAGNITUDE_MISMATCH')
            if phase_available and q is not None and q['phase_verified'] and abs(np.angle(ratio,deg=True))>limits['maximum_direction_phase_deg']:flags.append('DIRECTION_PHASE_MISMATCH')
        phase_ok=phase_available and q is not None and q['phase_verified']
        valid=not flags
        row={key:None for key in COLUMNS}
        row.update(frequency_hz=float(freq),s21_db=float(20*np.log10(abs(transfer[i,1,0]))) if abs(transfer[i,1,0])>0 else None,
                   valid=valid,uncertainty_db=uncertainty,quality_flag='|'.join(dict.fromkeys(flags+([] if phase_ok else ['MAGNITUDE_ONLY']))) or 'REVIEWED')
        # An invalid output-reference row is deliberately relative-only, including in plots.
        if valid:
            row.update(zt_magnitude_ohm=float(abs(z)),zt_db_ohm=float(20*np.log10(abs(z))))
            if phase_ok:row.update(zt_real_ohm=float(z.real),zt_imag_ohm=float(z.imag),phase_deg=float(np.angle(z,deg=True)))
        rows.append(row)
    return rows
