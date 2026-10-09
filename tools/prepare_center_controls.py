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
import struct
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
# The A333 fuel-panel face has no centre-button holes and lies 0.91-0.94 mm in front of the
# aligned donor roots; pressed korry faces sit 1.06 mm behind them. Lift the controls clear.
OUTWARD_OFFSET_M = 0.0023
# CTR, TANK, L, R, XFR and AUTO lettering around the donor buttons, in mm from the XFR root.
# The nearby T TANK MODE/FEED and ISOL legends label controls the A333 already has.
LEGEND_NODE = "INT_DECAL_LIGHTS"
LEGEND_REGION_MM = ((-45.0, 45.0), (-21.0, 12.0))
LEGEND_TRIANGLES = 12
# Donor lettering sits 0.65 mm above its own face; keep that clearance above the higher A333 face.
LEGEND_OFFSET_M = 0.0009
LEGEND_LIGHT = "(L:INI_AC_LIGHTS_FAILURE, Bool) (L:INI_POTENTIOMETER_15, Number) 100 / *"
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


def outward_axis(gltf, vfs_root, model_dir):
    """Unit vector toward the crew, opposite to the donor pushbutton press travel."""
    animation = next(a for a in gltf["animations"] if a.get("name") == "FUEL_CTR_XFR")
    channel = next(c for c in animation["channels"] if c["target"]["path"] == "translation")
    output = animation["samplers"][channel["sampler"]]["output"]
    if gltf["accessors"][output]["componentType"] != 5126 or gltf["accessors"][output]["type"] != "VEC3":
        raise ValueError("Unexpected donor press-animation format")
    values = struct.unpack(f"<{gltf['accessors'][output]['count'] * 3}f", accessor_data(gltf, output, vfs_root, model_dir))
    travel = [values[-3 + i] - values[i] for i in range(3)]
    length = math.hypot(*travel)
    axis = [-component / length for component in travel] if length > 0.001 else [0, 0, 0]
    if axis[1] > -0.5:
        raise ValueError("Donor press travel does not point into the downward-facing overhead panel")
    return axis


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
    # The SDK validator rejects any node without an ID once ASOBO_unique_id is in use.
    nodes.append({
        "name": "WV081_CENTER_CONTROLS_ALIGNMENT", "translation": translation, "children": roots,
        "extensions": {"ASOBO_unique_id": {"id": "x0_WV081_CENTER_CONTROLS_ALIGNMENT"}},
    })
    result = {
        "asset": copy.deepcopy(source["asset"]), "scene": 0, "scenes": [{"nodes": [len(nodes) - 1]}],
        "nodes": nodes, "meshes": meshes, "animations": animations, "materials": materials,
        "textures": textures, "images": images, "accessors": accessors, "bufferViews": views,
        "buffers": [{"uri": "center_controls.bin", "byteLength": len(payload)}],
    }
    return result, payload


