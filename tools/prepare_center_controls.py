"""Prepare a private, additive A330-200 center-control mesh for the A330-300.

Read installed, readable assets only. Generated stock-derived files stay in dist;
they are not covered by the project's license and must not be redistributed.
This prepares files only: it does not build, install, or operate the simulator.
"""

import argparse
import copy
import json
import math
from pathlib import Path, PureWindowsPath
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
AIRCRAFT = Path("SimObjects/Airplanes/microsoft-a330")
STOCK = AIRCRAFT / "attachments/inibuilds"
ATTACHMENT = AIRCRAFT / "attachments/a330wv081community/Function_A330_Center_Controls"
CACHE = ROOT / "dist/cached-cockpit-donor"
CONTROLS = {
    "FUEL_CTR_L": "INI_CENTER_TANK_LEFT",
    "FUEL_CTR_R": "INI_CENTER_TANK_RIGHT",
    "FUEL_CTR_XFR": "INI_CENTER_TANK_FUEL_XFR",
}
NOTICE = (
    "LOCAL BUILD ONLY - DO NOT REDISTRIBUTE\n"
    "This attachment contains selected geometry, animations and material metadata\n"
    "from the user's installed Microsoft/iniBuilds A330. Original rights apply.\n"
    "Only the preparation tool and its original declarations use the project license.\n"
    "SDK compilation and in-simulator rendering/interaction remain unverified.\n"
)


def read_source(vfs_root, relative):
    cached = CACHE / relative
    if cached.exists():
        return cached.read_bytes()
    data = (vfs_root / relative).read_bytes()
    if not data:
        raise ValueError(f"Empty projected input: {relative}")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)
    return data


def world_translation(gltf, name):
    """The observed shared overhead anchors have translation-only ancestors."""
    found = [i for i, node in enumerate(gltf["nodes"]) if node.get("name") == name]
    if len(found) != 1:
        raise ValueError(f"Expected one alignment node: {name}")
    parents = {child: i for i, node in enumerate(gltf["nodes"]) for child in node.get("children", [])}
    current = found[0]
    position = list(gltf["nodes"][current].get("translation", [0, 0, 0]))
    while current in parents:
        current = parents[current]
        node = gltf["nodes"][current]
        if "matrix" in node or node.get("rotation", [0, 0, 0, 1]) != [0, 0, 0, 1] or node.get("scale", [1, 1, 1]) != [1, 1, 1]:
            raise ValueError(f"Alignment ancestor of {name} needs a full transform; refusing an approximate placement")
        position = [a + b for a, b in zip(position, node.get("translation", [0, 0, 0]))]
    return position


