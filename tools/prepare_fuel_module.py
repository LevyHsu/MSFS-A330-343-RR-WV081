"""Prepare an experimental, private A333 centre-fuel module from a local stock file.

The observed projected .wasm is a native x64 PE, not portable WebAssembly. Its
loading and runtime behavior after copying remain unverified. Only this original
tool is distributable; generated stock-derived modules retain their original
rights and must stay private. This does not build, install, or run the simulator.
"""

import argparse
import json
from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
STOCK_MODULE = Path(
    "SimObjects/Airplanes/microsoft-a330/attachments/inibuilds/"
    "Function_A330_Interior/panel/inibuilds-a330.wasm"
)
MODULE_NAME = "inibuilds-a330-wv081.wasm"
EXPECTED_SIZE = 25_239_040
# Exact observed layout of the normal module, not its generic sibling.
SECTIONS = (
    (b".text", 0x1000, 0x15F3526, 0x15F3600, 0x400, 0x60000020),
    (b".rdata", 0x15F5000, 0x19C2C4, 0x19C400, 0x15F3A00, 0x40000040),
    (b".data", 0x1792000, 0xD10, 0x200, 0x178FE00, 0xC0000040),
    (b".pdata", 0x1793000, 0x81798, 0x81800, 0x1790000, 0x40000040),
    (b".00cfg", 0x1815000, 0x28, 0x200, 0x1811800, 0x40000040),
    (b"_RDATA", 0x1816000, 0x94, 0x200, 0x1811A00, 0x40000040),
    (b".reloc", 0x1817000, 0x2C, 0x200, 0x1811C00, 0x42000040),
)
CONTEXTS = {
    "centre_refuel": (0xBE0995, bytes.fromhex(
        "b9 14 09 00 00 e8 b1 1c 4b ff 83 f8 01 0f 84 16 04 00 00 "
        "8b 44 24 34 c5 fa 10 44 06 50"
    )),
    "centre_transfer": (0x3A2C0E, bytes.fromhex(
        "b9 14 09 00 00 e8 38 fa ce ff 83 f8 01 0f 85 15 05 00 00 "
        "b9 e3 03 00 00 e8 25 fa ce ff 83 f8 02 7f 28 "
        "b9 9c 09 00 00 e8 16 fa ce ff 83 f8 01 74 19"
    )),
    "preserved_a333_trim": (0x39FEFB, bytes.fromhex(
        "b9 14 09 00 00 e8 4b 27 cf ff 83 f8 00 0f 85 10 1e 00 00 "
        "b9 4e 08 00 00 e8 38 27 cf ff 83 f8 00 0f 85 fd 1d 00 00"
    )),
}


def file_offset(rva, size=1):
    for _, virtual, _, raw_size, raw, _ in SECTIONS:
        if virtual <= rva and rva + size <= virtual + raw_size:
            return raw + rva - virtual
    raise ValueError(f"RVA 0x{rva:x} is outside the observed file-backed sections")


def validate_source(data):
    if len(data) != EXPECTED_SIZE or data[:2] != b"MZ":
        raise ValueError("Expected the observed 25,239,040-byte native stock module; refusing another format/version")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe != 0x78 or data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Unexpected PE header")
    machine, count = struct.unpack_from("<HH", data, pe + 4)
    optional_size, characteristics = struct.unpack_from("<HH", data, pe + 20)
    optional = pe + 24
    if (machine, count, optional_size, characteristics) != (0x8664, 7, 240, 0x2022):
        raise ValueError("Unexpected PE machine, section count, optional header or characteristics")
    if (
        struct.unpack_from("<H", data, optional)[0] != 0x20B
        or struct.unpack_from("<Q", data, optional + 24)[0] != 0x180000000
        or struct.unpack_from("<II", data, optional + 32) != (4096, 512)
        or struct.unpack_from("<II", data, optional + 56) != (25_264_128, 1024)
    ):
        raise ValueError("Unexpected PE32+ image layout")
    for index, expected in enumerate(SECTIONS):
        offset = optional + optional_size + 40 * index
        name = data[offset:offset + 8].rstrip(b"\0")
        virtual_size, virtual, raw_size, raw = struct.unpack_from("<IIII", data, offset + 8)
        flags = struct.unpack_from("<I", data, offset + 36)[0]
        if (name, virtual, virtual_size, raw_size, raw, flags) != expected:
            raise ValueError(f"Unexpected PE section layout at index {index}")
        if raw + raw_size > len(data):
            raise ValueError("PE section extends beyond the input")
    for name, (rva, expected) in CONTEXTS.items():
        offset = file_offset(rva, len(expected))
        if data[offset:offset + len(expected)] != expected:
            raise ValueError(f"Instruction context changed at {name} (RVA 0x{rva:x}); review this stock version before adapting it")
    pointer = struct.unpack_from("<I", data, 0x16BE600 + 4 * 0x914)[0]
    name_offset = pointer + 0x15F4160
    if data[name_offset:name_offset + 11] != b"INI_IS_200\0":
        raise ValueError("Expected registry ID 0x914 to identify INI_IS_200")


