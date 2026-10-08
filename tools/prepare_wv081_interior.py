"""Prepare a private WV081 panel owner with complete stock A330-300 model references.

No stock cockpit mesh is copied. Generated configuration and native module remain
private under dist and retain their original rights. This never builds or installs.
"""

import argparse
import configparser
import io
import json
import ntpath
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
AIRCRAFT = Path("SimObjects/Airplanes/microsoft-a330")
STOCK = AIRCRAFT / "attachments/inibuilds"
BASE = STOCK / "Function_A330_Interior"
VARIANT = STOCK / "Function_A330-300_Interior"
ATTACHMENT = AIRCRAFT / "attachments/a330wv081community/Function_A330-300_WV081_Interior"
CACHE = ROOT / "dist/cached-stock-inputs"
MODULE = "inibuilds-a330-wv081.wasm"
MODEL = "model/a330-300_wv081_interior.xml"


def read_source(vfs_root, relative):
    cached = CACHE / relative
    for candidate in (cached, ROOT / "dist/cached-cockpit-donor" / relative, vfs_root / relative):
        if candidate.exists():
            data = candidate.read_bytes()
            if not data:
                raise ValueError(f"Empty projected or cached input: {relative}")
            if candidate != cached:
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(data)
            return data
    raise FileNotFoundError(f"No readable source or private cached input: {relative}")


def parse_config(data):
    result = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
    result.read_string(data.decode("utf-8-sig"))
    return result


def encode_config(config):
    output = io.StringIO()
    config.write(output)
    return output.getvalue().encode("utf-8")


def combine_attachments(base, variant):
    """Flatten base-first inheritance without loading the stock base panel twice."""
    result = configparser.ConfigParser(interpolation=None)
    result["Version"] = {"major": "1", "minor": "0"}
    counts = {"SIM_ATTACHMENT": 0, "MERGE_MODEL": 0}
    for source in (parse_config(base), parse_config(variant)):
        for section in source.sections():
            kind = section.split(".")[0].upper()
            if kind not in counts:
                raise ValueError(f"Unexpected inherited attachment section: {section}")
            values = dict(source[section])
            if "attachment" in values:
                legacy = values.pop("attachment").strip('"').replace("\\", "/")
                root, separator, model = legacy.partition("/model/")
                if not separator:
                    raise ValueError("Expected a model path in the inherited legacy attachment")
                values["attachment_root"] = f'"{root}"'
                values["attachment_file"] = f'"model/{model}"'
            result[f"{kind}.{counts[kind]}"] = values
            counts[kind] += 1
    if counts != {"SIM_ATTACHMENT": 120, "MERGE_MODEL": 1}:
        raise ValueError(f"Unexpected A330-300 cabin inheritance: {counts}")
    return encode_config(result), counts


def rebase_path(value, old_directory, new_directory):
    target = ntpath.normpath(ntpath.join(str(old_directory), value))
    relative = ntpath.relpath(target, str(new_directory))
    if not target.lower().startswith(str(STOCK).lower() + "\\"):
        raise ValueError(f"Model/texture reference escaped the stock attachment tree: {target}")
    return relative, Path(target)


