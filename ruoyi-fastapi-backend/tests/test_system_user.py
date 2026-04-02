"""
Example: system user list endpoint.
Copy this pattern for your own module tests.
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_user_list_requires_auth(client: httpx.AsyncClient) -> None:
    """Unauthenticated request should be rejected."""
    resp = await client.get('/system/user/list')
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_user_list(client: httpx.AsyncClient, auth_headers: dict) -> None:
    resp = await client.get(
        '/system/user/list',
        headers=auth_headers,
        params={'pageNum': 1, 'pageSize': 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data['code'] == 200
    assert isinstance(data['rows'], list)
    assert isinstance(data['total'], int)
