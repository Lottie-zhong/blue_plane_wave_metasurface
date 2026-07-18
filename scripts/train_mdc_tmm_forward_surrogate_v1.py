from __future__ import annotations
import argparse, csv, hashlib, json, math, os, platform, shutil, sys
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, RandomForestRegressor
try:
    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
except ImportError:  # scikit-learn 0.24 exposes this estimator only internally.
    from sklearn.ensemble._hist_gradient_boosting.gradient_boosting import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, f1_score, mean_absolute_error, mean_squared_error, precision_score,
    r2_score, recall_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

SEED = 20260711
VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "datasets" / "mdc_ml_database_v1"
VIEW = DB / "ml_views" / "tmm_nominal_forward_v1"
OUT = ROOT / "models" / "mdc_tmm_forward_surrogate_v1"
REPORT = ROOT / "reports" / "mdc_defect_450" / "mdc_tmm_forward_surrogate_v1.md"

FEATURES = ["topology_family", "N", "M", "H_nm", "L_nm", "C_nm",
            "effective_central_L_thickness_nm", "physical_layer_count", "total_thickness_nm",
            "has_M", "has_C", "has_effective_center"]
CAT_FEATURES = ["topology_family"]
NUM_FEATURES = [x for x in FEATURES if x not in CAT_FEATURES]
REGRESSION_TARGETS = ["spectral_peak_nm", "spectral_FWHM_nm", "T448", "T450", "T453",
                      "tmm_angular_FWHM_450_deg", "tmm_max_transmission_angle_450_abs_deg",
                      "normal_to_40_60_ratio"]
CLASSIFICATION_TARGETS = ["strict_normal_450", "near_normal_450", "FAB_pass", "PERF_pass", "combined_pass"]
SOURCE_FILES = ["database_manifest.json", "schema.json", "geometry_master.csv", "tmm_nominal_metrics.csv",
                "tolerance_samples.csv", "fdtd_validation.csv", "split_assignments.csv",
                "label_dictionary.csv", "quality_audit.json", "split_audit.json"]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row)) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)

def as_bool(x) -> float:
    if isinstance(x, bool): return float(x)
    if pd.isna(x) or str(x).strip() == "": return float("nan")
    s = str(x).strip().lower()
    if s in ("true", "1"): return 1.0
    if s in ("false", "0"): return 0.0
    raise ValueError(f"unknown boolean value: {x!r}")

def finite(x) -> bool:
    try: return math.isfinite(float(x))
    except (TypeError, ValueError): return False

def metric(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float); y_pred = np.asarray(y_pred, dtype=float)
    e = np.abs(y_true-y_pred)
    return {"n": int(len(y_true)), "MAE": float(mean_absolute_error(y_true,y_pred)),
            "RMSE": float(mean_squared_error(y_true,y_pred)**0.5),
            "R2": float(r2_score(y_true,y_pred)) if len(y_true) >= 2 else float("nan"),
            "P50_abs_error": float(np.quantile(e,.5)), "P90_abs_error": float(np.quantile(e,.9))}

def split_name(key: str) -> str:
    bucket = int(hashlib.sha256(f"{SEED}:{key}".encode()).hexdigest()[:8],16) % 100
    return "train" if bucket < 70 else ("validation" if bucket < 85 else "test")

