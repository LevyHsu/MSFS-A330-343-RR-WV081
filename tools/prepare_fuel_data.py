"""Stage private A330 module data from its layout and exact native resource paths.

This bounded inventory is not an exhaustive encrypted-archive inventory. It uses
the installed A330's plain files rather than colliding merged VFS copies; only
compressed entries and missing literal dependencies use the projector. Generated
stock-derived resources stay private under dist and must not be redistributed.
"""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import shutil

from prepare_fuel_module import ROOT, STOCK_MODULE, validate_source


CACHE = ROOT / "dist/cached-a330-module-data"


def private_path(path):
    dist = ROOT / "dist"
    resolved = Path(path).resolve()
    if dist.resolve() != dist or not resolved.is_relative_to(dist) or resolved == dist:
        raise ValueError("Resource output and cache must stay inside this repository's dist directory")
    if "community" in (part.casefold() for part in resolved.parts):
        raise ValueError("This tool does not prepare Community output")
    return resolved


def data_path(value):
    normalized = value.replace("\\", "/").removeprefix("./").removeprefix("/")
    path = PurePosixPath(normalized)
    if (
        not normalized.lower().startswith("data/")
        or path.is_absolute()
        or any(part in (".", "..") or ":" in part for part in path.parts)
    ):
        raise ValueError(f"Invalid package data path: {value}")
    return path.as_posix().lower()


def inventory(layout, module):
    result = {}
    for item in layout["content"]:
        name = item["path"]
        if not name.replace("\\", "/").lower().startswith("data/"):
            continue
        original = data_path(name)
        relative = original.removesuffix(".fsc")
        if relative in result:
            raise ValueError(f"Duplicate projected A330 data path: {relative}")
        result[relative] = {"layout_path": original, "module_literals": []}
    if not result:
        raise ValueError("The installed A330 layout contains no data files")
    unresolved = set()
    for match in re.finditer(rb"[\x20-\x7e]{5,}", module):
        literal = match.group().decode("ascii")
        normalized = literal.replace("\\", "/").removeprefix("./").removeprefix("/")
        if not normalized.lower().startswith("data/"):
            continue
        if any(character in normalized for character in "*?%{}") or not PurePosixPath(normalized).suffix:
            unresolved.add(literal)
            continue
        relative = data_path(literal)
        entry = result.setdefault(relative, {"layout_path": None, "module_literals": []})
        if literal not in entry["module_literals"]:
            entry["module_literals"].append(literal)
    return result, sorted(unresolved)


def find_package(vfs_root):
    candidates = [
        vfs_root.parent / "Packages/Official2024" / store / "microsoft-aircraft-a330"
        for store in ("Steam", "OneStore")
    ]
    found = [path for path in candidates if (path / "layout.json").is_file()]
    if len(found) != 1:
        raise ValueError("Supply --stock-package pointing to the installed microsoft-aircraft-a330 package")
    return found[0]


def package_inventory(vfs_root, stock_package):
    metadata_path = private_path(CACHE / "package-inventory.json")
    saved = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else None
    if stock_package:
        package = Path(stock_package).resolve()
    else:
        try:
            package = find_package(vfs_root)
        except ValueError:
            if saved is None:
                raise
            package = Path(saved["stock_package"])
    if (package / "manifest.json").is_file() and (package / "layout.json").is_file():
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8-sig"))
        layout = json.loads((package / "layout.json").read_text(encoding="utf-8-sig"))
        # Cache only package identity and resource paths/sizes, without hash metadata.
        saved = {
            "stock_package": str(package),
            "manifest": {key: manifest.get(key) for key in ("title", "package_version")},
            "layout": {"content": [
                {"path": item["path"], "size": item["size"]}
                for item in layout["content"]
                if item["path"].replace("\\", "/").lower().startswith("data/")
            ]},
        }
        if package.name.lower() != "microsoft-aircraft-a330" or manifest.get("title") != "Airbus A330":
            raise ValueError("Expected the installed Microsoft/iniBuilds Airbus A330 package")
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
    elif saved is None or Path(saved["stock_package"]).resolve() != package.resolve():
        raise ValueError("No installed or previously cached inventory for this A330 package")
    return package, saved["manifest"], saved["layout"]


