# Stanford Dragon source

Model data: **Stanford University Computer Graphics Laboratory**.

- [Stanford 3D Scanning Repository](https://graphics.stanford.edu/data/3Dscanrep/)
- [Original Dragon reconstruction archive](https://graphics.stanford.edu/pub/3Dscanrep/dragon/dragon_recon.tar.gz)
- Archive SHA-256: `74ac1d90989c9b1732edee82d57e9ce71452144cf4355f108d8c9c616d28d02f`
- Retrieved 2026-09-12. Included member: `dragon_recon/dragon_vrip_res4.ply`.
- The archive's [original README](source/STANFORD_README.txt) describes its reconstruction and decimation.

Stanford permits research use and free redistribution with acknowledgement. Commercial use or inclusion in a product for sale requires Stanford's permission, subject to its stated scholarly-publication exception. See the repository's current terms. The model and its derivatives are subject to those terms; they are not relicensed as toolkit code.

The official res4 mesh has **5,205 vertices, 15,796 unique edges and 11,102 triangles**. Its compressed PLY is included under `source/`; `prepare_model.py` converts it to `stanford_dragon.obj`. The conversion preserves all coordinate values, vertex order, faces and winding. No further decimation is applied. The highest-resolution PLY in the downloaded archive has 437,645 vertices and 871,414 triangles; these demo carts use res4.

The existing HORS-V3 pipeline centers, scales and projects the mesh, and precomputes viewing orientations. The metallic (grey), red, green and blue appearances use HORS-V3's generated lighting with C64 colour ramps. They are not scanned Stanford textures. `model.json` records the source and converted-model hashes.
