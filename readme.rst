SmoothUV
========

SmoothUV is a spatial derainbow filter. The luma is returned unchanged.

This repository now targets modern VapourSynth API4 packaging on Windows while
preserving the original filter behavior. It ships both:

- the native plugin ``smoothuv.dll``
- the Python helper module ``RainbowSmooth.py``

Currently only x86 systems are supported.

This is a port of the SmoothUV filter from the SmoothUV Avisynth plugin. The
Avisynth plugin also includes the SSHiQ filter, which was not ported.
``RainbowSmooth`` is a port of the Avisynth function ``rainbow_smooth()``.


Installation
============

Recommended install from the GitHub repository
----------------------------------------------

For Windows x86_64, the recommended install path is:

::

    pip install "vapoursynth-smoothuv @ git+https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4.git"

This is the preferred user-facing install strategy for this repository.
During installation, the build hook first tries to download the matching
prebuilt Release asset ``smoothuv-msys2-ucrt64.zip`` for the current package
version tag such as ``v1.0``. If that asset exists, pip reuses the tested
binary package instead of compiling ``smoothuv.dll`` locally.

Installed result:

- ``RainbowSmooth.py`` is placed in ``site-packages`` for
  ``import RainbowSmooth``
- ``smoothuv.dll`` and ``manifest.vs`` are placed under
  ``site-packages/vapoursynth/plugins/smoothuv/`` for VapourSynth R77 autoload

This avoids the normal "download DLL and copy it into the plugin directory"
workflow for end users.

Direct wheel install
--------------------

If you want the most direct binary install path, install the published wheel
from the GitHub Release:

::

    pip install https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4/releases/download/v1.0/vapoursynth_smoothuv-1.0-py3-none-win_amd64.whl

This installs the same Python helper and plugin files, but skips the VCS build
step entirely.

Install controls
----------------

The VCS/source install path can be overridden with environment variables:

- ``SMOOTHUV_FORCE_BUILD=1``
  Always skip Release assets and compile locally.
- ``SMOOTHUV_PREBUILT_URL=...``
  Use an explicit prebuilt archive path or URL. This is strict: if it fails,
  the build fails instead of silently falling back.
- ``SMOOTHUV_PREBUILT_TAG=v1.0``
  Override the default Release tag used to construct the GitHub asset URL.
- ``SMOOTHUV_PREBUILT_REPOSITORY=owner/repo``
  Override the default GitHub repository slug used for Release asset lookup.
- ``SMOOTHUV_PREBUILT_ASSET_NAME=smoothuv-msys2-ucrt64.zip``
  Override the expected Release asset filename.

Force a local source build in PowerShell:

::

    $env:SMOOTHUV_FORCE_BUILD = '1'
    pip install "vapoursynth-smoothuv @ git+https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4.git"

Point at a specific prebuilt archive in PowerShell:

::

    $env:SMOOTHUV_PREBUILT_URL = 'https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4/releases/download/v1.0/smoothuv-msys2-ucrt64.zip'
    pip install "vapoursynth-smoothuv @ git+https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4.git"

If the VCS install falls back to local compilation, it expects a working
Windows build environment as described below.


Usage
=====

::

    smoothuv.SmoothUV(clip clip, [int radius=3, int threshold=270, bint interlaced])


Parameters:
    *clip*
        A clip to process. It must have constant format and it must be
        8 bit YUV.

    *radius*
        Radius. Must be between 1 and 7.

        Larger values smooth more.

        Default: 3.

    *threshold*
        Threshold. Must be between 0 and 450.

        Larger values smooth more.

        Default: 270.

    *interlaced*
        Each frame's "_FieldBased" property is examined to determine if
        the frame should be considered interlaced. If the "_FieldBased"
        property is 0 or it doesn't exist, the frame is considered not
        interlaced.

        Set this parameter to override the automatic detection of
        interlaced frames.


::

    RainbowSmooth(clip, radius=3, lthresh=0, hthresh=220, mask="original")


Parameters:
    *clip*
        The clip to process.

    *radius*
        Radius passed to SmoothUV.

        Default: 3.

    *lthresh*, *hthresh*
        The low and the high smoothing thresholds. Use smaller values
        for safer processing. The masking is only used for hthresh,
        so if you set lthresh greater than hthresh lthresh will be the
        overall threshold and no masking will be used (fastest). But if
        you set lthresh=0 you disable the basic chroma smoothing and
        use only the chroma smoothing on edges.

        Default: lthresh=0, hthresh=220.

    *mask*
        Edge mask to use. It can be either a clip, or one of the
        following strings: "original", "prewitt", "sobel", "tcanny",
        "fast_sobel", "kirsch", "retinex_edgemask".

        "original" is the edge mask used by the original
        rainbow_smooth() Avisynth function.

        The latter three require kagefunc.py.

        Default: "original".


Building from source
====================

Preferred Windows API4 build
----------------------------

The preferred contributor and CI path is MSYS2/UCRT64 with Meson and a
VapourSynth R77 Python wheel installed into the active Python environment.

Repository helper scripts:

::

    python tools/ci_prepare_vs_wheel.py
    python tools/ci_build_windows.py --clean
    python tools/ci_smoke_package.py

``ci_prepare_vs_wheel.py`` writes a normalized ``vapoursynth.pc`` tree under
``_deps/vapoursynth-wheel-R77/``. The Windows build helper and wheel hook will
reuse that location automatically for both ``PKG_CONFIG`` and
``PKG_CONFIG_PATH`` when it is present.

To build the Windows wheel as well:

::

    python tools/ci_build_windows.py --clean --wheel

If the active Python does not have ``mesonbuild`` installed, point the build
helper at another Python that does:

::

    python tools/ci_build_windows.py --clean --meson-python C:\path\to\python.exe

Or point it at a specific ``meson.exe`` directly:

::

    python tools/ci_build_windows.py --clean --meson-exe C:\path\to\meson.exe

When invoking Meson from PowerShell or ``cmd.exe`` on Windows, keep the active
MSYS2 UCRT64 toolchain ahead of the system toolchain. If Meson still tries
``cl``, force GCC explicitly:

::

    $env:CC = 'gcc'
    $env:CXX = 'g++'
    python tools/ci_build_windows.py --clean

The packaged CI artifact is written to:

::

    dist/msys2-ucrt64/smoothuv/
      manifest.vs
      smoothuv.dll

That package directory is the same layout later reused for Release assets and
wheel packaging.

Generic Meson or Autotools build
--------------------------------

The upstream tree still includes the original generic build entry points:

::

    mkdir build
    cd build
    meson ../
    ninja

Or:

::

    ./autogen.sh
    ./configure
    make

Meson runs faster than autogen.sh and configure. These generic commands are
useful for manual development, but the Windows Release flow for this fork is
based on the helper scripts above.


Release workflow
================

The Windows GitHub Actions workflow produces three related outputs:

- a package directory artifact under ``dist/msys2-ucrt64/smoothuv/``
- a wheel under ``dist/wheels/``
- Release-ready assets under ``dist/release-assets/``

On ``v*`` tag pushes, the workflow creates or updates the matching GitHub
Release and uploads the contents of ``dist/release-assets/``. That directory
currently contains:

- ``smoothuv-msys2-ucrt64.zip`` for the prebuilt VCS/source-install path
- the built ``vapoursynth_smoothuv-*.whl`` wheel for direct pip installation


License
=======

GNU GPL, like the Avisynth plugin.
