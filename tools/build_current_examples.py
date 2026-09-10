#!/usr/bin/env python3
"""Rebuild the current stable standalone examples and original menu/HiFi carts.

For every release target plus validation and packaging, use COMPILE-RELEASE.sh.
The preserved v1 recipe is tools/build_v1_release_examples.py.
"""
from build_hors_v2_examples import main

if __name__ == '__main__':
    main()
