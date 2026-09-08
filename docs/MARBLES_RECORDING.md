# Marbles recording start

After examples-cleanup-02, run `python perf/marbles_wait_for_space.py`.
The accepted main cart waits on its existing SPACE to start screen indefinitely.
Start recording in VICE, focus the emulator, then press SPACE to begin the intro.

This changes only the startup timeout instruction (DEX/BNE to CLC/BCC). Animation data,
addresses and labels are unchanged. The automatic-start cart is backed up under
`examples/cart_marbles/history/startup-auto/`. Repeated application is harmless.
New hors-render-v1 scene builds also wait for SPACE. Historical renderer build
screens retain their previous behaviour. Automated end-to-end playback tests
must press SPACE or bypass this startup screen. Apply this after cleanup; running
the old promotion script again can restore the automatic-start copy.
