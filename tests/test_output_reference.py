import csv
import json
import subprocess
import sys
import numpy as np
import pytest
from analysis import rfcp, scope_tone
from analysis.output_reference import load_bundle, _align
from analysis.synthetic_output_reference import create, write_json, write_s
from tests.rehearsal_data import example


def case(tmp_path):
    source,metadata,expected=create(tmp_path/'input')
    meta=json.loads(metadata.read_text());bundle=json.loads((source.parent/'bundle.json').read_text())
    return source,metadata,meta,bundle,expected


def save(source,metadata,meta,bundle):
    write_json(metadata,meta);write_json(source.parent/'bundle.json',bundle)


def test_complex_wave_solution_and_full_frequency_range(tmp_path):
    source,metadata,meta,bundle,expected=case(tmp_path)
    _,_,_,rows,deps=rfcp.load_calibration(source,metadata)
    actual=[complex(r['zt_real_ohm'],r['zt_imag_ohm']) for r in rows]
    np.testing.assert_allclose(actual,expected,rtol=2e-14,atol=1e-14)
    assert len(deps)==10 and all(r['valid'] for r in rows)
    assert rows[-1]['frequency_hz']==500e6 and rows[-1]['uncertainty_db']==.2


@pytest.mark.parametrize('target,key,value',[
    ('reverse.identity','head_id','WRONG'),('reverse.identity','fixture_revision','R2'),
    ('forward.through','reference_plane_ids',['WRONG','WRONG']),('reverse.transfer','vna_calibration_id','WRONG'),
    ('forward.k','units','Iout/Icore'),('forward.k','source_fixture_revision','OLD'),
    ('load','connector','SMA-M'),('load','standards_connector','SMA-F'),
    ('load','calibration_id','SYN-2PORT-forward'),('load','applies_to_output_plane_ids',['WRONG']),
    ('load','sha256','0'*64),('review','configuration_id','WRONG'),
])
def test_mixed_configuration_provenance_rejected(tmp_path,target,key,value):
    source,metadata,meta,bundle,_=case(tmp_path);node=bundle
    for part in target.split('.'):node=node[part]
    node[key]=value;save(source,metadata,meta,bundle)
    with pytest.raises(ValueError):rfcp.load_calibration(source,metadata)


@pytest.mark.parametrize('column,value,flag',[
    ('uncertainty_db','','UNCERTAINTY_UNASSESSED'),('valid','false','REVIEW_REJECTED'),
    ('current_path_verified','false','CURRENT_PATH_UNVERIFIED'),('head_load_swap_verified','false','HEAD_LOAD_SWAP_UNVERIFIED'),
    ('forward_through_snr_db','2','LOW_SNR'),('reverse_transfer_snr_db','2','LOW_SNR'),
    ('direct_pickup_db','-10','DIRECT_PICKUP'),('repeatability_db','2','REPEATABILITY'),
])
def test_per_frequency_review_masks_absolute_output(tmp_path,column,value,flag):
    source,metadata,meta,bundle,_=case(tmp_path);path=source.parent/'review.csv'
    with path.open(newline='') as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;data=list(reader)
    data[2][column]=value
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(data)
    bundle['review']['sha256']=rfcp.sha256(path);save(source,metadata,meta,bundle)
    rows=rfcp.load_calibration(source,metadata)[3]
    assert not rows[2]['valid'] and flag in rows[2]['quality_flag']
    assert all(rows[2][key] is None for key in ['zt_magnitude_ohm','zt_real_ohm','zt_imag_ohm','zt_db_ohm','phase_deg'])
    assert rows[2]['s21_db'] is not None and rows[1]['valid'] and rows[3]['valid']
    with pytest.raises(ValueError):rfcp.tone_current_rms(20e6,.001,rows,meta,meta['included_chain_ids'])


@pytest.mark.parametrize('kind', ['through','k','load','direction_magnitude','direction_phase','reflection_phase','clipped','gap'])
def test_nulls_direction_phase_and_bands_block_quantification(tmp_path,kind):
    source,metadata,meta,bundle,_=case(tmp_path)
    if kind in ('through','direction_magnitude','direction_phase'):
        role='through' if kind=='through' else 'transfer';path=source.parent/bundle['reverse'][role]['file']
        f,s=rfcp.read_s2p(path);s[2,1,0]*={'through':0,'direction_magnitude':2,'direction_phase':1j}[kind]
        write_s(path,f,s);bundle['reverse'][role]['sha256']=rfcp.sha256(path)
    elif kind=='load':
        path=source.parent/'load.s1p';f,s=rfcp.read_s1p(path);s[2,0,0]=1;write_s(path,f,s);bundle['load']['sha256']=rfcp.sha256(path)
    elif kind=='k':
        path=source.parent/'forward_k.csv';lines=path.read_text().splitlines();parts=lines[3].split(',');parts[1:3]=['0','0'];lines[3]=','.join(parts)
        path.write_text('\n'.join(lines)+'\n');bundle['forward']['k']['sha256']=rfcp.sha256(path)
    elif kind=='reflection_phase':bundle['load']['phase_validated']=False
    elif kind=='clipped':meta['clipped']=True
    else:meta['invalid_frequency_bands_hz']=[[29e6,31e6]]
    save(source,metadata,meta,bundle);rows=rfcp.load_calibration(source,metadata)[3]
    assert not rows[2]['valid'] and rows[2]['zt_magnitude_ohm'] is None


def test_magnitude_only_does_not_claim_absolute_phase(tmp_path):
    source,metadata,meta,bundle,expected=case(tmp_path);meta['phase_validated']=False
    save(source,metadata,meta,bundle);rows=rfcp.load_calibration(source,metadata)[3]
    assert all(r['valid'] and r['phase_deg'] is None and r['zt_real_ohm'] is None for r in rows)
    np.testing.assert_allclose([r['zt_magnitude_ohm'] for r in rows],np.abs(expected))