def conditional_branch(data, rva, condition, target):
    offset = file_offset(rva, 6)
    instruction = data[offset:offset + 6]
    if instruction[:2] != bytes((0x0F, condition)):
        raise ValueError(f"Unexpected conditional branch at RVA 0x{rva:x}")
    decoded_target = rva + 6 + struct.unpack_from("<i", instruction, 2)[0]
    if decoded_target != target:
        raise ValueError(f"Unexpected branch target at RVA 0x{rva:x}")
    return offset, instruction


def prepare(vfs_root, output_module, *, source_module=None):
    source = Path(source_module) if source_module is not None else Path(vfs_root) / STOCK_MODULE
    source = source.resolve()
    destination = Path(output_module).resolve()
    dist = ROOT / "dist"
    if (
        dist.resolve() != dist
        or not destination.is_relative_to(dist)
        or destination.name != MODULE_NAME
        or "community" in (part.casefold() for part in destination.parts)
        or destination == source
    ):
        raise ValueError(f"Output must be a private {MODULE_NAME} inside this repository's dist directory")
    if source.name != "inibuilds-a330.wasm":
        raise ValueError("Supply the pristine normal inibuilds-a330.wasm, not a generated or generic module")
    data = source.read_bytes()
    validate_source(data)
    refuel_offset, refuel = conditional_branch(data, 0xBE09A2, 0x84, 0xBE0DBE)
    transfer_offset, transfer = conditional_branch(data, 0x3A2C1B, 0x85, 0x3A3136)
    conditional_branch(data, 0x39FF08, 0x85, 0x3A1D1E)

    # Refuel JE takes the centre path. NOP + JMP keeps its original rel32 target.
    refuel_new = b"\x90\xe9" + refuel[2:]
    # Transfer JNE skips the centre path. Removing this branch enables fallthrough.
    transfer_new = b"\x90" * 6
    patched = bytearray(data)
    patches = ((refuel_offset, refuel_new), (transfer_offset, transfer_new))
    for offset, replacement in patches:
        patched[offset:offset + len(replacement)] = replacement
    # Assert that only the two reviewed instruction slots changed, without hashes.
    cursor = 0
    for offset, replacement in sorted(patches):
        if patched[cursor:offset] != data[cursor:offset]:
            raise ValueError("Unexpected change outside the two centre branches")
        cursor = offset + len(replacement)
    if patched[cursor:] != data[cursor:] or len(patched) != len(data):
        raise ValueError("Unexpected change outside the two centre branches")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(patched)
    return {
        "source": str(source),
        "output": str(destination),
        "scope": "EXPERIMENTAL LOCAL PREPARATION ONLY - DO NOT REDISTRIBUTE",
        "changes": [
            {"rva": "0xbe09a2", "original": "JE 0xbe0dbe", "prepared": "NOP; JMP 0xbe0dbe",
             "before": refuel.hex(" "), "after": refuel_new.hex(" ")},
            {"rva": "0x3a2c1b", "original": "JNE 0x3a3136", "prepared": "6 NOPs; fall through to 0x3a2c21",
             "before": transfer.hex(" "), "after": transfer_new.hex(" ")},
        ],
        "preserved": "INI_IS_200 registry and all other bytes, including A333 CG/trim gate RVA 0x39ff08",
        "unverified": [
            "Loading and portability of this copied projected native PE module",
            "Refuel distribution, centre controls, engine supply and A333 trim/CG interaction in the simulator",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vfs-root", type=Path, required=True)
    parser.add_argument("--source-module", type=Path, help="Optional pristine private cached stock module")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/private-fuel-module" / MODULE_NAME)
    args = parser.parse_args()
    try:
        report = prepare(args.vfs_root, args.output, source_module=args.source_module)
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"Fuel module preparation refused: {error}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