def add_legends(result, payload, source, translation, outward, vfs_root, model_dir):
    """Append the donor CTR legend decals, selected by triangle centroid around the XFR button."""
    found = [i for i, node in enumerate(source["nodes"]) if node.get("name") == LEGEND_NODE]
    parents = {child for node in source["nodes"] for child in node.get("children", [])}
    if len(found) != 1 or found[0] in parents:
        raise ValueError("Expected one root donor lettering node")
    donor_node = source["nodes"][found[0]]
    if "matrix" in donor_node or donor_node.get("rotation", [0, 0, 0, 1]) != [0, 0, 0, 1] or "scale" in donor_node:
        raise ValueError("Donor lettering node needs a full transform; refusing an approximate placement")
    primitives = source["meshes"][donor_node["mesh"]]["primitives"]
    if len(primitives) != 1 or "targets" in primitives[0] or "extensions" in primitives[0]:
        raise ValueError("Unexpected donor lettering primitive")
    primitive = primitives[0]
    unpack = lambda index, fmt: struct.unpack(f"<{len(accessor_data(source, index, vfs_root, model_dir)) // struct.calcsize(fmt)}{fmt}",
                                              accessor_data(source, index, vfs_root, model_dir))
    index_format = {5123: "H", 5125: "I"}[source["accessors"][primitive["indices"]]["componentType"]]
    indices = unpack(primitive["indices"], index_format)
    if source["accessors"][primitive["attributes"]["POSITION"]]["componentType"] != 5126:
        raise ValueError("Unexpected donor lettering position format")
    flat = unpack(primitive["attributes"]["POSITION"], "f")
    positions = [flat[i:i + 3] for i in range(0, len(flat), 3)]
    root = world_translation(source, "FUEL_CTR_XFR")
    up_length = math.hypot(outward[1], outward[2])
    up = [0.0, outward[2] / up_length, -outward[1] / up_length]
    (x_low, x_high), (v_low, v_high) = LEGEND_REGION_MM
    selected = []
    for t in range(len(indices) // 3):
        triangle = indices[3 * t:3 * t + 3]
        centroid = [donor_node["translation"][k] + sum(positions[v][k] for v in triangle) / 3 - root[k] for k in range(3)]
        lateral, vertical = centroid[0] * 1000, sum(c * u for c, u in zip(centroid, up)) * 1000
        if x_low < lateral < x_high and v_low < vertical < v_high:
            selected.append(triangle)
    if len(selected) != LEGEND_TRIANGLES:
        raise ValueError(f"Expected {LEGEND_TRIANGLES} donor CTR legend triangles, found {len(selected)}")
    vertices = sorted({v for triangle in selected for v in triangle})
    remap = {old: new for new, old in enumerate(vertices)}

    def append(data, target, template):
        payload.extend(b"\0" * (-len(payload) % 4))
        result["bufferViews"].append({"buffer": 0, "byteOffset": len(payload), "byteLength": len(data), "target": target})
        payload.extend(data)
        accessor = {key: value for key, value in template.items() if key not in ("min", "max", "sparse", "byteOffset")}
        accessor["bufferView"] = len(result["bufferViews"]) - 1
        result["accessors"].append(accessor)
        return len(result["accessors"]) - 1, accessor

    attributes = {}
    for name, index in primitive["attributes"].items():
        template = source["accessors"][index]
        packed = accessor_data(source, index, vfs_root, model_dir)
        item = len(packed) // template["count"]
        data = b"".join(packed[v * item:(v + 1) * item] for v in vertices)
        attributes[name], accessor = append(data, 34962, dict(template, count=len(vertices)))
        if name == "POSITION":
            accessor["min"] = [min(positions[v][k] for v in vertices) for k in range(3)]
            accessor["max"] = [max(positions[v][k] for v in vertices) for k in range(3)]
    index_data = struct.pack(f"<{len(selected) * 3}H", *(remap[v] for triangle in selected for v in triangle))
    index_accessor, _ = append(index_data, 34963, {"componentType": 5123, "count": len(selected) * 3, "type": "SCALAR"})
    material = copy.deepcopy(source["materials"][primitive["material"]])
    texture_map = {}
    for old in sorted(set(texture_indices(material))):
        texture = copy.deepcopy(source["textures"][old])
        if "sampler" in texture or "extensions" in texture:
            raise ValueError("Donor lettering texture needs an unsupported sampler or extension")
        image = copy.deepcopy(source["images"][texture["source"]])
        image["uri"] = PureWindowsPath(image["uri"]).name.lower()
        result["images"].append(image)
        texture["source"] = len(result["images"]) - 1
        result["textures"].append(texture)
        texture_map[old] = len(result["textures"]) - 1
    remap_textures(material, texture_map)
    result["materials"].append(material)
    result["meshes"].append({"name": "WV081_CTR_LEGENDS", "primitives": [{
        "attributes": attributes, "indices": index_accessor, "material": len(result["materials"]) - 1}]})
    result["nodes"].append({
        "name": "WV081_CTR_LEGENDS", "mesh": len(result["meshes"]) - 1, "translation": donor_node["translation"],
        "extensions": {"ASOBO_unique_id": {"id": "x0_WV081_CTR_LEGENDS"}},
    })
    result["nodes"].append({
        "name": "WV081_CTR_LEGENDS_ALIGNMENT", "translation": translation, "children": [len(result["nodes"]) - 1],
        "extensions": {"ASOBO_unique_id": {"id": "x0_WV081_CTR_LEGENDS_ALIGNMENT"}},
    })
    result["scenes"][0]["nodes"].append(len(result["nodes"]) - 1)
    return len(selected)


def finish_gltf(result, payload):
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
    result["buffers"][0]["byteLength"] = len(payload)
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
        # The donor never drives the upper FAULT face; the controller reports low pump pressure.
        if name != "FUEL_CTR_XFR":
            fault = ET.SubElement(behaviors, "Component", {"ID": "WV081_" + name + "_FAULT", "Node": name + "_SEQ1"})
            emissive = ET.SubElement(fault, "UseTemplate", {"Name": "ASOBO_GT_Material_Emissive_Code"})
            ET.SubElement(emissive, "NODE_ID").text = name + "_SEQ1"
            ET.SubElement(emissive, "EMISSIVE_CODE").text = (
                f"(L:WV081_CTR_{name[-1]}_FAULT, Bool) (L:INI_ANNLT_SWITCH, Number) 0 == or"
                " (L:INI_GENERAL_LIGHT_MULTIPLIER, Number) * (L:INI_AC_LIGHTS_FAILURE, Bool) *"
            )
    # Legends follow the stock overhead lettering's integral-lighting potentiometer.
    legends = ET.SubElement(behaviors, "Component", {"ID": "WV081_CTR_LEGENDS", "Node": "WV081_CTR_LEGENDS"})
    lighting = ET.SubElement(legends, "UseTemplate", {"Name": "ASOBO_GT_Material_Emissive_Code"})
    ET.SubElement(lighting, "NODE_ID").text = "WV081_CTR_LEGENDS"
    ET.SubElement(lighting, "EMISSIVE_CODE").text = LEGEND_LIGHT
    # Runtime evidence that this attachment and its behaviors actually loaded.
    loaded = ET.SubElement(behaviors, "Component", {"ID": "WV081_CENTER_CONTROLS_LOADED"})
    update = ET.SubElement(loaded, "UseTemplate", {"Name": "ASOBO_GT_Update"})
    ET.SubElement(update, "FREQUENCY").text = "1"
    ET.SubElement(update, "UPDATE_CODE").text = "1 (>L:WV081_CTR_CONTROLS_LOADED, Bool)"
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
    outward = outward_axis(donor, vfs_root, donor_dir)
    legend_translation = [t + LEGEND_OFFSET_M * n for t, n in zip(translation, outward)]
    translation = [t + OUTWARD_OFFSET_M * n for t, n in zip(translation, outward)]
    mesh, payload = subset_mesh(donor, translation, vfs_root, donor_dir)
    legend_triangles = add_legends(mesh, payload, donor, legend_translation, outward, vfs_root, donor_dir)
    mesh, payload = finish_gltf(mesh, payload)
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
        "outward_offset_metres": OUTWARD_OFFSET_M, "outward_axis": outward,
        "legend_triangles": legend_triangles, "legend_offset_metres": LEGEND_OFFSET_M,
        "control_variables": CONTROLS, "texture_dependencies": texture_dependencies,
        "scope": "Additive controls and their CTR legends only; no variant flag or existing cockpit replacement.",
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