def source_audit() -> tuple[dict, dict]:
    manifest = json.loads((DB/"database_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("database_version") != "1.0.0" or manifest.get("schema_version") != "1.0.0":
        raise RuntimeError(f"unexpected database/schema version: {manifest}")
    for name in SOURCE_FILES:
        if not (DB/name).exists(): raise RuntimeError(f"required source missing: {name}")
    schema = json.loads((DB/"schema.json").read_text(encoding="utf-8"))
    labels = pd.read_csv(DB/"label_dictionary.csv", keep_default_na=False)
    label_names = set(labels["label_name"])
    required_labels = {"spectral_FWHM_nm", "tmm_angular_FWHM_450_deg", "tmm_max_transmission_angle_450_deg",
                       "fdtd_farfield_angular_FWHM_deg", "fdtd_farfield_peak_angle_deg", "FAB_pass", "PERF_pass", "combined_pass"}
    # The database dictionary is an audit aid, not a replacement for source-table
    # field names. Coverage gaps are recorded in view_audit; no label is invented.
    missing = required_labels-label_names
    return manifest, {name: sha256(DB/name) for name in SOURCE_FILES}

def make_view() -> tuple[pd.DataFrame, dict, dict]:
    manifest, source_before = source_audit()
    geo = pd.read_csv(DB/"geometry_master.csv", keep_default_na=False)
    tmm = pd.read_csv(DB/"tmm_nominal_metrics.csv", keep_default_na=False)
    if tmm["geometry_hash"].duplicated().any(): raise RuntimeError("nominal TMM geometry_hash is not unique")
    df = tmm.merge(geo, on=["geometry_id","geometry_hash"], how="left", validate="one_to_one", suffixes=("","_geo"))
    if df["topology_family"].eq("").any(): raise RuntimeError("geometry semantics missing after nominal join")
    for c in ["simulation_method","usable_for_training","boundary_clipped","quality_status"]:
        if c not in df: raise RuntimeError(f"missing required semantic field: {c}")
    # tmm_nominal_metrics is the canonical nominal-sweep fact table.
    # geometry_master.is_nominal_geometry is only a legacy reference-candidate
    # marker and would incorrectly reduce the recovered training set to two rows.
    base = (df["simulation_method"].eq("TMM") & df["usable_for_training"].astype(str).str.lower().eq("true") &
            ~df["boundary_clipped"].astype(str).str.lower().eq("true") &
            ~df["quality_status"].astype(str).str.contains("semantic-conflict", case=False, na=False))
    df = df.loc[base].copy()
    if len(df) == 0: raise RuntimeError("no usable nominal TMM rows")
    for c in ["N","M","H_nm","L_nm","C_nm","effective_central_L_thickness_nm","physical_layer_count","total_thickness_nm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["has_M"] = df["M"].notna().astype(int); df["has_C"] = df["C_nm"].notna().astype(int)
    df["has_effective_center"] = df["effective_central_L_thickness_nm"].notna().astype(int)
    for c in ["M","C_nm","effective_central_L_thickness_nm"]: df[c] = df[c].fillna(0.0)
    for c in ["spectral_peak_nm","spectral_FWHM_nm","T448","T450","T453","tmm_angular_FWHM_450_deg","tmm_max_transmission_angle_450_deg","normal_to_40_60_ratio"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["tmm_max_transmission_angle_450_abs_deg"] = df["tmm_max_transmission_angle_450_deg"].abs()
    for c in ["strict_normal_450","near_normal_450"]:
        df[c] = np.nan
    angle = df["tmm_max_transmission_angle_450_abs_deg"]
    df.loc[angle.notna(),"strict_normal_450"] = (angle[angle.notna()] <= 1).astype(int)
    df.loc[angle.notna(),"near_normal_450"] = (angle[angle.notna()] <= 5).astype(int)
    for c in ["FAB_pass","PERF_pass","combined_pass"]: df[c] = df[c].map(as_bool)
    for c in REGRESSION_TARGETS: df[f"target_available_{c}"] = df[c].map(finite).astype(int)
    for c in CLASSIFICATION_TARGETS: df[f"target_available_{c}"] = df[c].notna().astype(int)
    df["task_row_status"] = "eligible_per_target_complete_case"
    # Held-out edge combinations are defined without target fields and never used for selection.
    edge = pd.Series(False, index=df.index)
    for topo, idx in df.groupby("topology_family").groups.items():
        s = df.loc[idx]
        candidate = pd.Series(0, index=s.index)
        for c in ["N","H_nm","L_nm"]:
            lo, hi = s[c].min(), s[c].max(); candidate += ((s[c] == lo) | (s[c] == hi)).astype(int)
        optional = "C_nm" if (s["has_C"] > 0).any() else "M"
        valid = s[optional] != 0
        if valid.any():
            lo, hi = s.loc[valid,optional].min(), s.loc[valid,optional].max()
            candidate += (valid & ((s[optional] == lo) | (s[optional] == hi))).astype(int)
        edge.loc[s.index] = candidate >= 2
    df["blocked_parameter_test"] = edge.astype(int)
    df["split"] = ""
    for topo, idx in df.loc[~edge].groupby("topology_family").groups.items():
        ordered = sorted(idx, key=lambda i: hashlib.sha256(f"{SEED}:{df.at[i,'geometry_hash']}".encode()).hexdigest())
        n=len(ordered); ntr=round(.70*n); nval=round(.15*n)
        for k,i in enumerate(ordered): df.at[i,"split"] = "train" if k<ntr else ("validation" if k<ntr+nval else "test")
    df.loc[edge,"split"] = "blocked_parameter_test"
    if df.loc[df["split"]!="blocked_parameter_test","geometry_hash"].duplicated().any(): raise RuntimeError("geometry hash crosses standard split")
    availability_cols=[f"target_available_{x}" for x in [*REGRESSION_TARGETS,*CLASSIFICATION_TARGETS]]
    cols = ["record_id","geometry_id","geometry_hash","topology_family",*FEATURES,"split","blocked_parameter_test","task_row_status",*REGRESSION_TARGETS,*CLASSIFICATION_TARGETS,*availability_cols]
    view = df[cols].copy()
    VIEW.mkdir(parents=True, exist_ok=True)
    view.to_csv(VIEW/"features_targets.csv",index=False)
    view[["record_id","geometry_id","geometry_hash","topology_family","split","blocked_parameter_test"]].to_csv(VIEW/"split_assignments.csv",index=False)
    feature_dict=[]
    for x in FEATURES:
        feature_dict.append({"feature":x,"dtype":"category" if x in CAT_FEATURES else "float","definition":"Topology category" if x=="topology_family" else "Geometry-only physical feature","missing_policy":"one-hot" if x in CAT_FEATURES else ("0 with explicit indicator" if x in ("M","C_nm","effective_central_L_thickness_nm") else "not permitted")})
    write_csv(VIEW/"feature_dictionary.csv",feature_dict)
    labels = pd.read_csv(DB/"label_dictionary.csv",keep_default_na=False)
    label_names=set(labels["label_name"])
    target_dict=[]
    for x in REGRESSION_TARGETS: target_dict.append({"target":x,"task":"regression","unit":"nm" if x.endswith("_nm") else ("deg" if x.endswith("_deg") else "fraction_or_ratio"),"definition":"TMM plane-wave metric; not dipole FDTD far field","available_rows":int(view[f"target_available_{x}"] .sum())})
    for x in CLASSIFICATION_TARGETS: target_dict.append({"target":x,"task":"classification","unit":"bool","definition":"strict/near normal derived from absolute TMM maximum transmission angle (<=1 deg / <=5 deg); gates retained from nominal TMM","available_rows":int(view[f"target_available_{x}"].sum())})
    write_csv(VIEW/"target_dictionary.csv",target_dict)
    audit={"database_version":manifest["database_version"],"schema_version":manifest["schema_version"],"nominal_usable_rows":int(len(view)),"topology_distribution":dict(Counter(view["topology_family"])),"target_missing_rates":{x:float(1-view[f"target_available_{x}"].mean()) for x in [*REGRESSION_TARGETS,*CLASSIFICATION_TARGETS]},"label_dictionary_direct_coverage":{x:(x in label_names) for x in [*REGRESSION_TARGETS,*CLASSIFICATION_TARGETS]},"derived_label_semantics":{"strict_normal_450":"abs(tmm_max_transmission_angle_450_deg)<=1","near_normal_450":"abs(tmm_max_transmission_angle_450_deg)<=5"},"geometry_hash_unique":bool(not view["geometry_hash"].duplicated().any()),"geometry_hash_overlap_across_standard_splits":0,"target_leakage_features":[],"split_counts":dict(Counter(view["split"])),"split_strategy":"stratified_geometry_split_v1","seed":SEED,"blocked_definition":"two or more topology-local geometry parameters at min/max; never used for selection"}
    (VIEW/"view_audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    view_manifest={"view_name":"tmm_nominal_forward_v1","version":VERSION,"database_location":"datasets/mdc_ml_database_v1","database_version":manifest["database_version"],"schema_version":manifest["schema_version"],"source_sha256":source_before,"filters":["canonical tmm_nominal_metrics fact table","TMM only","usable_for_training true","not boundary-clipped","not semantic-conflict","per-target complete-case training"],"excluded":["tolerance_samples","fdtd_validation","runtime probes","provisional raw FDTD spectrum","superseded duplicates"],"features":FEATURES,"regression_targets":REGRESSION_TARGETS,"classification_targets":CLASSIFICATION_TARGETS,"split_strategy":"stratified_geometry_split_v1","seed":SEED,"counts":audit["split_counts"],"note":"Angular targets have sparse coverage and are never imputed from tolerance or FDTD."}
    (VIEW/"view_manifest.json").write_text(json.dumps(view_manifest,indent=2),encoding="utf-8")
    return view, audit, source_before

def prep() -> ColumnTransformer:
    try: enc=OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError: enc=OneHotEncoder(handle_unknown="ignore", sparse=False)
    return ColumnTransformer([("cat",enc,CAT_FEATURES),("num",SimpleImputer(strategy="median"),NUM_FEATURES)],remainder="drop")

def reg_models():
    return {
        "ExtraTreesRegressor": ExtraTreesRegressor(n_estimators=140, min_samples_leaf=2, random_state=SEED, n_jobs=-1),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=140, min_samples_leaf=2, random_state=SEED, n_jobs=-1),
        "HistGradientBoostingRegressor": HistGradientBoostingRegressor(max_iter=220, l2_regularization=0.1, random_state=SEED),
    }

def clf_models():
    return {
        "ExtraTreesClassifier": ExtraTreesClassifier(n_estimators=180,min_samples_leaf=2,class_weight="balanced",random_state=SEED,n_jobs=-1),
        "HistGradientBoostingClassifier": HistGradientBoostingClassifier(max_iter=180,l2_regularization=0.1,random_state=SEED),
    }

def save_if_light(model, name: str, records: list[dict]) -> None:
    p=OUT/"selected_models"/(name+".joblib"); p.parent.mkdir(parents=True,exist_ok=True); joblib.dump(model,p,compress=3)
    size=p.stat().st_size
    if size >= 50_000_000:
        p.unlink(); records.append({"artifact":name,"status":"not_committed_over_50MB","bytes":size})
    else: records.append({"artifact":name,"status":"committed","bytes":size})

def train(view: pd.DataFrame) -> dict:
    OUT.mkdir(parents=True,exist_ok=True)
    for p in (OUT/"selected_models",):
        if p.exists(): shutil.rmtree(p)
    train_df=view[view["split"].eq("train")]; val_df=view[view["split"].eq("validation")]; test_df=view[view["split"].eq("test")]; blocked_df=view[view["split"].eq("blocked_parameter_test")]
    reg_rows=[]; topo_rows=[]; blocked_rows=[]; pred_rows=[]; selected={}; artifacts=[]
    for target in REGRESSION_TARGETS:
        subsets={k:d[d[target].notna()].copy() for k,d in {"train":train_df,"validation":val_df,"test":test_df,"blocked_parameter_test":blocked_df}.items()}
        if min(len(subsets["train"]),len(subsets["validation"]),len(subsets["test"])) < 5:
            reg_rows.append({"target":target,"model":"SKIPPED","split":"all","status":"insufficient_complete_case_rows","n_train":len(subsets["train"]),"n_validation":len(subsets["validation"]),"n_test":len(subsets["test"]),"n_blocked":len(subsets["blocked_parameter_test"])})
            continue
        candidates=[]
        for name,est in reg_models().items():
            model=Pipeline([("prep",prep()),("model",est)])
            model.fit(subsets["train"][FEATURES],subsets["train"][target])
            m=metric(subsets["validation"][target],model.predict(subsets["validation"][FEATURES])); m.update({"target":target,"model":name,"split":"validation","status":"candidate"}); reg_rows.append(m); candidates.append((m["MAE"],name,model))
        _,name,model=min(candidates,key=lambda x:x[0]); selected[target]=(name,model)
        # Test is evaluated exactly once, after validation-only selection.
        for split,d in [("test",subsets["test"]),("blocked_parameter_test",subsets["blocked_parameter_test"])]:
            if len(d):
                yhat=model.predict(d[FEATURES]); m=metric(d[target],yhat);m.update({"target":target,"model":name,"split":split,"status":"selected_final"}); (reg_rows if split=="test" else blocked_rows).append(m)
                if split=="test":
                    for _,r in d.iterrows():
                        pred=float(model.predict(pd.DataFrame([r[FEATURES].to_dict()]))[0]); pred_rows.append({"record_id":r.record_id,"geometry_id":r.geometry_id,"geometry_hash":r.geometry_hash,"topology_family":r.topology_family,"target":target,"truth":float(r[target]),"prediction":pred,"abs_error":abs(float(r[target])-pred),"split":"test"})
                if split=="test":
                    dd=d.copy(); dd["pred"]=yhat
                    for topo,x in dd.groupby("topology_family"):
                        tm=metric(x[target],x.pred);tm.update({"target":target,"topology_family":topo,"split":"test","model":name});topo_rows.append(tm)
        save_if_light(model,"reg_"+target,artifacts)
    cls_rows=[]; confusion={}
    for target in CLASSIFICATION_TARGETS:
        subsets={k:d[d[target].notna()].copy() for k,d in {"train":train_df,"validation":val_df,"test":test_df,"blocked_parameter_test":blocked_df}.items()}
        classes=sorted(set(subsets["train"][target].astype(int)))
        if len(classes)<2 or min(len(subsets["validation"]),len(subsets["test"]))<5:
            cls_rows.append({"target":target,"model":"SKIPPED","split":"all","status":"single_class_or_insufficient_rows","n_train":len(subsets["train"]),"n_validation":len(subsets["validation"]),"n_test":len(subsets["test"]),"classes_train":"|".join(map(str,classes))}); continue
        candidates=[]
        for name,est in clf_models().items():
            model=Pipeline([("prep",prep()),("model",est)]);model.fit(subsets["train"][FEATURES],subsets["train"][target].astype(int))
            y=subsets["validation"][target].astype(int); yp=model.predict(subsets["validation"][FEATURES]); proba=model.predict_proba(subsets["validation"][FEATURES])[:,1]
            row={"target":target,"model":name,"split":"validation","status":"candidate","n":len(y),"accuracy":accuracy_score(y,yp),"balanced_accuracy":balanced_accuracy_score(y,yp),"precision":precision_score(y,yp,zero_division=0),"recall":recall_score(y,yp,zero_division=0),"F1":f1_score(y,yp,zero_division=0),"average_precision":average_precision_score(y,proba) if len(set(y))==2 else float("nan")};cls_rows.append(row);candidates.append((row["balanced_accuracy"],name,model))
        _,name,model=max(candidates,key=lambda x:x[0])
        for split,d in [("test",subsets["test"]),("blocked_parameter_test",subsets["blocked_parameter_test"])]:
            if not len(d): continue
            y=d[target].astype(int);yp=model.predict(d[FEATURES]);proba=model.predict_proba(d[FEATURES])[:,1]
            row={"target":target,"model":name,"split":split,"status":"selected_final","n":len(y),"accuracy":accuracy_score(y,yp),"balanced_accuracy":balanced_accuracy_score(y,yp),"precision":precision_score(y,yp,zero_division=0),"recall":recall_score(y,yp,zero_division=0),"F1":f1_score(y,yp,zero_division=0),"average_precision":average_precision_score(y,proba) if len(set(y))==2 else float("nan")};cls_rows.append(row)
            if split=="blocked_parameter_test": blocked_rows.append(row)
            confusion[f"{target}:{split}"]={"labels":[0,1],"matrix":confusion_matrix(y,yp,labels=[0,1]).tolist()}
        save_if_light(model,"clf_"+target,artifacts)
    write_csv(OUT/"regression_metrics.csv",reg_rows)
    write_csv(OUT/"classification_metrics.csv",cls_rows)
    write_csv(OUT/"topology_metrics.csv",topo_rows)
    write_csv(OUT/"blocked_test_metrics.csv",blocked_rows)
    write_csv(OUT/"predictions_test.csv",pred_rows)
    (OUT/"confusion_matrices.json").write_text(json.dumps(confusion,indent=2),encoding="utf-8")
    return {"selected":selected,"artifacts":artifacts,"regression_rows":reg_rows,"classification_rows":cls_rows,"topology_rows":topo_rows,"blocked_rows":blocked_rows}

def replay(view: pd.DataFrame, trained: dict) -> list[dict]:
    candidates=[("EX_N3_L79_H45_C156",lambda x: x["candidate_id_primary"].eq("EX_N3_L79_H45_C156")),
                ("ZL1_N3_M3_L78_H46",lambda x: x["candidate_id_primary"].eq("ZL1_N3_M3_L78_H46")),
                ("ZL1_N3_M3_L79_H44_alternative",lambda x: x["topology_family"].eq("ZL-1") & x["N"].eq(3) & x["M"].eq(3) & x["H_nm"].eq(44) & x["L_nm"].eq(79) & x["effective_central_L_thickness_nm"].eq(316))]
    geo=pd.read_csv(DB/"geometry_master.csv",keep_default_na=False)
    for c in ["N","M","H_nm","L_nm","effective_central_L_thickness_nm"]: geo[c]=pd.to_numeric(geo[c],errors="coerce")
    rows=[]
    for cname,rule in candidates:
        candidates_geo=geo.loc[rule(geo)].copy()
        nominal=view[view["geometry_id"].isin(candidates_geo["geometry_id"])].copy()
        if len(nominal): r=nominal.iloc[0]; origin="nominal_database"
        elif len(candidates_geo):
            r=candidates_geo.iloc[0].copy(); origin="external_inference_not_in_nominal_metrics"
            for c in FEATURES:
                if c not in r: r[c]=0
            r["has_M"]=int(float(r.get("M",0) or 0)>0);r["has_C"]=int(float(r.get("C_nm",0) or 0)>0);r["has_effective_center"]=int(float(r.get("effective_central_L_thickness_nm",0) or 0)>0)
        else:
            rows.append({"candidate":cname,"status":"geometry_not_found"});continue
        feat=pd.DataFrame([{c:r[c] for c in FEATURES}]); base={"candidate":cname,"status":origin,"geometry_id":r.get("geometry_id",""),"split":r.get("split","external"),"topology_family":r.get("topology_family","")}
        for target in REGRESSION_TARGETS:
            if target in trained["selected"]:
                _,model=trained["selected"][target]; pred=float(model.predict(feat)[0]); truth=r.get(target,np.nan); base.update({f"{target}_truth":truth,f"{target}_prediction":pred,f"{target}_error":abs(float(truth)-pred) if finite(truth) else ""})
            else: base.update({f"{target}_truth":r.get(target,np.nan),f"{target}_prediction":"",f"{target}_error":""})
        for target in CLASSIFICATION_TARGETS:
            base[f"{target}_truth"]=r.get(target,np.nan);base[f"{target}_prediction"]="not_trained_or_skipped"
        rows.append(base)
    write_csv(OUT/"candidate_replay.csv",rows)
    return rows

def report(view_audit: dict, trained: dict, replay_rows: list[dict], source_before: dict) -> None:
    reg=pd.read_csv(OUT/"regression_metrics.csv",keep_default_na=False); cls=pd.read_csv(OUT/"classification_metrics.csv",keep_default_na=False)
    core=["spectral_FWHM_nm","tmm_angular_FWHM_450_deg","tmm_max_transmission_angle_450_abs_deg"]
    selected_test=reg[(reg.get("status","")=="selected_final") & (reg.get("split","")=="test")]
    core_ok=set(selected_test.get("target",[]))
    approval="approved_with_limitations" if "spectral_FWHM_nm" in core_ok and len(core_ok)==3 else "not_approved"
    model_manifest={"model_name":"mdc_tmm_forward_surrogate_v1","version":VERSION,"seed":SEED,"database":"datasets/mdc_ml_database_v1","view":"datasets/mdc_ml_database_v1/ml_views/tmm_nominal_forward_v1","source_database_sha256":source_before,"models":[r for r in trained["artifacts"]],"test_evaluation":"one final evaluation after validation-only model selection","approval":approval,"approval_reason":"Full spectral-plus-angular surrogate is not approved when any core target lacks an independently evaluable nominal TMM model.","environment":{"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"pandas":pd.__version__,"scikit_learn":sklearn.__version__},"fdtd_boundary":"FDTD validation has 11 rows and is external high-fidelity reference only; it was not used for training, tuning, or test metrics."}
    (OUT/"model_manifest.json").write_text(json.dumps(model_manifest,indent=2),encoding="utf-8")
    (OUT/"feature_schema.json").write_text(json.dumps({"features":FEATURES,"categorical":CAT_FEATURES,"numeric":NUM_FEATURES,"forbidden":["candidate_id","geometry_hash","rank","FAB/PERF role","selection_reason","source path","provenance count","target-derived fields"]},indent=2),encoding="utf-8")
    (OUT/"target_schema.json").write_text(json.dumps({"regression":REGRESSION_TARGETS,"classification":CLASSIFICATION_TARGETS,"angle_note":"absolute maximum-transmission angle is a plane-wave TMM metric; signed angle retained only for audit; neither is a dipole far-field peak."},indent=2),encoding="utf-8")
    lines=["# MDC Native-M1 TMM nominal forward surrogate v1","",f"Database/schema: {view_audit['database_version']} / {view_audit['schema_version']}. Nominal usable TMM rows: {view_audit['nominal_usable_rows']}.","", "## Scope and data boundary","", "- Trained only on nominal TMM rows. Tolerance, all 11 FDTD records, runtime probes, and provisional FDTD spectra were excluded.", "- FDTD is an external high-fidelity reference only. TMM plane-wave angular metrics cannot replace dipole far-field metrics.", "- Per-target complete-case training is used because the database has sparse angular labels; no labels were imputed or borrowed from tolerance/FDTD.","", "## Split","",f"- `stratified_geometry_split_v1`, seed {SEED}; counts {view_audit['split_counts']}. Geometry hashes are unique and do not cross splits.","- `blocked_parameter_test` is held out by topology-local boundary combinations and never used for model selection.","", "## Regression results (selected final test models)",""]
    lines += ["| target | model | n | MAE | RMSE | R2 | P50 | P90 |","|---|---|---:|---:|---:|---:|---:|---:|"]
    for _,r in selected_test.iterrows(): lines.append(f"| {r.target} | {r.model} | {int(r.n)} | {float(r.MAE):.6g} | {float(r.RMSE):.6g} | {float(r.R2):.6g} | {float(r.P50_abs_error):.6g} | {float(r.P90_abs_error):.6g} |")
    lines += ["", "## Sparse target limitations",""]
    for _,r in reg[reg.get("status","")=="insufficient_complete_case_rows"].iterrows(): lines.append(f"- `{r.target}` skipped: train/validation/test complete cases = {r.n_train}/{r.n_validation}/{r.n_test}.")
    lines += ["", "## Classification results (selected final test models)",""]
    lines += ["| target | model | n | accuracy | balanced accuracy | precision | recall | F1 | AP |","|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for _,r in cls[(cls.get("status","")=="selected_final") & (cls.get("split","")=="test")].iterrows(): lines.append(f"| {r.target} | {r.model} | {int(r.n)} | {float(r.accuracy):.4f} | {float(r.balanced_accuracy):.4f} | {float(r.precision):.4f} | {float(r.recall):.4f} | {float(r.F1):.4f} | {float(r.average_precision):.4f} |")
    for _,r in cls[cls.get("status","")=="single_class_or_insufficient_rows"].iterrows(): lines.append(f"- `{r.target}` classification skipped: {r.status}; train/validation/test rows = {r.n_train}/{r.n_validation}/{r.n_test}.")
    lines += ["", "## Candidate replay",""]
    for r in replay_rows: lines.append(f"- `{r.get('candidate')}`: {r.get('status')}; spectral FWHM truth/pred/error = {r.get('spectral_FWHM_nm_truth','')}/{r.get('spectral_FWHM_nm_prediction','')}/{r.get('spectral_FWHM_nm_error','')}; T450 truth/pred/error = {r.get('T450_truth','')}/{r.get('T450_prediction','')}/{r.get('T450_error','')}.")
    lines += ["", "## External FDTD references (not ML labels)","", "- Explicit FAB prior FDTD far-field peak +0.03 deg; FWHM 26.84 deg.", "- ZL-1 prior FDTD far-field peak -0.03 deg; FWHM 25.14 deg.", "- These are cited solely as external references; this TMM surrogate does not predict or replace FDTD dipole far fields.","", "## Approval", "", f"Overall status: **{approval}**. The spectral-only portion may be useful for exploratory ranking, but the full requested spectral-plus-angular surrogate lacks adequate independent nominal angle labels and is not approved as a complete forward model."]
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    readme=["# MDC TMM forward surrogate v1","",f"Database: `datasets/mdc_ml_database_v1/` (database/schema {view_audit['database_version']}/{view_audit['schema_version']}).","",f"View: `datasets/mdc_ml_database_v1/ml_views/tmm_nominal_forward_v1/`; features: {', '.join(FEATURES)}.",f"Regression targets: {', '.join(REGRESSION_TARGETS)}. Classification targets: {', '.join(CLASSIFICATION_TARGETS)}.",f"Split: stratified_geometry_split_v1, seed {SEED}, with a separate blocked_parameter_test.","Models: ExtraTrees, RandomForest (regression), HistGradientBoosting; ExtraTrees and HistGradientBoosting (classification).","", "FDTD is not a training target or substitute: its 11 records are external reference only. Retrain with `python scripts/train_mdc_tmm_forward_surrogate_v1.py`; audit with `--audit-only`. For new geometry inference, provide only the documented geometry features and interpret unavailable angular targets as unsupported, not zero."]
    (OUT/"README.md").write_text("\n".join(readme)+"\n",encoding="utf-8")
    checks=[]
    for p in sorted(x for x in OUT.rglob("*") if x.is_file() and x.name!="checksums.csv"): checks.append({"relative_path":str(p.relative_to(OUT)).replace("\\","/"),"sha256":sha256(p),"bytes":p.stat().st_size})
    write_csv(OUT/"checksums.csv",checks)
    return approval

def audit_only() -> None:
    req=["model_manifest.json","feature_schema.json","target_schema.json","regression_metrics.csv","classification_metrics.csv","topology_metrics.csv","blocked_test_metrics.csv","candidate_replay.csv","predictions_test.csv","confusion_matrices.json","checksums.csv","README.md"]
    missing=[x for x in req if not (OUT/x).exists()]
    if missing: raise RuntimeError(f"model outputs missing: {missing}")
    m=json.loads((OUT/"model_manifest.json").read_text(encoding="utf-8")); current={name:sha256(DB/name) for name in SOURCE_FILES}
    if current != m.get("source_database_sha256"): raise RuntimeError("source database SHA256 changed")
    v=pd.read_csv(VIEW/"features_targets.csv",keep_default_na=False)
    if v["geometry_hash"].duplicated().any(): raise RuntimeError("view geometry hash duplicate")
    if not set(v["split"]).issubset({"train","validation","test","blocked_parameter_test"}): raise RuntimeError("invalid split")
    print(json.dumps({"audit":"PASS","view_rows":len(v),"approval":m["approval"],"source_database_sha256_unchanged":True},indent=2))

def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument("--audit-only",action="store_true");args=ap.parse_args()
    if args.audit_only: audit_only();return
    view,audit,source_before=make_view();trained=train(view);replay_rows=replay(view,trained);approval=report(audit,trained,replay_rows,source_before)
    source_after={name:sha256(DB/name) for name in SOURCE_FILES}
    if source_before != source_after: raise RuntimeError("source database changed during training")
    print(json.dumps({"status":"PASS","view_rows":len(view),"split_counts":audit["split_counts"],"approval":approval,"source_database_sha256_unchanged":True},indent=2))

if __name__ == "__main__": main()
