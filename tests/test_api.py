"""
DAR API test suite — aligned to openapi-dar.yaml v0.0.13
Uses real spec schema: controller-arrangement, identity-record-ref,
shared-notice/notices, per-controller compliance fields.

Run: pytest tests/ -v
"""
import base64
import hashlib
import json
from unittest.mock import patch

import pytest

from app import db as database
from app.factory import create_app

# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def app():
    with patch.object(database, 'init_db'):
        application = create_app()
    application.config['TESTING'] = True
    return application

@pytest.fixture
def client(app):
    return app.test_client()

# ── constants ─────────────────────────────────────────────────────────────────

ACCOUNT_ID = 'test_account'
SECRET_KEY  = 'test-secret'
DUID        = 'duid_testorg123456789012'
IR          = 'ir_a3c5e7f9b1d3a3c5e7f9b1d3'
AK          = 'ak_aabbcc112233445566778899'

MOCK_ACCOUNT = {
    '_id': ACCOUNT_ID, 'type': 'account', 'duid': DUID, 'role': 'data_user',
    'display_name': 'Test Org', 'callback_urls': [], 'contact_url': 'https://test.com',
    'status': 'active', 'registered_at': '2024-01-01T00:00:00Z',
    'data_types_supported': ['HH-CONSUMPTION'],
    'secret_hash': hashlib.sha256(SECRET_KEY.encode()).hexdigest(),
}
ADMIN_ACCOUNT = {**MOCK_ACCOUNT, 'role': 'admin',
                  'duid': 'duid_admin000000000000000'}
DCC_ACCOUNT   = {**MOCK_ACCOUNT, 'role': 'dcc',
                  'duid': 'duid_dcc000000000000000000'}
DP_ACCOUNT    = {**MOCK_ACCOUNT, 'role': 'data_provider',
                  'duid': 'duid_dp0000000000000000000'}

MOCK_IR = {
    '_id': IR, 'ir': IR, 'type': 'identity_record', 'duid': DUID,
    'mpxn': '1234567890123', 'created_at': '2024-01-01T00:00:00Z',
    'pii_principal': {'mpxn': '1234567890123', 'move-in-date': '2022-01-01'},
    'expressed_by': 'data-subject', 'principal_verification': None,
    'email_hash': None, 'has_email': False, 'credentials': [],
    'anonymised_at': None, 'pending_reidentify_tokens': {},
}

MOCK_RECORD = {
    '_id': AK, 'type': 'access_record', 'ak': AK, 'duid': DUID,
    'mpxn': '1234567890123', 'identity_record_ref': IR,
    'state': 'ACTIVE', 'created_at': '2024-01-01T00:00:00Z',
    'updated_at': '2024-01-01T00:00:00Z',
    'payload': {
        'record-metadata': {
            'schema-version': '1.0', 'record-identifier': AK,
            'created-at': '2024-01-01T00:00:00Z',
            'controller-arrangement': {
                'arrangement-type': 'sole',
                'controllers': [{'name': 'Test Co', 'role': 'sole',
                                  'contact-url': 'https://test.com'}],
            },
            'identity-record-ref': IR,
        },
        'notice': {'shared-notice': {'terms-url': 'https://test.com/p',
                                      'notice-version': 'v1'}},
        'processing': {'legal-basis': 'uk-consent', 'purpose': 'Test',
                        'data-types': ['HH-CONSUMPTION']},
        'access-event': {
            'state': 'ACTIVE', 'registered-at': '2024-01-01T00:00:00Z',
            'expiry': '2027-01-01T00:00:00Z',
            'controller-reference': 'REF-001',
            'consent': {'consent-type': 'expressed-consent',
                        'method': 'Explicit web checkbox'},
        },
    },
    'supersedes': None,
}

MOCK_DISC = {
    'type': 'discovered_record', 'ak': 'ak_disc000000000000000000',
    'state': 'DISCOVERED', 'mpxn': '1234567890123',
    'organisation_name': 'Acme', 'organisation_reference': 'ORG-001',
    'source_reference': 'SRC-001', 'first_seen': '2024-01-01T00:00:00Z',
    'last_seen': '2024-06-01T00:00:00Z', 'data_types_observed': ['HH-CONSUMPTION'],
    'superseded_by': None,
}

MOCK_WH = {
    'wid': 'wid_aabbcc112233445566778899', 'duid': DUID,
    'callback_url': 'https://example.com/wh', 'alert_email': 'ops@example.com',
    'notify_days_before': 30, 'event_types': ['consent.expiring'],
    'signing_secret': 'whsec_test', 'active': True,
    'created_at': '2024-01-01T00:00:00Z',
}

