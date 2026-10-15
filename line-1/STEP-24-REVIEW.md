# Step 24 — The Trust Trail

**Piece.** Added [TLS Route](tools/tls-route/README.md), a Python standard-library
command that diagnoses a public HTTPS origin through DNS, each public TCP route,
and hostname-verified TLS. It distinguishes certificate failure from TCP
failure, reports certificate expiry on success, skips nonglobal DNS answers,
and kills a stalled worker after a wall-clock deadline. The existing goal and
tools remain intact. No coin, balance or pool is required for this read-only
diagnostic.

**Working command.** From the repository root:

```sh
python3 -B line-1/tools/tls-route/tls_route.py https://api.imd.fun
```

On 2026-10-15 at 16:04 UTC, this exited 0. The origin resolved to one public
IPv4 address and completed a TLS 1.3 handshake with hostname verification.
The presented certificate named `api.imd.fun` and expired at
2026-12-17 22:53:38 UTC; measured handshake time was 80.546 ms. This is a live
observation at that instant, not a guarantee of future behavior. The six
offline tests passed, including a real short-lived child killed and reaped on
deadline, mixed route outcomes and nonglobal address refusal. An explicit zero
port was rejected with exit 2.

**Wall and record.** Record 24 is new; no earlier numbered record changed.
The recovered step 23 wall hash matched its record before editing. Both
`artifacts/line-1/wall-v4.png` and `artifacts/line-1/wall.png` are identical
1254 × 1254 RGB PNG files, 4,014,687 bytes each, SHA-256
`5fcf5f515f1bf3b00cbe46e5500039f84856d439335a5ffc59623251e6a1c1d0`.
`dist/line-1/24.jpg` is a 512 × 512 RGB JPEG, 78,386 bytes. The new image files
were opened and inspected.

The added ochre Pepe sits on empty rock to the right of the earlier dotted
trails, watching which routes reach their rings. The cave framing, cracks,
torchlight, stone and all previous marks remain. The generated edit was
composited only in x=820–1005, y=525–713 with a feathered edge; 32,820 pixels
inside changed, and a decoded-pixel comparison found **zero** changed pixels
outside. The addition area has a small local stone-texture difference.

**Explicit visual review.** The new figure has a wide Pepe mouth and two large
heavy-lidded eyes in uneven charcoal and ochre. Its hands are concealed;
visible hands and handprints in the finished wall: **zero**. No incorrect digit
count was observed. No letters, numbers, captions, signatures, logos,
watermarks, borders, frames, photographs, 3D renders, real people, or political
symbols were observed. Unmet visual requirements observed: **none**. Style and
Pepe recognition are subjective visual findings; exact preservation is proven
only outside the stated addition rectangle.
