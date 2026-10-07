"""Assemble the local Community prototype; never install it into MSFS."""

import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "a330-wv081-aircraft-baseline"


def main():
    raise SystemExit(
        "Packaging disabled: v0.1.1 was withdrawn following two reported MSFS startup crashes. "
        "See package/README.md; the merged aircraft requires SDK validation before another package is offered."
    )
    source = ROOT / "package"
    dist = ROOT / "dist"
    output = dist / PACKAGE_NAME
    # Only replace this builder's output within the repository.
    if dist.resolve().parent != ROOT or output.is_symlink() or output.resolve().parent != dist.resolve():
        raise RuntimeError("Build output must remain inside the repository's dist directory")
    dist.mkdir(exist_ok=True)
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(source, output)
    shutil.copy2(ROOT / "LICENSE", output / "LICENSE")

    content = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "layout.json"}:
            stat = path.stat()
            content.append({
                "path": path.relative_to(output).as_posix(),
                "size": stat.st_size,
                "date": stat.st_mtime_ns // 100 + 116444736000000000,
            })
    (output / "layout.json").write_text(
        json.dumps({"content": content}, indent=2) + "\n", encoding="utf-8"
    )
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["total_package_size"] = str(sum(entry["size"] for entry in content))
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    archive = shutil.make_archive(str(output), "zip", root_dir=dist, base_dir=PACKAGE_NAME)
    print(f"Package: {output}")
    print(f"Archive: {archive}")
    print("Development baseline only; simulator loading has not been verified.")


if __name__ == "__main__":
    main()
