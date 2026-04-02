"""
Test fixtures for ruoyi-fastapi-scaffold.

Tests run against a live dev server. Start it before running tests:

    cd ruoyi-fastapi-backend && python app.py --env=dev

Environment variables:
    TEST_BASE_URL   default: http://127.0.0.1:9099/dev-api
    TEST_USERNAME   default: admin
    TEST_PASSWORD   default: admin123
"""
import os

import pytest
import httpx

BASE_URL      = os.getenv('TEST_BASE_URL', 'http://127.0.0.1:9099/dev-api')
TEST_USERNAME = os.getenv('TEST_USERNAME', 'admin')
TEST_PASSWORD = os.getenv('TEST_PASSWORD', 'admin123')


@pytest.fixture(scope='session')
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope='session')
async def auth_token(client: httpx.AsyncClient) -> str:
    """Log in once per session, return the bearer token."""
    resp = await client.post('/login', json={
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD,
    })
    assert resp.status_code == 200, f'Login failed: {resp.text}'
    return resp.json()['data']['token']


@pytest.fixture(scope='session')
def auth_headers(auth_token: str) -> dict:
    return {'Authorization': f'Bearer {auth_token}'}