def prepare(vfs_root, output_root=None):
    from prepare_fuel_module import prepare as prepare_fuel_module

    vfs_root = Path(vfs_root)
    output_root = (Path(output_root) if output_root else ROOT / "dist/fuel-development/wv081-interior").resolve()
    if not output_root.is_relative_to((ROOT / "dist").resolve()) or output_root == (ROOT / "dist").resolve():
        raise ValueError("Private interior output must stay inside this repository's dist directory")

    attachment = parse_config(read_source(vfs_root, VARIANT / "attachment.cfg"))
    inherited = attachment.get("Inherit", "base").strip('"').replace("\\", "/").lower()
    if inherited != BASE.as_posix().lower():
        raise ValueError("Unexpected A330-300 base attachment")
    attachment.remove_section("Inherit")
    cabin, counts = combine_attachments(
        read_source(vfs_root, BASE / "config/attached_objects.cfg"),
        read_source(vfs_root, VARIANT / "config/attached_objects.cfg"),
    )
    model = ET.fromstring(read_source(vfs_root, VARIANT / "model/a330-300_interior.xml"))
    lods = model.findall("./LODS/LOD")
    if len(lods) != 5 or [lod.get("minSize") for lod in lods] != ["100", "50", "15", "5", "1"]:
        raise ValueError("Expected all five stock A330-300 cockpit LODs")
    model_references = []
    for lod in lods:
        relative, target = rebase_path(lod.attrib["ModelFile"], VARIANT / "model", ATTACHMENT / "model")
        metadata = json.loads(read_source(vfs_root, target))
        if not metadata.get("nodes") or not metadata.get("scenes"):
            raise ValueError(f"Empty stock cockpit model: {target}")
        lod.set("ModelFile", relative)
        model_references.append(target.as_posix())
    behaviors = model.find("Behaviors")
    if behaviors is None or behaviors.get("Compiled") != "True":
        raise ValueError("Expected the stock compiled A330-300 behavior reference")
    include = behaviors.find("IncludeBase")
    if include is None:
        raise ValueError("The stock cockpit has no compiled behavior include")
    relative, behavior_path = rebase_path(include.attrib["RelativeFile"], VARIANT / "model", ATTACHMENT / "model")
    read_source(vfs_root, behavior_path)
    include.set("RelativeFile", relative)
    ET.indent(model)

    textures = parse_config(read_source(vfs_root, VARIANT / "texture/texture.cfg"))
    fallbacks = dict(textures["fltsim"])
    if len(fallbacks) != 4 or any(not key.startswith("fallback.") for key in fallbacks):
        raise ValueError("Expected the four stock A330-300 texture fallbacks")
    for key, value in fallbacks.items():
        textures["fltsim"][key] = rebase_path(value, VARIANT / "texture", ATTACHMENT / "texture")[0]

    panel = read_source(vfs_root, BASE / "panel/panel.cfg")
    original_module = b"wasm_module=inibuilds-A330.wasm"
    if panel.count(original_module) != 20:
        raise ValueError("Expected twenty gauges sharing the stock A330 native module")
    updated_panel = panel.replace(original_module, b"wasm_module=" + MODULE.encode())
    original_native = BASE / "panel/inibuilds-a330.wasm"
    read_source(vfs_root, original_native)
    output_attachment = output_root / ATTACHMENT
    module_report = prepare_fuel_module(
        vfs_root, output_attachment / "panel" / MODULE, source_module=CACHE / original_native,
    )
    files = {
        "attachment.cfg": encode_config(attachment),
        "config/attached_objects.cfg": cabin,
        "config/systems.cfg": read_source(vfs_root, VARIANT / "config/systems.cfg"),
        "navigation_graph/navigation_graph_pilot.cfg": read_source(vfs_root, VARIANT / "navigation_graph/navigation_graph_pilot.cfg"),
        MODEL: ET.tostring(model, encoding="utf-8", xml_declaration=True) + b"\n",
        "texture/texture.cfg": encode_config(textures),
        "panel/panel.cfg": updated_panel,
    }
    for relative, data in files.items():
        destination = output_attachment / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    report = {
        "attachment_root": ATTACHMENT.as_posix(), "attachment_file": MODEL,
        "attach_to_model": "interior", "alias": "Interior_A333", "tag": "a330_300_interior",
        "payload_files": len(files) + 1, "stock_model_references": model_references,
        "stock_behavior_reference": behavior_path.as_posix(), "stock_meshes_copied": 0,
        "cabin_contributions": counts, "texture_fallbacks": dict(textures["fltsim"]),
        "native_gauge_references": 20, "native_module": MODULE, "module_preparation": module_report,
        "preserved_exactly": ["config/systems.cfg", "navigation_graph/navigation_graph_pilot.cfg"],
        "package_resources_complete": False,
        "package_resource_requirement": "Native ./data paths are package-relative. Stock fonts, display images and other data must be supplied privately or a supported dependency-resolution route established before a flight trial.",
        "limits": "Private experimental candidate; module relocation, cockpit loading, fuel/CG behavior and displays require simulator validation.",
        "redistribution": "Stock-derived configuration/module: local use only; do not redistribute.",
    }
    (output_root / "wv081-interior-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output_root / "WV081-INTERIOR-LOCAL-ONLY.txt").write_text(
        "LOCAL BUILD ONLY - DO NOT REDISTRIBUTE\n"
        "This tree contains installed stock configuration and a derived native module.\n"
        "Original third-party rights apply; the project license covers only original tool code.\n"
        "No simulator validation is implied by file preparation.\n", encoding="utf-8",
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vfs_root", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    try:
        report = prepare(args.vfs_root, args.output_root)
    except (OSError, ValueError, KeyError, configparser.Error, ET.ParseError) as exc:
        parser.exit(1, f"WV081 interior preparation failed: {exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