# Spec-compliant request payloads
CONSENT_PAYLOAD = {
    'record-metadata': {
        'schema-version': '1.0',
        'controller-arrangement': {
            'arrangement-type': 'sole',
            'controllers': [{'name': 'Test Co', 'role': 'sole',
                              'contact-url': 'https://test.com/contact',
                              'privacy-rights-url': 'https://test.com/rights'}],
        },
        'identity-record-ref': IR,
    },
    'notice': {'shared-notice': {'terms-url': 'https://test.com/p',
                                  'notice-version': 'v1'}},
    'processing': {'legal-basis': 'uk-consent', 'purpose': 'Test',
                   'data-types': ['HH-CONSUMPTION']},
    'access-event': {
        'state': 'ACTIVE', 'registered-at': '2024-01-01T00:00:00Z',
        'expiry': '2027-01-01T00:00:00Z',
        'consent': {'consent-type': 'expressed-consent',
                    'method': 'Explicit web checkbox'},
    },
}

LI_PAYLOAD = {
    'record-metadata': {
        'schema-version': '1.0',
        'controller-arrangement': {
            'arrangement-type': 'sole',
            'controllers': [{'name': 'Grid Co', 'role': 'sole',
                              'contact-url': 'https://grid.com/contact',
                              'privacy-rights-url': 'https://grid.com/rights',
                              'lia-reference': 'LIA-001'}],
        },
        'identity-record-ref': IR,
    },
    'notice': None,
    'processing': {'legal-basis': 'uk-legitimate-interests',
                   'purpose': 'Load balancing', 'data-types': ['HH-CONSUMPTION']},
    'access-event': {
        'state': 'ACTIVE', 'registered-at': '2024-01-01T00:00:00Z',
        'expiry': '2026-01-01T00:00:00Z', 'consent': None,
    },
}

# ── helpers ───────────────────────────────────────────────────────────────────

def basic_header(secret=SECRET_KEY):
    creds = base64.b64encode(f'{ACCOUNT_ID}:{secret}'.encode()).decode()
    return {'Authorization': f'Basic {creds}'}

def bearer(token):
    return {'Authorization': f'Bearer {token}'}

def get_token(client, account=None):
    acc = account or MOCK_ACCOUNT
    with patch.object(database, 'verify_account', return_value=True), \
         patch.object(database, 'get_account', return_value=acc):
        r = client.get('/v1/auth/token', headers=basic_header())
    assert r.status_code == 200
    return r.get_json()['bearer-token']


# ── Authentication ────────────────────────────────────────────────────────────

class TestAuth:
    def test_no_header_401(self, client):
        assert client.get('/v1/auth/token').status_code == 401

    def test_bad_credentials_401(self, client):
        with patch.object(database, 'verify_account', return_value=False):
            assert client.get('/v1/auth/token',
                              headers=basic_header('wrong')).status_code == 401

    def test_success_200(self, client):
        token = get_token(client)
        assert token.startswith('eyJ')

    def test_response_shape(self, client):
        token = get_token(client)
        with patch.object(database, 'verify_account', return_value=True), \
             patch.object(database, 'get_account', return_value=MOCK_ACCOUNT):
            r = client.get('/v1/auth/token', headers=basic_header())
        d = r.get_json()
        assert 'bearer-token' in d
        assert d['expires'] == 7200


# ── Identity Records ──────────────────────────────────────────────────────────

