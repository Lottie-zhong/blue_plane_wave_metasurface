from pathlib import Path
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
CONFIG_DIR = ROOT / "configs"
OUT_DIR = ROOT / "outputs/stage10a_h300_p2_local"

x_cfg = {
    "project": {
        "name": "blue_plane_wave_metasurface",
        "stage": "stage10a_h300_p2_local_x",
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
        "metasurface": "c-Si",
        "metasurface_index": 3.87,
    },
    "geometry": {
        "period_nm": 340,
        "length_nm": 75,
        "width_nm": 135,
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
        "result_dir": "outputs/stage10a_h300_p2_local/base_x",
    },
}

y_cfg = yaml.safe_load(yaml.safe_dump(x_cfg, sort_keys=False))
y_cfg["project"]["stage"] = "stage10a_h300_p2_local_y"
y_cfg["target"]["incident_polarization"] = "y"
y_cfg["target"]["output_polarization"] = "y"
y_cfg["output"]["result_dir"] = "outputs/stage10a_h300_p2_local/base_y"

sweep_cfg = {
    "project": {
        "name": "blue_plane_wave_metasurface",
        "stage": "stage10a_h300_p2_role_local_lookup",
    },
    "base_configs": {
        "x": "configs/stage10a_h300_p2_local_x.yaml",
        "y": "configs/stage10a_h300_p2_local_y.yaml",
    },
    "sweep": {
        "length_nm": [65, 70, 75, 80, 85, 90],
        "width_nm": [120, 125, 130, 135, 140, 145, 150],
        "height_nm": [300],
        "rotation_deg": [0],
    },
    "output": {
        "result_dir": "outputs/stage10a_h300_p2_local",
    },
}

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

(CONFIG_DIR / "stage10a_h300_p2_local_x.yaml").write_text(
    yaml.safe_dump(x_cfg, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
(CONFIG_DIR / "stage10a_h300_p2_local_y.yaml").write_text(
    yaml.safe_dump(y_cfg, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)
(CONFIG_DIR / "stage10a_h300_p2_local.yaml").write_text(
    yaml.safe_dump(sweep_cfg, sort_keys=False, allow_unicode=True),
    encoding="utf-8",
)

print("written=configs/stage10a_h300_p2_local_x.yaml")
print("written=configs/stage10a_h300_p2_local_y.yaml")
print("written=configs/stage10a_h300_p2_local.yaml")
print("cases=42")
print("simulations_expected=84")
