# References / inspiration

The C64 rasterizer work was informed by studying Mark Moxon's documented Elite source and flicker-free patch work:

- https://github.com/markmoxon/elite-source-code-commodore-64
- https://github.com/markmoxon/c64-elite-flicker-free
- https://elite.bbcelite.com/hacks/flicker-free_elite/
- https://elite.bbcelite.com/c64/indexes/subroutines.html

The toolkit does not bundle Elite binaries or source. The project uses the general engineering ideas as reference material: specialized line paths, precomputation, visibility reduction, and careful separation of presentation from drawing.
