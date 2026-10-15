#!/usr/bin/env python3
"""Find whether a public HTTPS origin fails at DNS, TCP, or verified TLS."""

import argparse
import datetime as dt
import ipaddress
import json
import math
import socket
import ssl
import subprocess
import sys
import time
from urllib.parse import urlsplit


def origin(value):
    """Accept only an ASCII public HTTPS origin, not a path or secret-bearing URL."""
    if any(ord(char) <= 32 or ord(char) == 127 for char in value):
        raise ValueError('URL contains whitespace or control characters')
    value.encode('ascii')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.path not in ('', '/')
            or parsed.query or parsed.fragment or parsed.netloc.endswith(':')):
        raise ValueError('give an HTTPS origin without credentials, path, query or fragment')
    port = 443 if parsed.port is None else parsed.port
    if not 1 <= port <= 65535:
        raise ValueError('port must be between 1 and 65535')
    return parsed.hostname, port


def _certificate_details(cert, now):
    end = ssl.cert_time_to_seconds(cert['notAfter'])
    expiry = dt.datetime.fromtimestamp(end, dt.timezone.utc)
    names = cert.get('subjectAltName', ())
    return {
        'expires_at': expiry.isoformat(),
        'days_remaining': round((end - now) / 86400, 2),
        'dns_names': [value for kind, value in names if kind == 'DNS'][:12],
    }


def diagnose(url, per_address=2.0, max_addresses=4, resolver=None,
             socket_factory=None, context_factory=None, now=None):
    """Probe each public DNS answer once. Dependencies can be supplied for offline tests."""
    host, port = origin(url)
    resolver = resolver or socket.getaddrinfo
    socket_factory = socket_factory or socket.socket
    context_factory = context_factory or ssl.create_default_context
    now = now or time.time
    report = {'schema': 'tls-route/v1', 'origin': url,
              'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'ok': False, 'degraded': False, 'addresses': [],
              'limits': {'per_address_seconds': per_address, 'max_addresses': max_addresses}}
    try:
        answers = resolver(host, port, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError) as error:
        report['error'] = {'kind': 'dns', 'message': str(error)}
        return report

    seen = set()
    for family, kind, protocol, _, sockaddr in answers:
        if family not in (socket.AF_INET, socket.AF_INET6):
            continue
        address = sockaddr[0]
        if address in seen:
            continue
        seen.add(address)
        if len(report['addresses']) >= max_addresses:
            report['more_addresses_omitted'] = True
            break
        attempt = {'address': address, 'family': 'IPv6' if family == socket.AF_INET6 else 'IPv4',
                   'ok': False}
        report['addresses'].append(attempt)
        try:
            if not ipaddress.ip_address(address).is_global:
                attempt['error'] = {'kind': 'address_policy',
                                    'message': 'DNS answer is not a public address'}
                continue
        except ValueError:
            attempt['error'] = {'kind': 'dns', 'message': 'invalid DNS answer'}
            continue
        stage = 'tcp'
        started = time.monotonic()
        try:
            with socket_factory(family, socket.SOCK_STREAM, protocol) as raw:
                raw.settimeout(per_address)
                raw.connect(sockaddr)
                stage = 'tls'
                # The platform trust store validates the chain and hostname.
                context = context_factory()
                with context.wrap_socket(raw, server_hostname=host) as secured:
                    attempt['tls_version'] = secured.version()
                    attempt['certificate'] = _certificate_details(secured.getpeercert(), now())
                    attempt['ok'] = True
        except (OSError, ValueError, KeyError) as error:
            if isinstance(error, ssl.SSLCertVerificationError):
                kind = 'certificate'
            elif isinstance(error, ssl.SSLError):
                kind = 'tls'
            elif isinstance(error, (socket.timeout, TimeoutError)):
                kind = 'timeout'
            else:
                kind = stage
            attempt['error'] = {'kind': kind, 'message': str(error)}
        attempt['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)

    if not report['addresses']:
        report['error'] = {'kind': 'dns', 'message': 'no usable IPv4 or IPv6 answers'}
    report['ok'] = any(item['ok'] for item in report['addresses'])
    report['degraded'] = report['ok'] and any(not item['ok'] for item in report['addresses'])
    return report


def supervise(command, deadline):
    """Cover DNS stalls as well as socket work; discard partial child output."""
    started = time.monotonic()
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as error:
        return {'ok': False, 'error': {'kind': 'worker_start', 'message': str(error)}}, 1
    try:
        stdout, stderr = child.communicate(timeout=max(0, deadline - (time.monotonic() - started)))
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate()
        return {'ok': False, 'error': {'kind': 'deadline',
                'message': 'Probe exceeded wall-clock deadline; worker killed without retry'}}, 1
    if child.returncode not in (0, 1):
        return {'ok': False, 'error': {'kind': 'worker',
                'message': stderr.decode('utf-8', 'replace')[:500]}}, 1
    try:
        report = json.loads(stdout)
        if not isinstance(report, dict) or type(report.get('ok')) is not bool:
            raise ValueError('missing boolean ok')
        if report.get('schema') != 'tls-route/v1' or report['ok'] != (child.returncode == 0):
            raise ValueError('inconsistent worker report')
    except (ValueError, UnicodeError) as error:
        return {'ok': False, 'error': {'kind': 'worker_protocol', 'message': str(error)}}, 1
    return report, child.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('url', help='public HTTPS origin, such as https://api.imd.fun')
    parser.add_argument('--deadline', type=float, default=12,
                        help='parent wall-clock budget, seconds (default 12)')
    parser.add_argument('--per-address', type=float, default=2,
                        help='TCP/TLS timeout for each DNS answer (default 2)')
    parser.add_argument('--max-addresses', type=int, default=4,
                        help='maximum distinct DNS answers to probe (default 4)')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        origin(args.url)
        if not math.isfinite(args.deadline) or not 0 < args.deadline <= 120:
            raise ValueError('deadline must be finite and in (0, 120] seconds')
        if not math.isfinite(args.per_address) or not 0 < args.per_address <= 30:
            raise ValueError('per-address must be finite and in (0, 30] seconds')
        if not 1 <= args.max_addresses <= 8:
            raise ValueError('max-addresses must be in 1..8')
    except (ValueError, UnicodeError) as error:
        parser.error(str(error))
    if args.worker:
        report = diagnose(args.url, args.per_address, args.max_addresses)
        code = 0 if report['ok'] else 1
    else:
        command = [sys.executable, '-I', '-B', __file__, args.url, '--worker',
                   '--deadline', str(args.deadline), '--per-address', str(args.per_address),
                   '--max-addresses', str(args.max_addresses)]
        report, code = supervise(command, args.deadline)
        if 'schema' not in report:
            report['schema'] = 'tls-route/v1'
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
