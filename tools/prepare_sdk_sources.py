"""Prepare private SDK sources from the user's installed A330; never build or install."""

import argparse
import configparser
import io
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
AIRCRAFT = Path("SimObjects/Airplanes/microsoft-a330")
PRESET = Path("presets/a330wv081community/a330-300-rr-baseline")
STOCK_PRESET = Path("presets/inibuilds/a330-300 (rr)")
CFG_FILES = (
    "config/ai.cfg", "config/aircraft.cfg", "config/attached_objects.cfg",
    "config/cameras.cfg", "config/cockpit.cfg", "config/engines.cfg",
    "config/flight_model.cfg", "config/gameplay.cfg", "config/reference_points.cfg",
    "config/systems.cfg", "navigation_graph/navigation_graph_passenger.cfg",
    "navigation_graph/navigation_graph_pilot.cfg",
    "navigation_graph/navigation_graph_preflight.cfg",
)
MERGE_XML_FILES = (
    "sound/sound.xml", "soundai/soundai.xml", "checklist/a330-300_checklist.xml",
)
THUMBNAILS = ("thumbnail.png", "thumbnail_button.png", "thumbnail_side.png")
NOTICE = (
    "LOCAL BUILD ONLY - DO NOT REDISTRIBUTE\n\n"
    "This tree contains configuration read from the user's installed Microsoft/iniBuilds A330.\n"
    "Stock-derived configuration retains its original rights and is not covered by the\n"
    "project's CC BY-NC-SA 4.0 license. That license covers original project contributions only.\n"
    "Keep this prepared source and any SDK output private. Distribute only the original\n"
    "preparation tool, metadata delta, thumbnails, and project documentation.\n"
    "SDK compilation and simulator loading have not been validated by this preparation.\n"
)


def aircraft_config(data):
    parsed = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
    parsed.read_string(data.decode("utf-8-sig"))
    return {section.upper(): dict(parsed[section]) for section in parsed.sections()}


def merge_aircraft(stock, delta):
    merged = aircraft_config(stock)
    if merged.get("GENERAL", {}).get("icao_type_designator", "").strip('"') != "A333":
        raise ValueError("Expected the stock A330-300 RR preset (A333)")
    for section, values in aircraft_config(delta).items():
        merged.setdefault(section, {}).update(values)
    result = configparser.ConfigParser(interpolation=None)
    result.read_dict(merged)
    output = io.StringIO()
    result.write(output)
    return output.getvalue().encode("utf-8")


def prepare(vfs_root):
    stock_root = vfs_root / AIRCRAFT
    delta_root = ROOT / "package" / AIRCRAFT / PRESET
    # Read every projected input before publishing any prepared tree. Placeholder sizes are unreliable.
    stock = {name: (stock_root / STOCK_PRESET / name).read_bytes() for name in CFG_FILES}
    if any(not content.strip() for content in stock.values()):
        raise ValueError("A stock preset configuration is empty; keep VFS Projector active and retry")
    metadata = merge_aircraft(stock["config/aircraft.cfg"], (delta_root / "config/aircraft.cfg").read_bytes())
    merge_xml = {}
    for name in MERGE_XML_FILES:
        source_root = ET.fromstring((stock_root / "common" / name).read_bytes())
        stub = ET.Element(source_root.tag, {**source_root.attrib, "AutoMerge": "1"})
        merge_xml[name] = ET.tostring(stub, encoding="utf-8", xml_declaration=True) + b"\n"
    thumbnails = {name: (delta_root / "thumbnail" / name).read_bytes() for name in THUMBNAILS}

    dist = ROOT / "dist"
    destination = dist / "local-sdk-sources"
    if dist.resolve().parent != ROOT or destination.resolve().parent != dist.resolve():
        raise ValueError("Prepared sources must remain within this repository's dist directory")
    dist.mkdir(exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".local-sdk-sources-", dir=dist))
    prepared_preset = stage / AIRCRAFT / PRESET

    def write(relative, data):
        path = stage / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    for name, content in stock.items():
        write(Path("reference/rr") / name, content)
        write(AIRCRAFT / PRESET / name, metadata if name == "config/aircraft.cfg" else content)
    for name, content in merge_xml.items():
        # The native modular lister omits preset checklist/PNG files; use a separate SDK Copy group.
        base = Path("preset-resources") if name.startswith("checklist/") else AIRCRAFT / PRESET
        write(base / name, content)
    for name, content in thumbnails.items():
        write(Path("preset-resources/thumbnail") / name, content)
    write(Path("legal/LICENSE"), (ROOT / "LICENSE").read_bytes())
    write(Path("legal/LOCAL-ONLY.txt"), NOTICE.encode("utf-8"))

    # Preserve every non-metadata preset contribution exactly, including camera/navigation files.
    for name, content in stock.items():
        if name != "config/aircraft.cfg" and (prepared_preset / name).read_bytes() != content:
            raise ValueError(f"Stock preset contribution changed during preparation: {name}")

    backup = None
    if destination.exists():
        backup = dist / ("previous-local-sdk-sources-" + stage.name.rsplit("-", 1)[-1])
        if backup.exists() or destination.resolve().parent != dist.resolve():
            raise ValueError("Cannot preserve the previous prepared sources safely")
        destination.rename(backup)
        print(f"Previous private sources retained: {backup}")
    try:
        stage.rename(destination)
    except OSError:
        if backup is not None and not destination.exists():
            backup.rename(destination)
        raise
    print(f"Prepared {len(stock)} stock preset CFG files and {len(merge_xml)} XML merge declarations.")
    print(f"Private sources: {destination}")
    print(f"SDK project: {ROOT / 'A330_WV081_Project.xml'}")
    print("No build, install, ZIP, or simulator launch performed. Keep generated sources and SDK output private.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vfs_root", type=Path, help="Active MSFS 2024 VFSProjection directory")
    args = parser.parse_args()
    try:
        prepare(args.vfs_root.resolve())
    except (OSError, ValueError, configparser.Error, ET.ParseError) as exc:
        parser.exit(1, f"Preparation failed: {exc}\nNo new complete source tree was published.\n")


if __name__ == "__main__":
    main()
