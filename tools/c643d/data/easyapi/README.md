# EasyAPI AM/M29F040 V1.4

Original software by Thomas "skoe" Giesel, (c) 2009-2010. The complete original
redistribution notice is retained at the top of `eapi-am29f040.s`. It permits
use, modification and redistribution with attribution/origin conditions.
The toolkit does not claim authorship of EasyAPI. Both source files are unmodified.

Source: <https://github.com/KimJorgensen/easyflash/tree/9278c9f96fc3226047fb816a6090ff70d6c86cde/EasySDK/eapi>

The official EasyFlash developer page refers to the original skoe repository:
<https://skoe.de/easyflash/develdocs/>. The pinned GitHub mirror supplies this
source snapshot. This is the AM/M29F040 driver, not VICE's emulator-only replacement.

`eapi-am29f040-14.bin` is the 768-byte payload, with the two-byte PRG load address
removed. SHA-256:
`032f3f21f2299e2fd96b28dc1a901a6ed19a04f600d446c7a362781b4592f432`.

Rebuild in this directory with ACME (verified with release 0.96.4):

```sh
acme -o eapi.prg eapi-am29f040.s
python -c "from pathlib import Path; p=Path('eapi.prg').read_bytes(); assert len(p)==770 and p[2:6]==b'eapi'; Path('eapi-am29f040-14.bin').write_bytes(p[2:])"
```

Normal toolkit builds use the included, hash-checked binary; ACME is not required.
The payload occupies bank 0 ROMH `$1800-$1aff`. The name structure follows at
`$1b00-$1b17`. These read-only demos do not initialize or call EasyAPI to write flash.
