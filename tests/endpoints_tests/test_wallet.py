import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.parametrize("balance, status_code", [
    (0, 201),
    (100, 201),
    (-100, 422),
], )
async def test_create_wallet(balance, status_code, ac_client: AsyncClient):
    response = await ac_client.post("/api/v1/wallets/", json={"balance": balance})
    assert response.status_code == status_code
    user_data = response.json()
    if status_code == 201:
        return user_data["uuid"]


@pytest.mark.parametrize("balance, status_code", [(100, 201)])
async def test_parallel_deposits(balance, status_code, ac_client: AsyncClient):
    response = await ac_client.post("/api/v1/wallets/", json={"balance": str(balance)})
    assert response.status_code == status_code
    wallet_id = response.json()["uuid"]

    async def deposit():
        response = await ac_client.post(f"/api/v1/wallets/{wallet_id}/deposit",
            json={"uuid": str(wallet_id), "amount": "10.00"})
        await asyncio.sleep(0.01)
        return response

    tasks = [deposit() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    for r in results:
        assert r.status_code == 200

    response = await ac_client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.json()["balance"] == "200.00"



@pytest.fixture(scope="function")
async def created_wallet(ac_client: AsyncClient):
    """Создается кошелек для тестов"""
    response = await ac_client.post("/api/v1/wallets/", json={"balance": 100})
    assert response.status_code == 201
    wallet_data = response.json()
    return wallet_data["uuid"]


@pytest.mark.parametrize("status_code", [200], )
async def test_get_wallet(created_wallet, status_code, ac_client: AsyncClient):
    response = await ac_client.get(f"/api/v1/wallets/{created_wallet}")
    assert response.status_code == status_code
    data = response.json()
    assert data["uuid"] == created_wallet


@pytest.mark.parametrize("amount, status_code", [
    (500, 200),
    (-100, 422),
], )
async def test_deposit(created_wallet, amount, status_code, ac_client: AsyncClient):
    response = await ac_client.post(f"/api/v1/wallets/{created_wallet}/deposit", json={
        "uuid": created_wallet,
        "amount": amount
    })
    assert response.status_code == status_code


@pytest.mark.parametrize("amount, status_code", [
    (100000, 400),
    (100, 200),
], )
async def test_withdraw(created_wallet, amount, status_code, ac_client: AsyncClient):
    response = await ac_client.post(f"/api/v1/wallets/{created_wallet}/withdraw", json={
        "uuid": created_wallet,
        "amount": amount
    })
    assert response.status_code == status_code
