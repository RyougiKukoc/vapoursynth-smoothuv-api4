#!/usr/bin/env python3
"""Smoke test the installed SmoothUV wheel via VapourSynth autoload."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any


def frame_hash(frame: Any) -> str:
    digest = hashlib.sha256()
    for plane in range(frame.format.num_planes):
        digest.update(bytes(frame[plane]))
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Smoke test an installed SmoothUV wheel.")
    parser.add_argument("--site-dir", help="Optional site-packages directory to prepend before importing modules.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = parser.parse_args(argv)

    if args.site_dir:
        sys.path.insert(0, args.site_dir)

    import vapoursynth as vs  # pylint: disable=import-outside-toplevel
    import RainbowSmooth  # pylint: disable=import-outside-toplevel

    core = vs.core
    namespace = getattr(core, "smoothuv", None)
    if namespace is None:
        raise RuntimeError("smoothuv plugin namespace was not autoloaded from the installed wheel")

    src = core.std.BlankClip(width=64, height=48, format=vs.YUV420P8, length=12, color=[96, 128, 128])
    out = core.smoothuv.SmoothUV(src, radius=3, threshold=270)
    frames = {number: out.get_frame(number) for number in (0, 3, 11)}
    frame = frames[3]
    hashes = {number: frame_hash(value) for number, value in frames.items()}
    if len(set(hashes.values())) != 1:
        raise RuntimeError(f"static SmoothUV input produced inconsistent frame hashes: {hashes}")
    stats = dict(core.std.PlaneStats(out).get_frame(3).props)

    invalid_input_rejected = False
    try:
        core.smoothuv.SmoothUV(core.std.BlankClip(width=64, height=48, format=vs.RGB24, length=1))
    except vs.Error:
        invalid_input_rejected = True
    if not invalid_input_rejected:
        raise RuntimeError("SmoothUV accepted unsupported RGB input")

    result = {
        "vapoursynth_module": vs.__file__,
        "module": RainbowSmooth.__file__,
        "namespace_loaded": namespace is not None,
        "callable_loaded": hasattr(RainbowSmooth, "RainbowSmooth"),
        "width": frame.width,
        "height": frame.height,
        "format": frame.format.name,
        "frames": out.num_frames,
        "frame_hashes": hashes,
        "invalid_input_rejected": invalid_input_rejected,
        "plane_stats_average": float(stats["PlaneStatsAverage"]),
        "plane_stats_min": float(stats["PlaneStatsMin"]),
        "plane_stats_max": float(stats["PlaneStatsMax"]),
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
