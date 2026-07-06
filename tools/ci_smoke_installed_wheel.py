#!/usr/bin/env python3
"""Smoke test the installed SmoothUV wheel via autoload and RainbowSmooth import."""

from __future__ import annotations

import argparse
import json
import sys


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

    clip = core.std.BlankClip(width=64, height=32, format=vs.YUV420P8, length=1, color=[128, 128, 128])
    out = RainbowSmooth.RainbowSmooth(clip)
    frame = out.get_frame(0)
    stats = dict(core.std.PlaneStats(out).get_frame(0).props)
    result = {
        "vapoursynth_module": vs.__file__,
        "module": RainbowSmooth.__file__,
        "namespace_loaded": namespace is not None,
        "callable_loaded": hasattr(RainbowSmooth, "RainbowSmooth"),
        "width": frame.width,
        "height": frame.height,
        "format": frame.format.name,
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
