from pathlib import Path
import csv, hashlib, json
root = Path(__file__).resolve().parents[1]
prep=root/'datasets/mdc_ml_database_v1_prepared'
expected=['tmm_canonical_spectral_labels.csv','tmm_angular_sparse_labels.csv','tolerance_robustness_labels.csv','fdtd_external_reference_labels.csv','label_dictionary_extended.csv','manifest.json']
assert sorted(p.name for p in prep.iterdir() if p.is_file())==sorted(expected)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def csvr(n):
    return list(csv.DictReader((prep/n).open(encoding='utf-8',newline='')))
t=csvr('tmm_canonical_spectral_labels.csv'); a=csvr('tmm_angular_sparse_labels.csv'); tol=csvr('tolerance_robustness_labels.csv'); f=csvr('fdtd_external_reference_labels.csv')
assert len(t)==2688 and len(a)==2688 and len(tol)==8400 and len(f)==11
assert len({r['geometry_hash'] for r in t})==2688
from collections import Counter
assert Counter(r['topology_family'] for r in t)=={'Explicit':1848,'ZL-1':630,'ZL-2':210}
assert Counter(r['source_id'] for r in t)=={'tmm_coarse':2673,'tmm_refined':15}
assert sum(r['has_angular_fwhm_label'].lower()=='true' for r in a)==15
assert sum(r['has_max_angle_label'].lower()=='true' for r in a)==2
assert sum(r['parent_join_status']=='geometry_matched_canonical_missing' for r in tol)==1243
assert len({r['parent_nominal_geometry_hash'] for r in tol if r['parent_join_status']=='geometry_matched_canonical_missing'})==6
assert all(r['source_id'] in {'tmm_coarse','tmm_refined'} and r['usable_for_training'].lower()=='true' for r in t)
assert all(r['usable_for_training'].lower()=='false' for r in tol)
assert all(r['sample_role']=='fdtd_external_high_fidelity_reference' for r in f)
assert all(r['spectral_FWHM_label_status']=='not_available' for r in f)
assert all(r['spectral_FWHM_missing_reason']=='single_wavelength_simulation' for r in f)
m=json.loads((prep/'manifest.json').read_text(encoding='utf-8'))
assert m['source_git_head'].startswith('16ff883920c9d539b08b88434b2edf62046b9a8d')
for rel,info in m['input_files'].items():
    p=root/'datasets/mdc_ml_database_v1'/rel
    assert sha(p)==info['sha256'] and p.stat().st_size==info['bytes']
for rel,info in m['output_files'].items():
    p=root/rel
    assert sha(p)==info['sha256'] and p.stat().st_size==info['bytes']
report=(root/'reports/mdc_ml_database_label_views_v1.md').read_text(encoding='utf-8')
assert 'angular sparse' in report and 'single-wavelength spectral FWHM' in report and 'non-canonical parents' in report and 'TMM angular transmission metrics are plane-wave metrics' in report
bad=[]
for p in prep.rglob('*'):
    if p.is_file() and (any(x in p.name.lower() for x in ['model','checkpoint','prediction','loss']) or p.suffix.lower() in {'.fsp','.ldf'}): bad.append(str(p))
assert not bad, bad
files=[prep/x for x in expected]+[root/'reports/mdc_ml_database_label_views_v1.md',root/'scripts/build_mdc_ml_label_views_v1.py',root/'tests/test_mdc_ml_label_views_v1.py']
print(json.dumps({'prepared_files':len(expected),'counts':{'tmm':len(t),'angular':len(a),'tolerance':len(tol),'fdtd':len(f)},'topology':dict(Counter(r['topology_family'] for r in t)),'angular_fwhm_valid':15,'max_angle_valid':2,'missing_parent_hashes':6,'affected_tolerance_rows':1243,'files':[{'path':str(p.relative_to(root)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]},indent=2))
