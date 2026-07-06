from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from packaging import tags


ROOT = Path(__file__).resolve().parent
PLUGIN_NAME = "smoothuv"
DEFAULT_REPOSITORY = "RyougiKukoc/vapoursynth-smoothuv-api4"
DEFAULT_PREBUILT_ASSET = "smoothuv-msys2-ucrt64.zip"


def _find_command(*candidates: str) -> str | None:
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def _meson_command() -> list[str]:
    meson = _find_command("meson")
    if meson:
        return [meson]

    for module_name in ("mesonbuild", "mesonbuild.mesonmain"):
        module_runner = [sys.executable, "-m", module_name]
        probe = subprocess.run(module_runner + ["--version"], cwd=ROOT, capture_output=True, text=True)
        if probe.returncode == 0:
            return module_runner

    raise FileNotFoundError("meson executable not found and python -m mesonbuild is unavailable")


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def _truthy(value: str | None) -> bool:
    return bool(value and value.strip().lower() not in {"", "0", "false", "no", "off"})


def _default_prebuilt_url(version: str) -> str:
    repository = os.environ.get("SMOOTHUV_PREBUILT_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPOSITORY
    tag = os.environ.get("SMOOTHUV_PREBUILT_TAG") or f"v{version}"
    asset = os.environ.get("SMOOTHUV_PREBUILT_ASSET_NAME") or DEFAULT_PREBUILT_ASSET
    return f"https://github.com/{repository}/releases/download/{tag}/{asset}"


def _project_version() -> str:
    override = os.environ.get("SMOOTHUV_PREBUILT_VERSION")
    if override:
        return override
    pyproject = ROOT / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    version = data.get("project", {}).get("version")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError(f"project.version missing from {pyproject}")
    return version


def _prebuilt_source(version: str) -> tuple[str, bool]:
    explicit = os.environ.get("SMOOTHUV_PREBUILT_URL")
    if explicit:
        return explicit, True
    return _default_prebuilt_url(version), False


def _supports_prebuilt() -> bool:
    return sys.platform == "win32" and platform.machine().lower() in {"amd64", "x86_64"}


def _fetch_prebuilt_archive(source: str, destination: Path) -> None:
    candidate = Path(source)
    if candidate.exists():
        shutil.copy2(candidate, destination)
        return

    request = urllib.request.Request(source, headers={"User-Agent": "vapoursynth-smoothuv-build-hook"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _stage_prebuilt_plugin(version: str, target_dir: Path) -> bool:
    if _truthy(os.environ.get("SMOOTHUV_FORCE_BUILD")):
        print("SmoothUV wheel build: skipping prebuilt asset because SMOOTHUV_FORCE_BUILD is set")
        return False
    if not _supports_prebuilt():
        print("SmoothUV wheel build: prebuilt release asset path only applies to Windows x86_64; falling back to local build")
        return False

    source, explicit = _prebuilt_source(version)
    asset_name = Path(source).name or DEFAULT_PREBUILT_ASSET
    try:
        with tempfile.TemporaryDirectory(prefix="smoothuv-prebuilt-") as temp_dir_text:
            temp_dir = Path(temp_dir_text)
            archive_path = temp_dir / asset_name
            _fetch_prebuilt_archive(source, archive_path)
            with zipfile.ZipFile(archive_path) as zf:
                package_members = [name for name in zf.namelist() if name.replace("\\", "/").startswith(f"{PLUGIN_NAME}/") and not name.endswith("/")]
                if not package_members:
                    package_members = [name for name in zf.namelist() if name.replace("\\", "/") in {f"{PLUGIN_NAME}.dll", "manifest.vs"}]
                if not package_members:
                    raise FileNotFoundError(f"prebuilt archive does not contain a {PLUGIN_NAME}/ package directory")

                for member in package_members:
                    normalized = member.replace("\\", "/")
                    relative = normalized.split("/", 1)[1] if normalized.startswith(f"{PLUGIN_NAME}/") else normalized
                    out_path = target_dir / relative
                    if normalized.endswith("/"):
                        continue
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, out_path.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
            plugin_dll = target_dir / f"{PLUGIN_NAME}.dll"
            if not plugin_dll.exists():
                raise FileNotFoundError(f"prebuilt archive did not provide {PLUGIN_NAME}.dll")
            manifest = target_dir / "manifest.vs"
            if not manifest.exists():
                manifest.write_text(
                    "[VapourSynth Manifest V1]\n"
                    f"{PLUGIN_NAME}\n",
                    encoding="utf-8",
                )
    except Exception as exc:
        if explicit:
            raise RuntimeError(f"failed to use explicit SmoothUV prebuilt asset {source!r}") from exc
        print(f"SmoothUV wheel build: prebuilt asset unavailable at {source}; falling back to local build ({exc})")
        return False

    print(f"SmoothUV wheel build: using prebuilt release asset {source}")
    return True


class CustomHook(BuildHookInterface[Any]):
    build_dir = ROOT / "build-wheel"
    dist_dir = ROOT / "vapoursynth" / "plugins" / PLUGIN_NAME

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        del version
        build_data["pure_python"] = False
        build_data["tag"] = f"py3-none-{next(tags.platform_tags())}"
        project_version = _project_version()

        shutil.rmtree(self.build_dir, ignore_errors=True)
        shutil.rmtree(self.dist_dir.parent.parent, ignore_errors=True)
        self.dist_dir.mkdir(parents=True, exist_ok=True)

        if not _stage_prebuilt_plugin(project_version, self.dist_dir):
            env = os.environ.copy()
            meson = _meson_command()
            _run(meson + ["setup", str(self.build_dir), "--wipe"], env=env)
            _run(meson + ["compile", "-C", str(self.build_dir)], env=env)

            plugin_dll = self.build_dir / f"{PLUGIN_NAME}.dll"
            if not plugin_dll.exists():
                raise FileNotFoundError(f"missing built plugin: {plugin_dll}")

            shutil.copy2(plugin_dll, self.dist_dir / plugin_dll.name)
            (self.dist_dir / "manifest.vs").write_text(
                "[VapourSynth Manifest V1]\n"
                f"{PLUGIN_NAME}\n",
                encoding="utf-8",
            )

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:
        del version, build_data, artifact_path
        shutil.rmtree(self.build_dir, ignore_errors=True)
        shutil.rmtree(self.dist_dir.parent.parent, ignore_errors=True)