def test_alignment_no_extrapolation_null_bridging_or_hidden_gap():
    f=np.array([1.,3.,7.]);v=np.array([1+1j,3+3j,7+7j]);target=np.array([.5,1.,2.,3.,5.,8.])
    policy=dict(method='linear_complex',maximum_gap_hz=2,valid_bands=[[1,7]],invalid_bands=[])
    result,valid=_align(target,f,v,np.array([True,True,True]),policy)
    assert valid.tolist()==[False,True,True,True,False,False] and result[2]==2+2j
    assert not _align([2.],f,v,[True,False,True],policy)[1][0]
    policy['invalid_bands']=[[1.4,1.6]]
    assert not _align([2.],f,v,[True,True,True],policy)[1][0]
    policy.update(invalid_bands=[],valid_bands=[[1,1.5],[1.6,7]])
    assert not _align([2.],f,v,[True,True,True],policy)[1][0]


def test_end_to_end_cli_manifest_and_cw(tmp_path):
    f,_,cal,t,v,scope=example()
    source,metadata,_=create(tmp_path/'input',f=f,zt=5/np.sqrt(10),calibration=cal)
    out=tmp_path/'zt'
    process=subprocess.run([sys.executable,'-m','analysis.rfcp',str(source),'--metadata',str(metadata),'--out',str(out)],capture_output=True,text=True)
    assert process.returncode==0,process.stderr
    manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['eligible_rows']==len(f) and len(manifest['inputs'])==10
    assert set(manifest['analysis_code_sha256'])=={'rfcp.py','output_reference.py'}
    assert (out/'response.png').stat().st_size>1000
    with pytest.raises(FileExistsError):rfcp.export(source,metadata,out)
    waveform=tmp_path/'cw.csv';np.savetxt(waveform,np.column_stack([t,v]),delimiter=',',header='time_s,voltage_v',comments='')
    scopefile=tmp_path/'cw.json';write_json(scopefile,scope)
    result=scope_tone.export(waveform,scopefile,tmp_path/'tone',source,metadata)
    assert result['current_rms_a']==pytest.approx(.001,rel=1e-10)
    assert len(json.loads((tmp_path/'tone/manifest.json').read_text())['inputs'])==12


@pytest.mark.parametrize('fmt', ['RI','MA','DB'])
def test_one_port_touchstone_v2(tmp_path,fmt):
    path=tmp_path/'load.s1p';z=.1+.2j
    pair=f'{z.real} {z.imag}' if fmt=='RI' else f'{abs(z) if fmt=="MA" else 20*np.log10(abs(z))} {np.angle(z,deg=True)}'
    path.write_text(f'[Version] 2.0\n# MHz S {fmt} R 50\n[Number of Ports] 1\n[Number of Frequencies] 2\n[Reference] 50\n[Network Data]\n1 {pair}\n2 {pair}\n[End]\n')
    f,s=rfcp.read_s1p(path);np.testing.assert_allclose(f,[1e6,2e6]);np.testing.assert_allclose(s[:,0,0],z)


@pytest.mark.parametrize('policy',['exact','linear','gap','invalid_band','null_endpoint','no_extrapolation'])
def test_file_grid_alignment_is_explicit_and_conservative(tmp_path,policy):
    source,metadata,meta,bundle,_=case(tmp_path)
    path=source.parent/'forward_through.s2p';f,s=rfcp.read_s2p(path)
    keep=np.arange(len(f))!=1
    if policy=='no_extrapolation':keep[0]=False
    if policy=='null_endpoint':s[0,1,0]=0
    write_s(path,f[keep],s[keep]);bundle['forward']['through']['sha256']=rfcp.sha256(path)
    if policy!='exact':bundle['alignment']=dict(method='linear_complex',maximum_gap_hz=50e6,evidence='SYNTHETIC interpolation test')
    if policy=='gap':bundle['alignment']['maximum_gap_hz']=1e6
    if policy=='invalid_band':meta['invalid_frequency_bands_hz']=[[3e6,4e6]]
    save(source,metadata,meta,bundle);rows=rfcp.load_calibration(source,metadata)[3]
    assert rows[1]['valid']==(policy=='linear')
    assert rows[2]['valid']


def test_unreviewed_output_plane_rejected(tmp_path):
    source,metadata,meta,bundle,_=case(tmp_path);meta['output_reference_plane']['verified']=False
    save(source,metadata,meta,bundle)
    with pytest.raises(ValueError,match='reference plane'):rfcp.load_calibration(source,metadata)


def test_powershell_uppercase_sha256_accepted(tmp_path):
    source,metadata,meta,bundle,_=case(tmp_path)
    bundle['load']['sha256']=bundle['load']['sha256'].upper();save(source,metadata,meta,bundle)
    assert all(row['valid'] for row in rfcp.load_calibration(source,metadata)[3])


def test_feedback_null_and_reverse_sign(tmp_path):
    source,metadata,meta,bundle,_=case(tmp_path)
    path=source.parent/'forward_through.s2p';f,s=rfcp.read_s2p(path)
    gamma=rfcp.read_s1p(source.parent/'load.s1p')[1][:,0,0];s[3,1,1]=1/gamma[3]
    write_s(path,f,s);bundle['forward']['through']['sha256']=rfcp.sha256(path)
    bundle['reverse']['polarity']=1
    save(source,metadata,meta,bundle);rows=rfcp.load_calibration(source,metadata)[3]
    assert 'FEEDBACK_NULL' in rows[3]['quality_flag']
    assert 'DIRECTION_PHASE_MISMATCH' in rows[2]['quality_flag']
    assert not any(r['valid'] for r in rows)
