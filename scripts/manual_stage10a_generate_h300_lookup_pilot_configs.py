from pathlib import Path
import yaml
import csv
import sys

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
CONFIG_DIR = ROOT / "configs"
OUT_DIR = ROOT / "outputs/stage10a_h300_single_pillar_pilot"

x_cfg = {
    "project": {
        "name": "blue_plane_wave_metasurface",
        "stage": "stage10a_h300_single_pillar_lookup_x",
    },
    "target": {
        "wavelength_nm": 633,
        "incident_wave": "plane_wave",
        "incident_polarization": "x",
        "output_polarization": "x",
        "deflection_angle_deg": 0,
        "target_order": "zero",
    },
    "material": {
        # Keep both name and explicit index.
        # If the runner uses index, this is robust; if it uses material name, this records c-Si intent.
        "metasurface": "c-Si",
        "metasurface_index": 3.87,
    },
    "geometry": {
        "period_nm": 340,
        "length_nm": 115,
        "width_nm": 55,
        "height_nm": 300,
        "rotation_deg": 0,
    },
    "far_field": {
        "projection_direction": "auto",
        "material_index": "auto",
        "far_field_filter": 1,
        "resolution_2d": 1001,
        "resolution_3d": 1001,
        "assume_structure_is_periodic": True,
        "illumination": "Gaussian Spot",
        "override_near_field_mesh": False,
        "near_field_samples_per_wavelength": 4,
    },
    "output": {
        "result_dir": "outputs/stage10a_h300_single_pillar_pilot/base_x",
    },
}

y_cfg = yaml.safe_load(yaml.safe_dump(x_cfg, sort_keys=False))
y_cfg["project"]["stage"] = "stage10a_h300_single_pillar_lookup_y"
y_cfg["target"]["incident_polarization"] = "y"
y_cfg["target"]["output_polarization"] = "y"
y_cfg["output"]["result_dir"] = "outputs/stage10a_h300_single_pillar_pilot/base_y"

sweep_cfg = {
    "project": {
        "name": "blue_plane_wave_metasurface",
        "stage": "stage10a_h300_single_pillar_lookup_pilot",
    },
    "base_configs": {
        "x": "configs/stage10a_h300_single_x.yaml",
        "y": "configs/stage10a_h300_single_y.yaml",
    },
    "sweep": {
        # Pilot set:
        # 75x135 and 115x55 are current h300 dimer anchor pillars.
        # 130x70 and 150x85 are APCD-paper h300 reference pillars.
        "length_nm": [75, 115, 130, 150],
        "width_nm": [55, 70, 85, 135],
        "height_nm": [300],
        "rotation_deg": [0],
    },
    "output": {
        "result_dir": "outputs/stage10a_h300_single_pillar_pilot",
    },
}

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

(CONFIG_DIR / "stage10a_h300_single_x.yaml").write_text(
    yaml.safe_dump(x_cfg, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
(CONFIG_DIR / "stage10a_h300_single_y.yaml").write_text(
    yaml.safe_dump(y_cfg, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
(CONFIG_DIR / "stage10a_h300_lookup_pilot.yaml").write_text(
    yaml.safe_dump(sweep_cfg, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)

print("written=configs/stage10a_h300_single_x.yaml")
print("written=configs/stage10a_h300_single_y.yaml")
print("written=configs/stage10a_h300_lookup_pilot.yaml")
print("")
print("pilot_geometry_count=16")
print("simulations_expected=32")
print("")
print("length_nm,width_nm")
for L in sweep_cfg["sweep"]["length_nm"]:
    for W in sweep_cfg["sweep"]["width_nm"]:
        print(f"{L},{W}")