def accessor_data(gltf, index, vfs_root, model_dir):
    accessor = gltf["accessors"][index]
    if "sparse" in accessor or accessor["type"] not in ("SCALAR", "VEC2", "VEC3", "VEC4"):
        raise ValueError(f"Unsupported selected accessor: {index}")
    view = gltf["bufferViews"][accessor["bufferView"]]
    width = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[accessor["componentType"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    item_size = width * components
    stride = view.get("byteStride", item_size)
    count = accessor["count"]
    offset = accessor.get("byteOffset", 0)
    extent = (count - 1) * stride + item_size
    if count < 1 or stride < item_size or offset + extent > view["byteLength"]:
        raise ValueError(f"Selected accessor exceeds its source view: {index}")
    cached = CACHE / "selected-center-accessors" / f"{index}.bin"
    if cached.exists():
        packed = cached.read_bytes()
    else:
        buffer = gltf["buffers"][view["buffer"]]
        source = model_dir / buffer["uri"]
        if Path(buffer["uri"]).name != buffer["uri"]:
            raise ValueError("Expected a local stock mesh buffer")
        start = view.get("byteOffset", 0) + offset
        if start + extent > buffer["byteLength"]:
            raise ValueError(f"Selected accessor exceeds the source buffer: {index}")
        with (vfs_root / source).open("rb") as stream:
            stream.seek(start)
            data = stream.read(extent)
        if len(data) != extent:
            raise ValueError(f"Incomplete projected mesh buffer: {source}")
        packed = b"".join(data[i * stride:i * stride + item_size] for i in range(count))
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(packed)
    if len(packed) != count * item_size:
        raise ValueError(f"Incomplete cached accessor: {index}")
    return packed


def texture_indices(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "index":
                yield child
            else:
                yield from texture_indices(child)
    elif isinstance(value, list):
        for child in value:
            yield from texture_indices(child)


def remap_textures(value, mapping):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "index":
                value[key] = mapping[child]
            else:
                remap_textures(child, mapping)
    elif isinstance(value, list):
        for child in value:
            remap_textures(child, mapping)


def subset_mesh(source, translation, vfs_root, model_dir):
    selected = [i for i, node in enumerate(source["nodes"]) if node.get("name") in {
        name + suffix for name in CONTROLS for suffix in ("", "_SEQ1", "_SEQ2")
    }]
    if len(selected) != 9:
        raise ValueError("Expected exactly three donor center controls with two indicator faces each")
    node_map = {old: new for new, old in enumerate(selected)}
    mesh_ids = sorted({source["nodes"][i]["mesh"] for i in selected})
    mesh_map = {old: new for new, old in enumerate(mesh_ids)}
    nodes = [copy.deepcopy(source["nodes"][i]) for i in selected]
    for node in nodes:
        if "skin" in node:
            raise ValueError("Selected donor control unexpectedly requires a skin")
        node["mesh"] = mesh_map[node["mesh"]]
        if "children" in node:
            node["children"] = [node_map[i] for i in node["children"]]
    animations = [copy.deepcopy(a) for a in source["animations"] if a.get("name") in CONTROLS]
    if len(animations) != 3:
        raise ValueError("Expected three donor button animations")
    meshes = [copy.deepcopy(source["meshes"][i]) for i in mesh_ids]
    accessor_ids = set()
    material_ids = set()
    for mesh in meshes:
        for primitive in mesh["primitives"]:
            if "targets" in primitive or "extensions" in primitive:
                raise ValueError("Selected primitive needs an unsupported mesh extension or morph target")
            accessor_ids.update(primitive["attributes"].values())
            accessor_ids.add(primitive["indices"])
            material_ids.add(primitive["material"])
    for animation in animations:
        for channel in animation["channels"]:
            channel["target"]["node"] = node_map[channel["target"]["node"]]
        for sampler in animation["samplers"]:
            accessor_ids.update((sampler["input"], sampler["output"]))
    accessor_map = {old: new for new, old in enumerate(sorted(accessor_ids))}
    material_map = {old: new for new, old in enumerate(sorted(material_ids))}
    materials = [copy.deepcopy(source["materials"][i]) for i in sorted(material_ids)]
    texture_ids = sorted(set(texture_indices(materials)))
    texture_map = {old: new for new, old in enumerate(texture_ids)}
    textures = [copy.deepcopy(source["textures"][i]) for i in texture_ids]
    image_ids = sorted({t["source"] for t in textures})
    image_map = {old: new for new, old in enumerate(image_ids)}
    images = [copy.deepcopy(source["images"][i]) for i in image_ids]
    for texture in textures:
        if "sampler" in texture or "extensions" in texture:
            raise ValueError("Selected texture needs an unsupported sampler or extension")
        texture["source"] = image_map[texture["source"]]
    for image in images:
        image["uri"] = PureWindowsPath(image["uri"]).name.lower()
    remap_textures(materials, texture_map)
    for mesh in meshes:
        for primitive in mesh["primitives"]:
            primitive["attributes"] = {key: accessor_map[value] for key, value in primitive["attributes"].items()}
            primitive["indices"] = accessor_map[primitive["indices"]]
            primitive["material"] = material_map[primitive["material"]]
    for animation in animations:
        for sampler in animation["samplers"]:
            sampler["input"] = accessor_map[sampler["input"]]
            sampler["output"] = accessor_map[sampler["output"]]
    payload = bytearray()
    accessors, views = [], []
    for old in sorted(accessor_ids):
        accessor = copy.deepcopy(source["accessors"][old])
        original_view = source["bufferViews"][accessor["bufferView"]]
        packed = accessor_data(source, old, vfs_root, model_dir)
        payload.extend(b"\0" * (-len(payload) % 4))
        view = {"buffer": 0, "byteOffset": len(payload), "byteLength": len(packed)}
        if "target" in original_view:
            view["target"] = original_view["target"]
        accessor["bufferView"] = len(views)
        accessor["byteOffset"] = 0
        views.append(view)
        accessors.append(accessor)
        payload.extend(packed)
    roots = [i for i, node in enumerate(nodes) if node["name"] in CONTROLS]
    nodes.append({"name": "WV081_CENTER_CONTROLS_ALIGNMENT", "translation": translation, "children": roots})
    result = {
        "asset": copy.deepcopy(source["asset"]), "scene": 0, "scenes": [{"nodes": [len(nodes) - 1]}],
        "nodes": nodes, "meshes": meshes, "animations": animations, "materials": materials,
        "textures": textures, "images": images, "accessors": accessors, "bufferViews": views,
        "buffers": [{"uri": "center_controls.bin", "byteLength": len(payload)}],
    }
    extensions = set()

    def collect_extensions(value):
        if isinstance(value, dict):
            extensions.update(value.get("extensions", {}))
            for child in value.values():
                collect_extensions(child)
        elif isinstance(value, list):
            for child in value:
                collect_extensions(child)

    collect_extensions(result)
    result["extensionsUsed"] = sorted(extensions)
    return result, bytes(payload)


def model_xml():
    model = ET.Element("ModelInfo", {"guid": "{7ea4775f-f424-48dc-bd06-b879146c7e11}", "version": "1.1"})
    ET.SubElement(ET.SubElement(model, "LODS"), "LOD", {"minSize": "0", "ModelFile": "center_controls.gltf"})
    behaviors = ET.SubElement(model, "Behaviors", {"version": "1"})
    ET.SubElement(behaviors, "Include", {"ModelBehaviorFile": r"Asobo\Generic.xml"})
    for name, variable in CONTROLS.items():
        component = ET.SubElement(behaviors, "Component", {"ID": "WV081_" + name, "Node": name})
        interaction = ET.SubElement(component, "UseTemplate", {"Name": "ASOBO_GT_Interaction_LeftSingle_Code"})
        ET.SubElement(interaction, "NODE_ID").text = name
        ET.SubElement(interaction, "LEFT_SINGLE_CODE").text = f"(L:{variable}, Bool) ! (>L:{variable}, Bool)"
        animation = ET.SubElement(component, "UseTemplate", {"Name": "ASOBO_GT_Anim_Code"})
        for key, value in {"ANIM_NAME": name, "ANIM_CODE": f"(L:{variable}, Bool) 100 *", "ANIM_LENGTH": "100", "ANIM_LAG": "400"}.items():
            ET.SubElement(animation, key).text = value
        indicator = ET.SubElement(behaviors, "Component", {"ID": "WV081_" + name + "_INDICATOR", "Node": name + "_SEQ2"})
        emissive = ET.SubElement(indicator, "UseTemplate", {"Name": "ASOBO_GT_Material_Emissive_Code"})
        ET.SubElement(emissive, "NODE_ID").text = name + "_SEQ2"
        state = f"(L:{variable}, Bool)" + (" !" if name != "FUEL_CTR_XFR" else "")
        ET.SubElement(emissive, "EMISSIVE_CODE").text = (
            state + " (L:INI_ANNLT_SWITCH, Number) 0 == or"
            " (L:INI_GENERAL_LIGHT_MULTIPLIER, Number) * (L:INI_AC_LIGHTS_FAILURE, Bool) *"
        )
    ET.indent(model)
    return ET.tostring(model, encoding="utf-8", xml_declaration=True) + b"\n"


def prepare(vfs_root, output_root=None):
    """Return a report and write only this attachment below the chosen dist root."""
    vfs_root = Path(vfs_root)
    output_root = Path(output_root) if output_root else ROOT / "dist/fuel-development"
    output_root = output_root.resolve()
    if not output_root.is_relative_to((ROOT / "dist").resolve()) or output_root == (ROOT / "dist").resolve():
        raise ValueError("Private donor output must be inside this repository's dist directory")
    donor_dir = STOCK / "part_a330-200_cockpit/model"
    donor = json.loads(read_source(vfs_root, donor_dir / "a330-200_cockpit_lod00.gltf"))
    recipient = json.loads(read_source(vfs_root, STOCK / "part_a330-300_cockpit/model/a330-300_cockpit_lod00.gltf"))
    donor_anchor = world_translation(donor, "FUEL_XFEED")
    target_anchor = world_translation(recipient, "FUEL_XFEED")
    translation = [target - original for target, original in zip(target_anchor, donor_anchor)]
    residuals = {}
    for name in ("FUEL_ENG1_L1", "FUEL_ENG2_R2"):
        original, target = world_translation(donor, name), world_translation(recipient, name)
        residuals[name] = math.dist([a + b for a, b in zip(original, translation)], target)
    if max(residuals.values()) > 0.002:
        raise ValueError("Shared overhead controls disagree by more than 2 mm after alignment")
    mesh, payload = subset_mesh(donor, translation, vfs_root, donor_dir)
    texture_dependencies = []
    for image in mesh["images"]:
        relative = STOCK / "asset_a330_common/texture.cockpit" / (image["uri"] + ".ktx2")
        # Keep the installed converted resources offline, but resolve them through stock fallback in the package.
        read_source(vfs_root, relative)
        read_source(vfs_root, Path(str(relative) + ".json"))
        texture_dependencies.append(str(relative).replace("\\", "/"))
    attachment = output_root / ATTACHMENT
    files = {
        "attachment.cfg": b'[Version]\nmajor = 1\nminor = 0\n\n[Tags]\ntag.0 = "wv081_center_controls"\n',
        "model/center_controls.xml": model_xml(),
        "model/center_controls.gltf": (json.dumps(mesh, separators=(",", ":")) + "\n").encode(),
        "model/center_controls.bin": payload,
        "texture/texture.cfg": b'[fltsim]\nfallback.1 = ..\\..\\..\\inibuilds\\Asset_A330_Common\\texture.cockpit\n',
    }
    for relative, data in files.items():
        path = attachment / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    report = {
        "attachment_root": str(ATTACHMENT).replace("\\", "/"),
        "attachment_file": "model/center_controls.xml", "attach_to_model": "interior",
        "alias": "WV081_Center_Controls", "nodes": len(mesh["nodes"]), "donor_nodes": 9,
        "meshes": len(mesh["meshes"]), "animations": len(mesh["animations"]),
        "materials": len(mesh["materials"]), "accessors": len(mesh["accessors"]), "mesh_bytes": len(payload),
        "alignment_metres": translation, "alignment_residual_metres": residuals,
        "control_variables": CONTROLS, "texture_dependencies": texture_dependencies,
        "scope": "Additive controls only; no fuel writer, variant flag, existing cockpit replacement or ECAM change.",
        "limits": "Unverified SDK/runtime loading. Uses installed converted textures. Direct L-variable click bindings; donor B-event/tooltips and Wwise click triggers are not reproduced.",
        "redistribution": "Private stock-derived output; do not redistribute.",
    }
    (output_root / "center-controls-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output_root / "CENTER-CONTROLS-LOCAL-ONLY.txt").write_text(NOTICE, encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vfs_root", type=Path)
    parser.add_argument("--output-root", type=Path, help="Private output directory within this repository's dist")
    args = parser.parse_args()
    try:
        report = prepare(args.vfs_root, args.output_root)
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        parser.exit(1, f"Center-control preparation failed: {exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
