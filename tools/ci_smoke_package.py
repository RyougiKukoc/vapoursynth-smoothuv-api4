#!/usr/bin/env python3
"""Smoke-load the packaged SmoothUV plugin and render a deterministic frame."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def resolve_artifact_dir(artifact_dir_arg: str | None, artifact_zip_arg: str | None) -> tuple[Path, Path | None]:
    if artifact_zip_arg:
        archive = (ROOT / artifact_zip_arg).resolve()
        if not archive.exists():
            raise FileNotFoundError(f"missing artifact zip: {archive}")
        temp_dir = Path(tempfile.mkdtemp(prefix="smoothuv-package-"))
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(temp_dir)
        extracted_root = temp_dir
        candidates = [path for path in extracted_root.iterdir() if path.is_dir()]
        if len(candidates) != 1:
            raise RuntimeError(f"expected one top-level package directory in {archive}, found {len(candidates)}")
        return candidates[0], temp_dir

    artifact_dir = (ROOT / (artifact_dir_arg or "dist/msys2-ucrt64/smoothuv")).resolve()
    return artifact_dir, None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Smoke test a packaged SmoothUV plugin.")
    parser.add_argument("--artifact-dir", help="Packaged plugin directory.")
    parser.add_argument("--artifact-zip", help="Packaged plugin zip asset.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = parser.parse_args(argv)

    artifact_dir, temp_dir = resolve_artifact_dir(args.artifact_dir, args.artifact_zip)
    plugin = artifact_dir / "smoothuv.dll"
    manifest = artifact_dir / "manifest.vs"
    if not plugin.exists():
        raise FileNotFoundError(f"missing plugin: {plugin}")
    if not manifest.exists():
        raise FileNotFoundError(f"missing manifest: {manifest}")

    add_dll_directory = getattr(os, "add_dll_directory", None)
    dll_handles = []
    if add_dll_directory is not None:
        dll_handles.append(add_dll_directory(str(artifact_dir)))

    import vapoursynth as vs  # pylint: disable=import-outside-toplevel

    core = vs.core
    try:
        env = vs.create_environment(flags=vs.DISABLE_AUTO_LOADING)
        core = env.get_core()
    except AttributeError:
        pass

    core.std.LoadPlugin(str(plugin))
    out = core.smoothuv.SmoothUV(
        core.std.BlankClip(width=64, height=32, format=vs.YUV420P8, length=1, color=[128, 128, 128])
    )
    frame = out.get_frame(0)
    stats = dict(core.std.PlaneStats(out).get_frame(0).props)
    result = {
        "plugin": str(plugin),
        "manifest": str(manifest),
        "width": frame.width,
        "height": frame.height,
        "format": frame.format.name,
        "plane_stats_average": float(stats["PlaneStatsAverage"]),
        "plane_stats_min": float(stats["PlaneStatsMin"]),
        "plane_stats_max": float(stats["PlaneStatsMax"]),
    }

    try:
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            for key, value in result.items():
                print(f"{key}={value}")
        return 0
    finally:
        for handle in dll_handles:
            handle.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
