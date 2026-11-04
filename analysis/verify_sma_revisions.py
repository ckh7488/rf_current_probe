"""Independently compare saved boards and exported drills, with KiCad Python."""
from pathlib import Path
import json,hashlib,re,zipfile,xml.etree.ElementTree as ET
import pcbnew as p
R=Path(__file__).resolve().parents[1]
mm=lambda n:round(p.ToMM(n),6)
xy=lambda v:(mm(v.x),mm(v.y))
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def outline(b):
    s=p.SHAPE_POLY_SET();assert b.GetBoardPolygonOutlines(s,False)
    def ring(a):return [xy(a.CPoint(i)) for i in range(a.PointCount())]
    return [(ring(s.COutline(i)),[ring(s.CHole(i,j)) for j in range(s.HoleCount(i))]) for i in range(s.OutlineCount())]
def pads(b):
    return sorted((fp.GetReference(),pd.GetNumber(),xy(pd.GetPosition()),xy(pd.GetSize()),xy(pd.GetDrillSize()),pd.GetNetname(),int(pd.GetAttribute())) for fp in b.GetFootprints() for pd in fp.Pads())
def tracks(b):
    rows=[]
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA):rows.append(('via',xy(t.GetPosition()),mm(t.GetDrillValue()),mm(t.GetWidth(p.F_Cu)),t.GetNetname()))
        else:rows.append(('track',xy(t.GetStart()),xy(t.GetEnd()),mm(t.GetWidth()),t.GetLayerName(),t.GetNetname()))
    return sorted(rows)
def read_drills(path):
    ts={};cur=None;rows=[]
    for line in path.read_text().splitlines():
        m=re.fullmatch(r'T(\d+)C([\d.]+)',line)
        if m:ts[m[1]]=float(m[2]);continue
        m=re.fullmatch(r'T(\d+)',line)
        if m:cur=m[1];continue
        m=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)',line)
        if m:rows.append((ts[cur],float(m[1]),-float(m[2])))
    return sorted(tuple(round(v,6) for v in row) for row in rows)
reports=[]
for directory in ['probe_head_A04_DRAFT','calibration_fixture_PCB_A03_DRAFT']:
    h=R/'hardware'/directory;c=json.loads((h/'revision.json').read_text())
    old=p.LoadBoard(str(h/'baseline'/(c['old_name']+'.kicad_pcb')))
    f=h/(c['new_name']+'.kicad_pcb');new=p.LoadBoard(str(f))
    assert outline(old)==outline(new),'External and window geometry must stay fixed'
    assert tracks(old)==tracks(new),'No trace or via changes authorized by this revision'
    assert old.GetDesignSettings().GetBoardThickness()==new.GetDesignSettings().GetBoardThickness()
    assert len(old.Zones())==len(new.Zones())
    changes=[]
    for a,b in zip(pads(old),pads(new)):
        assert a[:4]==b[:4] and a[5:]==b[5:]
        if a[4]!=b[4]:
            assert a[4] in [(1.5,1.5),(1.7,1.7)]
            assert b[4]==((1.7,1.7) if a[1]=='1' else (1.9,1.9))
            changes.append({'reference':a[0],'pad':a[1],'xy':a[2],'old':a[4][0],'new':b[4][0]})
    assert len(changes)==(5 if 'Head' in c['new_name'] else 10)
    erc=json.loads((h/'review/erc.json').read_text());drc=json.loads((h/'review/drc.json').read_text())
    assert all(not x['violations'] for x in erc['sheets'])
    assert not any(drc[k] for k in ['violations','unconnected_items','schematic_parity','ignored_checks'])
    pt=[];np=[]
    for fp in new.GetFootprints():
        for pd in fp.Pads():
            row=(mm(pd.GetDrillSize().x),*xy(pd.GetPosition()))
            (np if pd.GetAttribute()==p.PAD_ATTRIB_NPTH else pt).append(row)
    for t in new.GetTracks():
        if isinstance(t,p.PCB_VIA):pt.append((mm(t.GetDrillValue()),*xy(t.GetPosition())))
    assert sorted(pt)==read_drills(h/'gerbers_DRAFT'/(c['new_name']+'-PTH.drl'))
    assert sorted(np)==read_drills(h/'gerbers_DRAFT'/(c['new_name']+'-NPTH.drl'))
    edges_old=(R/'hardware'/c['source_directory']/'gerbers_DRAFT'/(c['old_name']+'-Edge_Cuts.gm1'))
    if not edges_old.exists():edges_old=R/'hardware'/c['source_directory']/'fabrication_DRAFT'/(c['old_name']+'-Edge_Cuts.gm1')
    # Gerber commands independent of variable generator date/project metadata.
    def gerber_commands(path):return [x for x in path.read_text().splitlines() if not x.startswith(('G04','%TF.'))]
    edge_export_unchanged=gerber_commands(edges_old)==gerber_commands(h/'gerbers_DRAFT'/(c['new_name']+'-Edge_Cuts.gm1')) if edges_old.exists() else None
    assert edge_export_unchanged is not False
    package=h/(c['new_name']+'_REVIEW_ONLY.zip')
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None
        entries=z.namelist();assert len(entries)==len(set(entries))
        for name in entries:
            assert z.read(name)==(h/'gerbers_DRAFT'/name).read_bytes(),name
        assert set(entries)=={f.name for f in (h/'gerbers_DRAFT').iterdir() if f.is_file()}
    out=dict(data_kind='CALCULATED_NOT_MEASURED',source_pcb_sha256=sha(f),
             external_outline_windows_thickness_identical=True,
             footprints_pad_perimeters_coordinates_nets_identical=True,
             signal_tracks_and_vias_identical=True,gerber_outline_commands_identical=edge_export_unchanged,
             erc_drc_parity_unconnected_ignored_all_zero=True,
             drill_coordinates_match_saved_board=True,pth_count=len(pt),npth_count=len(np),
             review_zip_byte_matches_exports=True,review_zip_sha256=sha(package),
             intentional_hole_changes=changes,
             limitations=['No RF response, solder joint strength, pin straightness or physical fit is certified by ERC/DRC.','No JLC submission or fabrication approval follows from this check.'])
    (h/'review/revision_verification.json').write_text(json.dumps(out,indent=2))
    reports.append({'directory':directory,**{k:v for k,v in out.items() if k not in ['intentional_hole_changes','limitations']}})
hashes=json.loads((R/'reviews/design_closure_20260921/baseline_hashes.json').read_text())
assert all(sha(R/file)==v for file,v in hashes.items())
report=dict(revisions=reports,old_files_and_15_print_stl_byte_identical=True)
(R/'reviews/design_closure_20260921/pcb_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
