project('SmoothUV', 'cpp',
        version: '3',
        default_options: ['cpp_std=c++11', 'buildtype=release'],
        meson_version: '>=0.49')

plugin_name = 'smoothuv'

warnings = [
  '-Wall',
  '-Wextra',
  '-Wshadow',
]

cflags = warnings

ldflags = [
]


host_cpu_family = host_machine.cpu_family()

if host_cpu_family.startswith('x86')
  cflags += ['-mfpmath=sse', '-msse2']
else
  error('Currently only x86 systems are supported.')
endif


host_system = host_machine.system()

if host_system == 'windows' or host_system == 'cygwin'
  if host_cpu_family == 'x86'
    cflags += '-mstackrealign'
    ldflags += '-Wl,--kill-at'
  endif
endif

cxx = meson.get_compiler('cpp')
gcc_syntax = cxx.get_argument_syntax() == 'gcc'

if not gcc_syntax
  cflags = []
  ldflags = []
endif

sources = [
  'src/SmoothUV.cpp',
]

deps = [
  dependency('vapoursynth').partial_dependency(includes: true, compile_args: true),
  cxx.find_library('m', required: false),
]

shared_module(plugin_name,
              sources,
              dependencies: deps,
              link_args: ldflags,
              cpp_args: cflags,
              name_prefix: '',
              install: true)