class TestIdentityRecords:
    def test_create_201(self, client):
        token = get_token(client)
        with patch.object(database, 'create_identity_record',
                          return_value=(MOCK_IR, None)):
            r = client.post('/v1/identity-records',
                            json={'pii-principal': {'mpxn': '1234567890123',
                                                    'move-in-date': '2022-01-01'},
                                  'expressed-by': 'data-subject',
                                  'principal-verification': None},
                            headers=bearer(token))
        assert r.status_code == 201
        d = r.get_json()
        assert d['ir'] == IR
        assert 'Location' in r.headers
        assert d['passkey-registration-redirect'] is None

    def test_create_with_passkey(self, client):
        token    = get_token(client)
        redirect = {'redirect-url': 'https://id.central.consent/passkey/register?session=pks_x',
                    'token-ref': 'mlr_aabbcc112233445566778899',
                    'expires-at': '2024-01-01T00:05:00Z', 'return-url': None}
        with patch.object(database, 'create_identity_record',
                          return_value=(MOCK_IR, redirect)):
            r = client.post('/v1/identity-records',
                            json={'pii-principal': {'mpxn': '1234567890123',
                                                    'move-in-date': '2022-01-01'},
                                  'expressed-by': 'data-subject',
                                  'principal-verification': None,
                                  'initiate-passkey-registration': True,
                                  'passkey-return-url': 'https://app.example.com/done'},
                            headers=bearer(token))
        assert r.status_code == 201
        assert r.get_json()['passkey-registration-redirect'] is not None

    def test_create_bad_mpxn_400(self, client):
        token = get_token(client)
        r = client.post('/v1/identity-records',
                        json={'pii-principal': {'mpxn': 'INVALID'},
                              'expressed-by': 'data-subject'},
                        headers=bearer(token))
        assert r.status_code == 400

    def test_create_missing_expressed_by_400(self, client):
        token = get_token(client)
        r = client.post('/v1/identity-records',
                        json={'pii-principal': {'mpxn': '1234567890123',
                                                'move-in-date': '2022-01-01'}},
                        headers=bearer(token))
        assert r.status_code == 400

    def test_create_unauthenticated_401(self, client):
        r = client.post('/v1/identity-records',
                        json={'pii-principal': {'mpxn': '1234567890123',
                                                'move-in-date': '2022-01-01'},
                              'expressed-by': 'data-subject'})
        assert r.status_code == 401

    def test_lookup_by_mpxn_200(self, client):
        token = get_token(client)
        with patch.object(database, 'lookup_identity_records',
                          return_value=[MOCK_IR]):
            r = client.get('/v1/identity-records?mpxn=1234567890123',
                           headers=bearer(token))
        assert r.status_code == 200
        d = r.get_json()
        assert 'identity-records' in d
        assert len(d['identity-records']) == 1

    def test_lookup_no_params_400(self, client):
        token = get_token(client)
        assert client.get('/v1/identity-records',
                          headers=bearer(token)).status_code == 400

    def test_get_200(self, client):
        token = get_token(client)
        with patch.object(database, 'get_identity_record', return_value=MOCK_IR):
            r = client.get(f'/v1/identity-records/{IR}', headers=bearer(token))
        assert r.status_code == 200
        d = r.get_json()['identity-record']
        assert 'has-email' in d
        assert 'credentials' in d
        assert 'email' not in d          # plaintext email never returned
        assert 'email_hash' not in d     # internal field never exposed

    def test_get_not_found_404(self, client):
        token = get_token(client)
        with patch.object(database, 'get_identity_record', return_value=None):
            assert client.get(f'/v1/identity-records/{IR}',
                              headers=bearer(token)).status_code == 404

    def test_anonymise_200(self, client):
        token = get_token(client)
        anon = {**MOCK_IR, 'anonymised_at': '2025-01-01T00:00:00Z',
                'pii_principal': None}
        with patch.object(database, 'anonymise_identity_record',
                          return_value=(anon, '')):
            r = client.delete(f'/v1/identity-records/{IR}',
                              headers=bearer(token))
        assert r.status_code == 200
        assert 'anonymised-at' in r.get_json()

    def test_anonymise_active_records_409(self, client):
        token = get_token(client)
        with patch.object(database, 'anonymise_identity_record',
                          return_value=(None, 'CONFLICT')):
            assert client.delete(f'/v1/identity-records/{IR}',
                                 headers=bearer(token)).status_code == 409

    def test_remove_credential_204(self, client):
        token = get_token(client)
        with patch.object(database, 'remove_passkey_credential', return_value=True):
            r = client.delete(
                f'/v1/identity-records/{IR}/credentials/cred_abc123def456abc123def456',
                headers=bearer(token))
        assert r.status_code == 204

    def test_remove_credential_not_found_404(self, client):
        token = get_token(client)
        with patch.object(database, 'remove_passkey_credential', return_value=False):
            assert client.delete(
                f'/v1/identity-records/{IR}/credentials/cred_abc123def456abc123def456',
                headers=bearer(token)).status_code == 404

    def test_reidentify_magic_link_200(self, client):
        token = get_token(client)
        result = {'method': 'magic-link',
                  'magic-link': {'dispatched-to': 'c*@e.com',
                                 'expires-at': '2024-01-01T00:15:00Z',
                                 'token-ref': 'mlr_aabbcc112233445566778899',
                                 'redirect-url': None},
                  'passkey': None}
        with patch.object(database, 'initiate_reidentify',
                          return_value=(result, '')):
            r = client.post(f'/v1/identity-records/{IR}/re-identify',
                            json={'method': 'magic-link'},
                            headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['magic-link'] is not None
        assert r.get_json()['passkey'] is None

    def test_reidentify_no_email_422(self, client):
        token = get_token(client)
        with patch.object(database, 'initiate_reidentify',
                          return_value=(None, 'NO_EMAIL')):
            assert client.post(f'/v1/identity-records/{IR}/re-identify',
                               json={'method': 'magic-link'},
                               headers=bearer(token)).status_code == 422

    def test_reidentify_anonymised_409(self, client):
        token = get_token(client)
        with patch.object(database, 'initiate_reidentify',
                          return_value=(None, 'ANONYMISED')):
            assert client.post(f'/v1/identity-records/{IR}/re-identify',
                               json={'method': 'magic-link'},
                               headers=bearer(token)).status_code == 409

    def test_poll_200(self, client):
        token = get_token(client)
        with patch.object(database, 'poll_reidentify',
                          return_value=({'method': 'magic-link',
                                         'status': 'pending',
                                         'confirmed-at': None}, '')):
            r = client.get(
                f'/v1/identity-records/{IR}/re-identify/mlr_aabbcc112233445566778899',
                headers=bearer(token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['status'] == 'pending'
        assert d['confirmed-at'] is None


# ── Access Records ────────────────────────────────────────────────────────────

class TestCreateAccessRecord:
    def test_consent_sole_201(self, client):
        token = get_token(client)
        with patch.object(database, 'create_access_record',
                          return_value=MOCK_RECORD), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post('/v1/access-records', json=CONSENT_PAYLOAD,
                            headers=bearer(token))
        assert r.status_code == 201
        assert 'Location' in r.headers
        assert r.get_json()['access-token']['key'] == AK

    def test_consent_joint_201(self, client):
        token = get_token(client)
        joint = json.loads(json.dumps(CONSENT_PAYLOAD))
        joint['record-metadata']['controller-arrangement'] = {
            'arrangement-type': 'joint',
            'art26-reference':  'JCA-2024-001',
            'controllers': [
                {'name': 'Co A', 'role': 'lead',
                 'contact-url': 'https://a.com',
                 'privacy-rights-url': 'https://a.com/rights'},
                {'name': 'Co B', 'role': 'joint',
                 'contact-url': 'https://b.com'},
            ],
        }
        joint['notice'] = {
            'notices': [
                {'controller-name': 'Co A', 'terms-url': 'https://a.com/p',
                 'notice-version': 'v1'},
                {'controller-name': 'Co B', 'terms-url': 'https://b.com/p',
                 'notice-version': 'v1'},
            ]
        }
        with patch.object(database, 'create_access_record',
                          return_value=MOCK_RECORD), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post('/v1/access-records', json=joint,
                            headers=bearer(token))
        assert r.status_code == 201

    def test_legitimate_interests_201(self, client):
        token = get_token(client)
        with patch.object(database, 'create_access_record',
                          return_value=MOCK_RECORD), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post('/v1/access-records', json=LI_PAYLOAD,
                            headers=bearer(token))
        assert r.status_code == 201

    def test_missing_controller_arrangement_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(CONSENT_PAYLOAD))
        del bad['record-metadata']['controller-arrangement']
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_missing_identity_record_ref_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(CONSENT_PAYLOAD))
        del bad['record-metadata']['identity-record-ref']
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_invalid_ir_format_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(CONSENT_PAYLOAD))
        bad['record-metadata']['identity-record-ref'] = 'not-an-ir'
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_consent_without_notice_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(CONSENT_PAYLOAD))
        bad['notice'] = None
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_non_consent_with_notice_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(LI_PAYLOAD))
        bad['notice'] = {'shared-notice': {'terms-url': 'https://x.com',
                                            'notice-version': 'v1'}}
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_joint_without_art26_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(CONSENT_PAYLOAD))
        bad['record-metadata']['controller-arrangement'] = {
            'arrangement-type': 'joint',
            'controllers': [
                {'name': 'A', 'role': 'lead', 'contact-url': 'https://a.com'},
                {'name': 'B', 'role': 'joint', 'contact-url': 'https://b.com'},
            ],
        }
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_invalid_legal_basis_400(self, client):
        token = get_token(client)
        bad   = json.loads(json.dumps(CONSENT_PAYLOAD))
        bad['processing']['legal-basis'] = 'not-valid'
        assert client.post('/v1/access-records', json=bad,
                           headers=bearer(token)).status_code == 400

    def test_unauthenticated_401(self, client):
        assert client.post('/v1/access-records',
                           json=CONSENT_PAYLOAD).status_code == 401


