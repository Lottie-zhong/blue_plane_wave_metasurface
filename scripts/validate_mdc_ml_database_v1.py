import csv,json,hashlib,math,re
from pathlib import Path
root = Path(__file__).resolve().parents[1]
db = root / 'datasets' / 'mdc_ml_database_v1'
files=sorted(db.iterdir()); bad=[]; heavy=[]
for p in files:
 if p.suffix.lower() in {'.fsp','.ldf','.mat','.h5','.hdf5','.npy','.npz'} or p.stat().st_size>50_000_000: heavy.append((p.name,p.stat().st_size))
 for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
  if re.search(r'(?i)(^|[,\s\[])(nan|inf|-inf)(?=$|[,\s\]])',line): bad.append((p.name,line[:120])); break
uni={}
for fn,key in [('geometry_master.csv','geometry_id'),('tmm_nominal_metrics.csv','record_id'),('tolerance_samples.csv','sample_id'),('fdtd_validation.csv','record_id'),('provenance_links.csv','record_id'),('split_assignments.csv','record_id')]:
 rows=list(csv.DictReader(open(db/fn,encoding='utf-8'))); vals=[r[key] for r in rows]; uni[fn]=len(vals)==len(set(vals))
print(json.dumps({'files':len(files),'heavy':heavy,'nan_inf_hits':bad[:5],'unique_keys':uni,'split_audit':json.load(open(db/'split_audit.json')),'quality':json.load(open(db/'quality_audit.json'))},indent=2))
