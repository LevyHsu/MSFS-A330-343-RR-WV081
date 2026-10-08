"""Prepare private SDK sources from the user's installed A330; never build or install."""

import argparse
import configparser
import io
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET

from prepare_center_controls import prepare as prepare_center_controls


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
# The stock RR preset has no sound, AI-sound or checklist files and inherits common. Empty preset
# stubs replaced those files (a silent aircraft and blank checklist), so none is generated.
THUMBNAILS = ("thumbnail.png", "thumbnail_button.png", "thumbnail_side.png")
DELTA_CFG_FILES = ("config/aircraft.cfg", "config/flight_model.cfg", "config/attached_objects.cfg")
EFB_HTML = Path("html_ui/Pages/VCockpit/Instruments/ini-efb-a330/ini-efb-a330.html")
EFB_EXTENSION = Path("html_ui/Pages/VCockpit/Instruments/a330-wv081-efb/a330-wv081-efb.js")
WASM_HTML = Path("html_ui/Pages/VCockpit/Instruments/WasmInstrument/WasmInstrument.html")
FUEL_EXTENSION = Path("html_ui/Pages/VCockpit/Instruments/a330-wv081-fuel/a330-wv081-fuel.js")
# The native ECAM digits use this installed A330 font, which is outside html_ui at runtime.
STOCK_ECAM_FONT = Path("data/fonts/inidisplayini-regular.ttf")
ECAM_FONT_CACHE = ROOT / "dist/cached-a330-module-data/0.0.53"
STOCK_EFB_IMPORT = b'<script type="text/html" import-script="/Pages/VCockpit/Instruments/ini-efb-a330/ini-efb-a330.js"></script>'
WV081_EFB_IMPORT = b'<script type="text/html" import-script="/Pages/VCockpit/Instruments/a330-wv081-efb/a330-wv081-efb.js"></script>'
STOCK_WASM_IMPORT = b'<script type="text/html" import-script="/Pages/VCockpit/Instruments/WasmInstrument/WasmInstrument.js"></script>'
WV081_FUEL_IMPORT = b'<script type="text/html" import-script="/Pages/VCockpit/Instruments/a330-wv081-fuel/a330-wv081-fuel.js"></script>'
NOTICE = (
    "LOCAL BUILD ONLY - DO NOT REDISTRIBUTE\n\n"
    "This tree contains configuration, instrument loaders, model data and an ECAM font from the user's installed A330.\n"
    "Stock-derived material retains its original rights and is not covered by the\n"
    "project's CC BY-NC-SA 4.0 license. That license covers original project contributions only.\n"
    "Keep this prepared source and any SDK output private. Distribute only the original\n"
    "preparation tools, original configuration deltas, instrument extensions, thumbnails, and documentation.\n"
    "SDK compilation and simulator loading have not been validated by this preparation.\n"
)


def read_config(data):
    parsed = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
    parsed.read_string(data.decode("utf-8-sig"))
    return {section.upper(): dict(parsed[section]) for section in parsed.sections()}


def merge_config(stock, delta):
    merged = read_config(stock)
    for section, values in read_config(delta).items():
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
    identity = read_config(stock["config/aircraft.cfg"])
    if identity.get("GENERAL", {}).get("icao_type_designator", "").strip('"') != "A333":
        raise ValueError("Expected the stock A330-300 RR preset (A333)")
    if "SIM_ATTACHMENT.3" in read_config(stock["config/attached_objects.cfg"]):
        raise ValueError("Stock attachment slot 3 is occupied; review the centre-control attachment delta")
    overrides = {name: merge_config(stock[name], (delta_root / name).read_bytes()) for name in DELTA_CFG_FILES}
    thumbnails = {name: (delta_root / "thumbnail" / name).read_bytes() for name in THUMBNAILS}
    stock_html = (vfs_root / EFB_HTML).read_bytes()
    if stock_html.count(STOCK_EFB_IMPORT) != 1 or b'id="iniEfbA330"' not in stock_html:
        raise ValueError("Expected the stock A330 EFB loader and template")
    if WV081_EFB_IMPORT in stock_html:
        raise ValueError("The EFB loader already includes this mod; supply the pristine stock loader")
    loader = stock_html.replace(STOCK_EFB_IMPORT, WV081_EFB_IMPORT + b"\n" + STOCK_EFB_IMPORT)
    extension = (ROOT / "package" / EFB_EXTENSION).read_bytes()
    stock_wasm_html = (vfs_root / WASM_HTML).read_bytes()
    if stock_wasm_html.count(STOCK_WASM_IMPORT) != 1 or b'id="WasmInstrument"' not in stock_wasm_html:
        raise ValueError("Expected the stock WASM instrument loader and template")
    if WV081_FUEL_IMPORT in stock_wasm_html:
        raise ValueError("The WASM loader already includes this mod; supply pristine locally cached input")
    wasm_loader = stock_wasm_html.replace(STOCK_WASM_IMPORT, STOCK_WASM_IMPORT + b"\n" + WV081_FUEL_IMPORT)
    fuel_extension = (ROOT / "package" / FUEL_EXTENSION).read_bytes()
    font_source = ECAM_FONT_CACHE / STOCK_ECAM_FONT
    ecam_font = (font_source if font_source.exists() else vfs_root / STOCK_ECAM_FONT).read_bytes()
    if not ecam_font:
        raise ValueError("The installed A330 ECAM font is empty; keep VFS Projector active and retry")

    dist = ROOT / "dist"
    destination = dist / "local-sdk-sources"
    if dist.resolve().parent != ROOT or destination.resolve() != dist.resolve() / "local-sdk-sources":
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
        write(AIRCRAFT / PRESET / name, overrides.get(name, content))
    # The native modular lister omits preset PNG files; use a separate SDK Copy group.
    for name, content in thumbnails.items():
        write(Path("preset-resources/thumbnail") / name, content)
    write(Path("efb-loader") / EFB_HTML.relative_to("html_ui"), loader)
    write(Path("efb-loader") / EFB_EXTENSION.relative_to("html_ui"), extension)
    write(Path("efb-loader") / WASM_HTML.relative_to("html_ui"), wasm_loader)
    write(Path("efb-loader") / FUEL_EXTENSION.relative_to("html_ui"), fuel_extension)
    write(Path("efb-loader") / FUEL_EXTENSION.relative_to("html_ui").parent / STOCK_ECAM_FONT.name, ecam_font)
    write(Path("legal/LICENSE"), (ROOT / "LICENSE").read_bytes())
    write(Path("legal/LOCAL-ONLY.txt"), NOTICE.encode("utf-8"))
    # Inside the ModularSimObject tree so the SDK compiles the attachment model behaviors.
    prepare_center_controls(vfs_root, stage)

    # Preserve every CFG without an authored delta exactly, including camera/navigation files.
    for name, content in stock.items():
        if name not in overrides and (prepared_preset / name).read_bytes() != content:
            raise ValueError(f"Stock preset contribution changed during preparation: {name}")

    # Publish only after all inputs are read and staged. The user requested no backups.
    if destination.exists():
        if destination.resolve() != ROOT / "dist" / "local-sdk-sources":
            raise ValueError("Refusing to replace prepared sources outside the expected directory")
        shutil.rmtree(destination)
    stage.rename(destination)
    print(f"Prepared {len(stock)} stock preset CFG files.")
    print(f"Private sources: {destination}")
    print(f"SDK project: {ROOT / 'A330_WV081_Project.xml'}")
    print("Shared instrument loaders select the exact WV081 title for EFB loading and the centre-fuel controller.")
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