def prepare(vfs_root, output_data_dir, *, stock_package=None, source_module=None):
    vfs_root = Path(vfs_root).resolve()
    package, manifest, layout = package_inventory(vfs_root, stock_package)
    output = private_path(output_data_dir)
    if output.name.lower() != "data":
        raise ValueError("The output directory must be the private candidate's package-root data directory")
    if package.name.lower() != "microsoft-aircraft-a330" or manifest.get("title") != "Airbus A330":
        raise ValueError("Expected the installed Microsoft/iniBuilds Airbus A330 package")
    version = manifest.get("package_version", "")
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", version):
        raise ValueError("Unexpected A330 package version")
    cache = private_path(CACHE / version)
    if output.is_relative_to(cache) or cache.is_relative_to(output):
        raise ValueError("Candidate resources and private source cache must be separate")
    module_path = Path(source_module) if source_module else vfs_root / STOCK_MODULE
    if source_module is None and not module_path.is_file():
        module_path = ROOT / "dist/cached-stock-inputs" / STOCK_MODULE
    module = module_path.read_bytes()
    validate_source(module)
    entries, unresolved = inventory(layout, module)
    provenance_path = private_path(cache / "source-provenance.json")
    sources = json.loads(provenance_path.read_text(encoding="utf-8")) if provenance_path.is_file() else {}
    files = []
    # Read/cache the complete bounded inventory before publishing candidate files.
    for relative, entry in sorted(entries.items()):
        stored = entry["layout_path"]
        plain = stored is not None and not stored.endswith(".fsc")
        source = package / stored if plain else vfs_root / relative
        cached = private_path(cache / relative)
        provenance = "installed-a330-layout" if plain else (
            "projected-decompressed-layout" if stored else "projected-module-literal"
        )
        from_cache = cached.is_file() and not (plain and source.is_file())
        if not from_cache:
            data = source.read_bytes()
            if not data:
                raise ValueError(f"Required A330 module resource is empty: {relative}")
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(data)
            size = len(data)
            sources[relative] = {"source": str(source), "provenance": provenance}
        else:
            size = cached.stat().st_size
            if not size:
                raise ValueError(f"Required cached A330 module resource is empty: {relative}")
            if relative not in sources:
                raise ValueError(f"Cached resource is missing its source provenance: {relative}")
        files.append({
            "path": relative, "bytes": size, "provenance": provenance,
            "source": sources[relative]["source"], "read_from_cache": from_cache, "layout_path": stored,
            "module_literals": entry["module_literals"],
        })
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    if output.exists() and any(path.is_file() for path in output.rglob("*")):
        existing = {path.relative_to(output).as_posix().lower() for path in output.rglob("*") if path.is_file()}
        expected = {str(PurePosixPath(name).relative_to("data")) for name in entries}
        if existing - expected:
            raise ValueError("Candidate data directory contains files outside this inventory; use a fresh private staging directory")
    for item in files:
        destination = private_path(output / PurePosixPath(item["path"]).relative_to("data"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cache / item["path"], destination)
    report = {
        "scope": "LOCAL STOCK-DERIVED DATA ONLY - DO NOT REDISTRIBUTE",
        "stock_package": str(package), "package_version": version,
        "source_module": str(module_path), "output_data": str(output),
        "file_count": len(files), "total_bytes": sum(item["bytes"] for item in files),
        "layout_file_count": sum(item["layout_path"] is not None for item in files),
        "literal_only_file_count": sum(item["layout_path"] is None for item in files),
        "unresolved_directory_or_dynamic_literals": unresolved,
        "limitations": [
            "Complete only for the installed A330 layout data paths and exact literal data-file paths in the inspected module",
            "Encrypted archive indexes and dynamically constructed paths are not exhaustively inventoried",
            "Projected compressed entries and literal-only files have unverified individual package ownership in the merged VFS",
            "No SDK build, module loading, cockpit rendering or simulator behavior is validated here",
        ],
        "files": files,
    }
    report_path = private_path(output.parent / "fuel-data-resources.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vfs-root", type=Path, required=True)
    parser.add_argument("--stock-package", type=Path)
    parser.add_argument("--source-module", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/private-fuel-module/data")
    args = parser.parse_args()
    try:
        report = prepare(args.vfs_root, args.output, stock_package=args.stock_package, source_module=args.source_module)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Fuel data preparation refused: {error}\n")
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
