# TLS Route

Diagnose a public HTTPS origin from DNS through TCP connection and verified TLS.
It checks up to four distinct public DNS answers and reports the stage of each
failure, negotiated TLS version and certificate expiry for successful routes.
Python 3.9+ standard library only; no installation.

From the repository root, one command probes the real swarm:

```sh
python3 -B line-1/tools/tls-route/tls_route.py https://api.imd.fun
```

The JSON report exits 0 when at least one address completes a hostname-verified
TLS handshake, 1 when none do or the deadline expires, and 2 for invalid input.
`degraded: true` means some answers failed while at least one succeeded. Failure
kinds distinguish `dns`, `address_policy`, `tcp`, `timeout`, `tls`, and
`certificate`. This probes the origin only; it does not make an HTTP request or
claim that any application path works. Use Endpoint Sentry for HTTP and JSON.

Only global IP addresses are contacted. DNS answers for loopback, private,
link-local, reserved and other nonglobal ranges are reported and skipped. The
parent process kills and reaps a stalled child after `--deadline` (12 seconds by
default), including a DNS stall; no retry occurs. `--per-address` defaults to
two seconds and `--max-addresses` to four. DNS answer order is retained. The
probe uses the running platform's certificate trust store and SNI with the
original hostname. Certificate expiry is an observation of the presented
certificate, not a forecast of renewal. No response body or local report is
saved; no wallet, key, signing, transaction, payment or post is used. Give it
only public, non-secret origins. A URL with a path, query, fragment or userinfo
is refused so credentials cannot appear in the output.

## What happened when tried

On 2026-10-15 at 16:04 UTC the command exited 0. `api.imd.fun` resolved to one
public IPv4 address; its TCP and verified TLS 1.3 handshakes succeeded, and the
presented certificate named `api.imd.fun` with expiry 2026-12-17 22:53:38 UTC.
The measured handshake took 80.546 ms. This is a historical observation; DNS,
routes, certificates and availability can change.

The offline checks use injected DNS/socket/TLS behavior and a real short-lived
child process to verify failure stages, private-address refusal, mixed routes,
certificate errors and killing a stalled worker:

```sh
python3 -B -m unittest discover -s line-1/tools/tls-route -v
```
