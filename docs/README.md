# Documentation — 0.7.1

## Current usage

- [Main README](../README.md): setup, build commands and renderer overview.
- [Examples](../examples/README.md) and [cartridge inventory](V10_CARTRIDGES.md).
- [Builds and verification](V10_TESTING.md), including accepted Marbles reproduction limits.
- [Configuration](CONFIGURATION.md) and [Windows setup](WINDOWS_SETUP.md).
- [Architecture](ARCHITECTURE.md), [Blender](BLENDER_PIPELINE.md),
  [OBJ](OBJ_PIPELINE.md) and [SVG](SVG_PIPELINE.md) pipelines.
- [Authored scenes](CARTRIDGE_SCENES.md) and [recording start](MARBLES_RECORDING.md).
- [Upgrade and documentation fix pack](UPGRADING_0.7.1.md).
- [Example cleanup](EXAMPLES_CLEANUP_070.md) and [external history](REPOSITORY_CLEANUP_070.md).

## Measurements and further development

- [Canonical performance comparison](PERFORMANCE_COMPARISON.md): matched normal PLAY ALL results.
- [Capacity accounting](CARTRIDGE_CAPACITY.md).
- [Optimization findings](OPTIMIZATION_FINDINGS.md) and [Marbles recovery](MARBLES_RECOVERY.md): chronological experiments, with the release outcome at the top.
- [Candidate runner](CANDIDATE_PIPELINE.md).
- [Roadmap](ROADMAP.md), [cartridge design plan](CARTRIDGE_ROADMAP.md) and [GMod plans](GMOD_BACKENDS.md).
- [References](REFERENCES.md), [cartridge references](CARTRIDGE_REFERENCES.md) and [frozen scene inputs](../assets/COMPARISON_REFERENCES.md).

## Historical implementation records

[V2](CARTRIDGE_STREAM_V2.md), [V3](CARTRIDGE_STREAM_V3.md),
[V4](CARTRIDGE_STREAM_V4.md), [V6](CARTRIDGE_STREAM_V6.md),
[V7](CARTRIDGE_STREAM_V7.md), [V8](CARTRIDGE_STREAM_V8.md) and
[V9](CARTRIDGE_STREAM_V9.md) retain their original measurements and release
context. V5 is described in the [main renderer history](../README.md#what-v5-optimizes).
The [cartridge pipeline](CARTRIDGE_PIPELINE.md) and [scene guide](CARTRIDGE_SCENES.md)
include clearly separated historical scaffold/V4 details.

`UPGRADING_0.6.*` files are historical upgrade records, not current installation
instructions. Historical binary/report paths may require their original release
or the optional sibling archive; they are not promises of files in this checkout.
