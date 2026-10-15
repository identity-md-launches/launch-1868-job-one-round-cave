"""Offline checks for public-address policy, failure stages and the watchdog."""
import importlib.util
from pathlib import Path
import socket
import ssl
import sys
import unittest


spec = importlib.util.spec_from_file_location('tls_route', Path(__file__).with_name('tls_route.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def answer(address):
    family = socket.AF_INET6 if ':' in address else socket.AF_INET
    sockaddr = (address, 443, 0, 0) if family == socket.AF_INET6 else (address, 443)
    return family, socket.SOCK_STREAM, 0, '', sockaddr


class FakeSocket:
    def __init__(self, failures, calls):
        self.failures, self.calls = failures, calls

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def settimeout(self, seconds):
        self.calls.append(('timeout', seconds))

    def connect(self, sockaddr):
        self.calls.append(('connect', sockaddr[0]))
        if sockaddr[0] in self.failures:
            raise self.failures[sockaddr[0]]


class FakeSecured:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def version(self):
        return 'TLSv1.3'

    def getpeercert(self):
        return {'notAfter': 'Jan  1 00:00:00 2030 GMT',
                'subjectAltName': (('DNS', 'example.com'),)}


class FakeContext:
    def __init__(self, failure=None):
        self.failure = failure
        self.hosts = []

    def wrap_socket(self, raw, server_hostname):
        self.hosts.append(server_hostname)
        if self.failure:
            raise self.failure
        return FakeSecured()


class RouteTests(unittest.TestCase):
    def test_origin_rejects_secret_bearing_and_invalid_urls(self):
        for url in ('http://example.com', 'https://x:y@example.com',
                    'https://example.com/path', 'https://example.com/?token=abc',
                    'https://example.com:0', 'https://example.com:',
                    'https://example.com:65536',
                    'https://example.com/#part', 'https://example.com\n'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                module.origin(url)
        self.assertEqual(module.origin('https://example.com:8443/'), ('example.com', 8443))

    def test_dns_failure_is_reported_without_socket_attempt(self):
        def fail(*_, **__):
            raise socket.gaierror('no DNS answer')
        report = module.diagnose('https://example.com', resolver=fail)
        self.assertFalse(report['ok'])
        self.assertEqual(report['error']['kind'], 'dns')
        self.assertEqual(report['addresses'], [])

    def test_private_answer_is_not_connected(self):
        calls = []
        report = module.diagnose('https://example.com',
            resolver=lambda *_, **__: [answer('127.0.0.1'), answer('10.0.0.1')],
            socket_factory=lambda *args: calls.append(args))
        self.assertFalse(report['ok'])
        self.assertEqual([a['error']['kind'] for a in report['addresses']],
                         ['address_policy', 'address_policy'])
        self.assertEqual(calls, [])

    def test_mixed_routes_identify_tcp_failure_and_verified_tls_success(self):
        calls = []
        context = FakeContext()
        report = module.diagnose('https://example.com', max_addresses=2,
            resolver=lambda *_, **__: [answer('1.1.1.1'), answer('8.8.8.8'), answer('9.9.9.9')],
            socket_factory=lambda *args: FakeSocket({'1.1.1.1': ConnectionRefusedError('refused')}, calls),
            context_factory=lambda: context, now=lambda: 1700000000)
        self.assertTrue(report['ok'])
        self.assertTrue(report['degraded'])
        self.assertTrue(report['more_addresses_omitted'])
        self.assertEqual(report['addresses'][0]['error']['kind'], 'tcp')
        self.assertEqual(report['addresses'][1]['tls_version'], 'TLSv1.3')
        self.assertEqual(report['addresses'][1]['certificate']['dns_names'], ['example.com'])
        self.assertEqual(context.hosts, ['example.com'])
        self.assertEqual([x for x in calls if x[0] == 'connect'],
                         [('connect', '1.1.1.1'), ('connect', '8.8.8.8')])

    def test_certificate_failure_is_distinct_from_tcp(self):
        context = FakeContext(ssl.SSLCertVerificationError('untrusted'))
        report = module.diagnose('https://example.com',
            resolver=lambda *_, **__: [answer('1.1.1.1')],
            socket_factory=lambda *args: FakeSocket({}, []),
            context_factory=lambda: context)
        self.assertFalse(report['ok'])
        self.assertEqual(report['addresses'][0]['error']['kind'], 'certificate')

    def test_deadline_kills_a_stalled_worker(self):
        report, code = module.supervise(
            [sys.executable, '-I', '-B', '-c', 'import time; time.sleep(3)'], 0.05)
        self.assertEqual(code, 1)
        self.assertEqual(report['error']['kind'], 'deadline')


if __name__ == '__main__':
    unittest.main()