class TestReplaceAccessRecord:
    def test_replace_active_200(self, client):
        token = get_token(client)
        with patch.object(database, 'replace_access_record',
                          return_value=(MOCK_RECORD, '')), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.put(f'/v1/access-records/{AK}', json=CONSENT_PAYLOAD,
                           headers=bearer(token))
        assert r.status_code == 200

    def test_replace_revoked_409(self, client):
        token = get_token(client)
        with patch.object(database, 'replace_access_record',
                          return_value=(None, 'CONFLICT')):
            assert client.put(f'/v1/access-records/{AK}', json=CONSENT_PAYLOAD,
                              headers=bearer(token)).status_code == 409

    def test_replace_not_found_404(self, client):
        token = get_token(client)
        with patch.object(database, 'replace_access_record',
                          return_value=(None, 'NOT_FOUND')):
            assert client.put(f'/v1/access-records/{AK}', json=CONSENT_PAYLOAD,
                              headers=bearer(token)).status_code == 404

    def test_invalid_payload_400(self, client):
        token = get_token(client)
        assert client.put(f'/v1/access-records/{AK}', json={},
                          headers=bearer(token)).status_code == 400


class TestRevokeAccessRecord:
    def _revoked(self):
        return {**MOCK_RECORD, 'state': 'REVOKED',
                'revoked_at': '2025-01-01T00:00:00Z'}

    def test_revoke_200(self, client):
        token = get_token(client)
        with patch.object(database, 'revoke_access_record',
                          return_value=self._revoked()), \
             patch.object(database, 'write_audit', return_value={}), \
             patch('app.routes.data_users.deliver_event') as mock_ev:
            r = client.delete(f'/v1/access-records/{AK}',
                              headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['ak'] == AK
        assert 'revoked-at' in r.get_json()
        mock_ev.assert_called_once()

    def test_revoke_with_reason_200(self, client):
        token = get_token(client)
        with patch.object(database, 'revoke_access_record',
                          return_value=self._revoked()), \
             patch.object(database, 'write_audit', return_value={}), \
             patch('app.routes.data_users.deliver_event'):
            r = client.delete(
                f'/v1/access-records/{AK}?reason=customer-request',
                headers=bearer(token))
        assert r.status_code == 200

    def test_invalid_reason_400(self, client):
        token = get_token(client)
        assert client.delete(f'/v1/access-records/{AK}?reason=nonsense',
                             headers=bearer(token)).status_code == 400

    def test_not_found_404(self, client):
        token = get_token(client)
        with patch.object(database, 'revoke_access_record', return_value=None):
            assert client.delete(f'/v1/access-records/{AK}',
                                 headers=bearer(token)).status_code == 404

    def test_unauthenticated_401(self, client):
        assert client.delete(f'/v1/access-records/{AK}').status_code == 401


class TestVerifyAccess:
    def test_verify_200_no_auth_required(self, client):
        with patch.object(database, 'verify_access_record',
                          return_value=MOCK_RECORD):
            r = client.get(f'/v1/access-records/{AK}')
        assert r.status_code == 200
        rec = r.get_json()['access-record']
        # No PII — identity-record-ref is present but pii-principal is not
        assert 'pii-principal' not in str(rec)
        assert rec['record-metadata']['identity-record-ref'] == IR

    def test_not_found_404(self, client):
        with patch.object(database, 'verify_access_record', return_value=None):
            assert client.get(f'/v1/access-records/{AK}').status_code == 404


class TestListAccessRecords:
    def test_list_returns_summary_shape(self, client):
        token = get_token(client)
        with patch.object(database, 'list_records_for_mpxn',
                          return_value=[MOCK_RECORD, MOCK_DISC]):
            r = client.get('/v1/meter-points/1234567890123/access-records',
                           headers=bearer(token))
        assert r.status_code == 200
        recs = r.get_json()['access-records']
        assert len(recs) == 2

        full = next(x for x in recs if x['state'] == 'ACTIVE')
        disc = next(x for x in recs if x['state'] == 'DISCOVERED')

        # Full record summary fields
        assert full['lead-controller-name'] == 'Test Co'
        assert full['arrangement-type'] == 'sole'
        assert full['controller-count'] == 1
        assert full['discovered-access'] is None

        # Discovered record fields
        assert disc['lead-controller-name'] is None
        assert disc['arrangement-type'] is None
        assert disc['discovered-access'] is not None
        assert disc['discovered-access']['organisation-name'] == 'Acme'

    def test_invalid_state_filter_400(self, client):
        token = get_token(client)
        assert client.get('/v1/meter-points/1234567890123/access-records?state=INVALID',
                          headers=bearer(token)).status_code == 400

    def test_invalid_basis_filter_400(self, client):
        token = get_token(client)
        assert client.get('/v1/meter-points/1234567890123/access-records?legal-basis=bad',
                          headers=bearer(token)).status_code == 400

    def test_unauthenticated_401(self, client):
        assert client.get(
            '/v1/meter-points/1234567890123/access-records').status_code == 401


# ── Data User Directory ───────────────────────────────────────────────────────

class TestGetDataUser:
    def test_200(self, client):
        token = get_token(client)
        with patch.object(database, 'get_account_by_duid',
                          return_value=MOCK_ACCOUNT):
            r = client.get(f'/v1/data-users/{DUID}', headers=bearer(token))
        assert r.status_code == 200
        d = r.get_json()['data-user']
        assert d['duid'] == DUID
        assert 'display-name' in d
        assert 'status' in d
        assert 'contact-url' in d
        assert 'data-types-supported' in d

    def test_not_found_404(self, client):
        token = get_token(client)
        with patch.object(database, 'get_account_by_duid', return_value=None):
            assert client.get('/v1/data-users/duid_unknown000000000000000',
                              headers=bearer(token)).status_code == 404


# ── Webhooks ──────────────────────────────────────────────────────────────────

class TestWebhooks:
    def test_list_200(self, client):
        token = get_token(client)
        with patch.object(database, 'list_webhooks', return_value=[MOCK_WH]):
            r = client.get('/v1/webhooks', headers=bearer(token))
        assert r.status_code == 200
        wh = r.get_json()['webhooks'][0]
        # Spec field names
        assert 'callback-url' in wh
        assert 'alert-email' in wh
        assert 'notify-days-before' in wh
        assert 'url' not in wh      # old non-spec field must not appear

    def test_create_201(self, client):
        token = get_token(client)
        with patch.object(database, 'get_webhook_by_callback_url',
                          return_value=None), \
             patch.object(database, 'create_webhook', return_value=MOCK_WH):
            r = client.post('/v1/webhooks',
                            json={'callback-url': 'https://example.com/wh',
                                  'alert-email':  'ops@example.com'},
                            headers=bearer(token))
        assert r.status_code == 201
        assert 'signing-secret' in r.get_json()

    def test_non_https_400(self, client):
        token = get_token(client)
        assert client.post('/v1/webhooks',
                           json={'callback-url': 'http://example.com',
                                 'alert-email': 'ops@x.com'},
                           headers=bearer(token)).status_code == 400

    def test_missing_alert_email_400(self, client):
        token = get_token(client)
        assert client.post('/v1/webhooks',
                           json={'callback-url': 'https://x.com/wh'},
                           headers=bearer(token)).status_code == 400

    def test_duplicate_callback_url_409(self, client):
        token = get_token(client)
        with patch.object(database, 'get_webhook_by_callback_url',
                          return_value=MOCK_WH):
            assert client.post('/v1/webhooks',
                               json={'callback-url': 'https://example.com/wh',
                                     'alert-email': 'ops@x.com'},
                               headers=bearer(token)).status_code == 409

    def test_delete_204(self, client):
        token = get_token(client)
        with patch.object(database, 'delete_webhook', return_value=True):
            r = client.delete(f'/v1/webhooks/{MOCK_WH["wid"]}',
                              headers=bearer(token))
        assert r.status_code == 204

    def test_delete_not_found_404(self, client):
        token = get_token(client)
        with patch.object(database, 'delete_webhook', return_value=False):
            assert client.delete(f'/v1/webhooks/{MOCK_WH["wid"]}',
                                 headers=bearer(token)).status_code == 404

    def test_patch_200(self, client):
        token = get_token(client)
        with patch.object(database, 'update_webhook',
                          return_value=(MOCK_WH, '')):
            r = client.patch(f'/v1/webhooks/{MOCK_WH["wid"]}',
                             json={'notify-days-before': 14},
                             headers=bearer(token))
        assert r.status_code == 200
        assert 'webhook' in r.get_json()

    def test_patch_rotate_secret(self, client):
        token = get_token(client)
        with patch.object(database, 'update_webhook',
                          return_value=(MOCK_WH, 'new_secret_xyz')):
            r = client.patch(f'/v1/webhooks/{MOCK_WH["wid"]}',
                             json={'rotate-secret': True},
                             headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['signing-secret'] == 'new_secret_xyz'


# ── DCC ───────────────────────────────────────────────────────────────────────

class TestDCC:
    def _disc_body(self):
        return {
            'mpxn': '1234567890123',
            'organisation-name': 'Acme',
            'organisation-reference': 'ORG-001',
            'source-reference': 'SRC-001',
            'first-seen': '2024-01-01',
            'data-types-observed': ['HH-CONSUMPTION'],
        }

    def test_submit_discovered_201(self, client):
        token = get_token(client, DCC_ACCOUNT)
        with patch.object(database, 'submit_discovered_record',
                          return_value=(MOCK_DISC, True)):
            r = client.post('/v1/discovered-access', json=self._disc_body(),
                            headers=bearer(token))
        assert r.status_code == 201

    def test_submit_discovered_idempotent_200(self, client):
        token = get_token(client, DCC_ACCOUNT)
        with patch.object(database, 'submit_discovered_record',
                          return_value=(MOCK_DISC, False)):
            r = client.post('/v1/discovered-access', json=self._disc_body(),
                            headers=bearer(token))
        assert r.status_code == 200

    def test_data_user_token_rejected_403(self, client):
        token = get_token(client)
        assert client.post('/v1/discovered-access',
                           json=self._disc_body(),
                           headers=bearer(token)).status_code == 403

    def test_cot_event_201(self, client):
        token = get_token(client, DCC_ACCOUNT)
        cot_doc = {'event_id': 'cot_abc', 'mpxn': '1234567890123',
                   'effective_date': '2025-06-01', 'source_reference': 'DCC-001',
                   'submitted_at': '2025-01-01T00:00:00Z'}
        with patch.object(database, 'submit_cot_event',
                          return_value=(cot_doc, True)), \
             patch.object(database, 'get_active_records_for_mpxn',
                          return_value=[{'ak': AK, 'duid': DUID}]), \
             patch.object(database, 'get_all_webhooks_for_event',
                          return_value=[]):
            r = client.post('/v1/cot-events',
                            json={'mpxn': '1234567890123',
                                  'effective-date': '2025-06-01',
                                  'source-reference': 'DCC-001'},
                            headers=bearer(token))
        assert r.status_code == 201
        d = r.get_json()
        # Spec CotEventResponse fields
        assert d['active-records-affected'] == 1
        assert isinstance(d['data-users-notified'], list)
        assert 'effective-date' in d
        assert 'source-reference' in d

    def test_cot_data_user_rejected_403(self, client):
        token = get_token(client)
        assert client.post('/v1/cot-events',
                           json={'mpxn': '1234567890123',
                                 'effective-date': '2025-06-01',
                                 'source-reference': 'X'},
                           headers=bearer(token)).status_code == 403


# ── Customer Sessions ─────────────────────────────────────────────────────────

class TestCustomerSessions:
    def test_create_201(self, client):
        token = get_token(client)
        session = {'token': 'tok123', 'duid': DUID, 'mpxn': '1234567890123',
                   'return_url': 'https://app.example.com', 'purpose': 'View'}
        with patch.object(database, 'get_data_user_profile',
                          return_value=MOCK_ACCOUNT), \
             patch.object(database, 'create_portal_session',
                          return_value=session):
            r = client.post('/v1/customer-sessions',
                            json={'mpxn': '1234567890123',
                                  'return-url': 'https://app.example.com',
                                  'purpose': 'View access records'},
                            headers=bearer(token))
        assert r.status_code == 201
        d = r.get_json()
        assert 'session-token' in d
        assert 'portal-url' in d
        assert d['expires-in'] == 60

    def test_missing_mpxn_400(self, client):
        token = get_token(client)
        with patch.object(database, 'get_data_user_profile',
                          return_value=MOCK_ACCOUNT):
            assert client.post('/v1/customer-sessions',
                               json={'return-url': 'https://app.example.com',
                                     'purpose': 'Test'},
                               headers=bearer(token)).status_code == 400


# ── Self-Service ──────────────────────────────────────────────────────────────

class TestSelfService:
    def test_get_self_200(self, client):
        token = get_token(client)
        with patch.object(database, 'get_account', return_value=MOCK_ACCOUNT):
            r = client.get('/v1/self', headers=bearer(token))
        assert r.status_code == 200
        d = r.get_json()['account']
        assert d['account-id'] == ACCOUNT_ID
        assert d['duid'] == DUID
        assert 'secret' not in str(d)

    def test_rotate_secret_200(self, client):
        token = get_token(client)
        with patch.object(database, 'get_account', return_value=MOCK_ACCOUNT), \
             patch.object(database, '_put', return_value=MOCK_ACCOUNT), \
             patch.object(database, '_now', return_value='2025-01-01T00:00:00Z'), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post('/v1/self/rotate-secret', headers=bearer(token))
        assert r.status_code == 200
        assert len(r.get_json()['secret-key']) == 64


# ── Admin ─────────────────────────────────────────────────────────────────────

class TestAdmin:
    def test_stats_200(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        stats = {'total_accounts': 3, 'active_accounts': 3, 'total_records': 5,
                 'active_records': 4, 'revoked_records': 1,
                 'total_webhooks': 2, 'active_webhooks': 2}
        with patch.object(database, 'get_account_stats', return_value=stats):
            r = client.get('/v1/admin/stats', headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['total_records'] == 5

    def test_stats_data_user_403(self, client):
        token = get_token(client)
        with patch.object(database, 'get_account_stats', return_value={}):
            assert client.get('/v1/admin/stats',
                              headers=bearer(token)).status_code == 403

    def test_list_accounts_200(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        with patch.object(database, 'list_all_accounts',
                          return_value=[MOCK_ACCOUNT]):
            r = client.get('/v1/admin/accounts', headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['total'] == 1

    def test_create_account_201(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        with patch.object(database, 'get_account', return_value=None), \
             patch.object(database, 'create_account',
                          return_value=MOCK_ACCOUNT), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post('/v1/admin/accounts',
                            json={'account-id': 'new_org',
                                  'secret-key': 'secret123',
                                  'display-name': 'New Org',
                                  'duid': 'duid_neworg123456789012',
                                  'role': 'data_user'},
                            headers=bearer(token))
        assert r.status_code == 201

    def test_create_account_duplicate_409(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        with patch.object(database, 'get_account', return_value=MOCK_ACCOUNT):
            assert client.post('/v1/admin/accounts',
                               json={'account-id': ACCOUNT_ID,
                                     'secret-key': 'x',
                                     'display-name': 'X',
                                     'duid': 'duid_x',
                                     'role': 'data_user'},
                               headers=bearer(token)).status_code == 409

    def test_suspend_200(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        sus = {**MOCK_ACCOUNT, 'status': 'suspended'}
        with patch.object(database, 'suspend_account', return_value=sus), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post(f'/v1/admin/accounts/{ACCOUNT_ID}/suspend',
                            headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['account']['status'] == 'suspended'

    def test_reactivate_200(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        with patch.object(database, 'reactivate_account',
                          return_value=MOCK_ACCOUNT), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post(f'/v1/admin/accounts/{ACCOUNT_ID}/reactivate',
                            headers=bearer(token))
        assert r.status_code == 200

    def test_records_200(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        with patch.object(database, 'list_all_records',
                          return_value=[MOCK_RECORD]):
            r = client.get('/v1/admin/records', headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['total'] == 1
        # Check serialised shape
        rec = r.get_json()['records'][0]
        assert rec['ak'] == AK
        assert rec['lead-controller-name'] == 'Test Co'

    def test_audit_200(self, client):
        token = get_token(client, ADMIN_ACCOUNT)
        events = [{'event_id': 'aud_1', 'account_id': ACCOUNT_ID,
                   'event_type': 'record.created', 'ak': AK,
                   'mpxn': '1234567890123', 'detail': {},
                   'timestamp': '2024-01-01T00:00:00Z'}]
        with patch.object(database, 'list_audit_events', return_value=events):
            r = client.get('/v1/admin/audit', headers=bearer(token))
        assert r.status_code == 200
        assert r.get_json()['total'] == 1


# ── Response envelope ─────────────────────────────────────────────────────────

class TestResponseEnvelope:
    def test_success_has_response_metadata(self, client):
        token = get_token(client)
        with patch.object(database, 'create_access_record',
                          return_value=MOCK_RECORD), \
             patch.object(database, 'write_audit', return_value={}):
            r = client.post('/v1/access-records', json=CONSENT_PAYLOAD,
                            headers=bearer(token))
        meta = r.get_json()['response']
        assert 'timestamp' in meta
        assert meta['transaction-id'].startswith('tid_')
        assert 'resource' in meta

    def test_error_has_error_array(self, client):
        r = client.get('/v1/auth/token')
        d = r.get_json()
        assert 'errors' in d
        assert d['errors'][0]['error-code']
        assert d['errors'][0]['message']


# ── UI static files ───────────────────────────────────────────────────────────

class TestUIServing:
    def test_admin_ui(self, client):
        r = client.get('/admin')
        assert r.status_code == 200
        assert b'DAR Admin' in r.data

    def test_dashboard_ui(self, client):
        r = client.get('/dashboard')
        assert r.status_code == 200
        assert b'DAR Dashboard' in r.data

    def test_portal_ui(self, client):
        r = client.get('/portal')
        assert r.status_code == 200
        assert b'Central Access Register' in r.data

    def test_lib_css(self, client):
        r = client.get('/ui/lib/dar-styles.css')
        assert r.status_code == 200

    def test_lib_api_js(self, client):
        r = client.get('/ui/lib/dar-api.js')
        assert r.status_code == 200

    def test_lib_components_js(self, client):
        r = client.get('/ui/lib/dar-components.js')
        assert r.status_code == 200
