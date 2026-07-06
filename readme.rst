Description
===========

SmoothUV is a spatial derainbow filter.

The luma is returned unchanged.

Currently only x86 systems are supported.

This is a port of the SmoothUV filter from the SmoothUV Avisynth
plugin. The Avisynth plugin also includes the SSHiQ filter, which was
not ported.


RainbowSmooth is a script which adds edge detection to SmoothUV. It is
a port of the Avisynth function rainbow_smooth().


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

Compilation
===========

::

    mkdir build && cd build
    meson ../
    ninja

Or:

::

    ./autogen.sh
    ./configure
    make

Meson runs faster than autogen.sh and configure.

Windows CI / local reproducible API4 build
==========================================

The preferred Windows API4 path is MSYS2/UCRT64 with Meson and a VapourSynth
R77 Python wheel installed into the active Python environment.

Repository helper scripts:

::

    python tools/ci_prepare_vs_wheel.py
    python tools/ci_build_windows.py --clean
    python tools/ci_smoke_package.py

If the active Python does not have ``mesonbuild`` installed, point the build
helper at another Python that does:

::

    python tools/ci_build_windows.py --clean --meson-python C:\path\to\python.exe

Or point it at a specific ``meson.exe`` directly:

::

    python tools/ci_build_windows.py --clean --meson-exe C:\path\to\meson.exe

To build the Windows wheel as well:

::

    python tools/ci_build_windows.py --clean --wheel

The packaged CI artifact is written to:

::

    dist/msys2-ucrt64/smoothuv/
      manifest.vs
      smoothuv.dll

This package directory can be copied under a VapourSynth
``vapoursynth/plugins`` directory for manifest-based loading.

Windows PyPI wheel
==================

The repository now also supports a Windows-first wheel layout intended for
``pip install vapoursynth-smoothuv``.

The wheel contains both:

- ``vapoursynth/plugins/smoothuv/smoothuv.dll`` and ``manifest.vs`` for
  VapourSynth R77 plugin discovery.
- Top-level ``RainbowSmooth.py`` so users can directly ``import RainbowSmooth``.

Build locally with a Python that has ``build``, ``hatchling``, ``packaging``,
``meson``, ``ninja``, ``VapourSynth``, and the prepared ``PKG_CONFIG_PATH``:

::

    python -m build --wheel --no-isolation

The GitHub Actions Windows workflow now builds the package directory, builds
the wheel, installs the wheel, verifies ``import RainbowSmooth``, and renders
one deterministic frame through the installed plugin.

Installation
============

Recommended Windows install: release wheel
------------------------------------------

If a Windows wheel has already been published, install that directly:

::

    pip install https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4/releases/download/v1.0/vapoursynth_smoothuv-1.0-py3-none-win_amd64.whl

This is the most direct binary install path. It places:

- ``RainbowSmooth.py`` in ``site-packages`` for ``import RainbowSmooth``
- ``smoothuv.dll`` and ``manifest.vs`` under
  ``site-packages/vapoursynth/plugins/smoothuv/`` for VapourSynth R77 autoload

Source install from the Git repository
--------------------------------------

To install from the repository itself, use pip's VCS form:

::

    pip install "vapoursynth-smoothuv @ git+https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4.git"

On Windows x86_64, the build hook first tries to download a prebuilt release
asset named ``smoothuv-msys2-ucrt64.zip`` from:

::

    https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4/releases/download/v<version>/

where ``<version>`` defaults to the package version in ``pyproject.toml``
prefixed with ``v``.

If that release asset exists, pip still builds a wheel locally, but it reuses
the downloaded prebuilt plugin package instead of compiling ``smoothuv.dll``.
If the release asset is missing or unreachable, the hook falls back to the
normal local Meson build.

Install strategy controls
-------------------------

The source-install helper logic can be overridden with environment variables:

- ``SMOOTHUV_FORCE_BUILD=1``
  Always skip release assets and compile locally.
- ``SMOOTHUV_PREBUILT_URL=...``
  Use an explicit prebuilt archive path or URL. This is strict: if it fails,
  the build fails instead of silently falling back.
- ``SMOOTHUV_PREBUILT_TAG=v1.0``
  Override the default release tag used to construct the GitHub release asset
  URL.
- ``SMOOTHUV_PREBUILT_REPOSITORY=owner/repo``
  Override the default GitHub repository slug used for release asset lookup.
- ``SMOOTHUV_PREBUILT_ASSET_NAME=smoothuv-msys2-ucrt64.zip``
  Override the expected release asset filename.

Force a local source build:

::

    set SMOOTHUV_FORCE_BUILD=1
    pip install "vapoursynth-smoothuv @ git+https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4.git"

Build from the repository while pointing at a specific prebuilt archive:

::

    set SMOOTHUV_PREBUILT_URL=https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4/releases/download/v1.0/smoothuv-msys2-ucrt64.zip
    pip install "vapoursynth-smoothuv @ git+https://github.com/RyougiKukoc/vapoursynth-smoothuv-api4.git"

Release workflow
================

The Windows GitHub Actions workflow now produces three related outputs:

- a package directory artifact under ``dist/msys2-ucrt64/smoothuv/``
- a wheel under ``dist/wheels/``
- release-ready assets under ``dist/release-assets/``

On ``v*`` tag pushes, the workflow creates or updates the matching GitHub
Release and uploads the contents of ``dist/release-assets/``. That directory
currently contains:

- ``smoothuv-msys2-ucrt64.zip`` for the prebuilt source-install path
- the built ``vapoursynth_smoothuv-*.whl`` wheel for direct pip installation


License
=======

GNU GPL, like the Avisynth plugin.
