import asyncio

from decimal import Decimal

import pytest
from httpx import AsyncClient
import logging
logger = logging.getLogger(__name__)

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


# ------ Test transfer -------


import asyncio
from decimal import Decimal
import uuid as uuid_pkg  # Import uuid module

import pytest
from httpx import AsyncClient


# Assume ac_client fixture is defined elsewhere similar to your example
# Assume API base URL is implicitly handled by ac_client

# --- Fixtures ---

@pytest.fixture(scope="function")
async def wallet_factory(ac_client: AsyncClient):
    """Factory fixture to create wallets for tests."""
    created_wallets = []

    async def _create_wallet(initial_balance: Decimal | str = "0.00"):
        response = await ac_client.post("/api/v1/wallets/", json={"balance": str(initial_balance)})
        assert response.status_code == 201, f"Failed to create wallet: {response.text}"
        wallet_data = response.json()
        wallet_uuid = wallet_data["uuid"]
        created_wallets.append(wallet_uuid)  # Keep track if cleanup is needed
        return wallet_uuid, Decimal(wallet_data["balance"])

    yield _create_wallet

    # Optional: Cleanup - delete created wallets if necessary
    # for wallet_id in created_wallets:
    #     await ac_client.delete(f"/api/v1/wallets/{wallet_id}") # Assuming a DELETE endpoint exists


@pytest.fixture(scope="function")
async def two_wallets(wallet_factory):
    """Creates two wallets for transfer tests."""
    wallet1_uuid, _ = await wallet_factory("100.00")
    wallet2_uuid, _ = await wallet_factory("50.00")
    return wallet1_uuid, wallet2_uuid


# --- Test Cases ---

@pytest.mark.parametrize(
    "transfer_amount, expected_status, expected_balance_from, expected_balance_to",
    [
        ("50.00", 200, "50.00", "100.00"),  # Successful transfer
        ("100.00", 200, "0.00", "150.00"),  # Transfer all funds
        ("0.00", 200, "100.00", "50.00"),  # Transfer zero (should succeed, no change)
    ],
)
async def test_transfer_success(
        two_wallets,
        transfer_amount,
        expected_status,
        expected_balance_from,
        expected_balance_to,
        ac_client: AsyncClient,
):
    """Tests successful fund transfers between two wallets."""
    wallet_from_uuid, wallet_to_uuid = two_wallets

    payload = {
        "wallet_from": {"uuid": str(wallet_from_uuid), "amount": transfer_amount},
        "wallet_to": {"uuid": str(wallet_to_uuid)},
    }

    response = await ac_client.post(
        f"/api/v1/wallets/{wallet_from_uuid}/transfer", json=payload
    )

    assert response.status_code == expected_status

    # Verify response structure and data if successful
    if expected_status == 200:
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 2

        # Find the data for each wallet (order might not be guaranteed)
        wallet_from_data = next(w for w in response_data if w["uuid"] == str(wallet_from_uuid))
        wallet_to_data = next(w for w in response_data if w["uuid"] == str(wallet_to_uuid))

        assert wallet_from_data["balance"] == expected_balance_from
        assert wallet_to_data["balance"] == expected_balance_to

        # Also verify by fetching wallets directly
        resp_from = await ac_client.get(f"/api/v1/wallets/{wallet_from_uuid}")
        resp_to = await ac_client.get(f"/api/v1/wallets/{wallet_to_uuid}")
        assert resp_from.status_code == 200
        assert resp_to.status_code == 200
        assert resp_from.json()["balance"] == expected_balance_from
        assert resp_to.json()["balance"] == expected_balance_to


@pytest.mark.parametrize(
    "transfer_amount, initial_balance_from, expected_status",
    [
        ("100.01", "100.00", 400),  # Insufficient funds (assuming 400 Bad Request)
        ("150.00", "100.00", 400),  # Clearly insufficient funds
    ],
)
async def test_transfer_insufficient_funds(
        wallet_factory,
        transfer_amount,
        initial_balance_from,
        expected_status,
        ac_client: AsyncClient,
):
    """Tests transfers failing due to insufficient funds."""
    wallet_from_uuid, _ = await wallet_factory(initial_balance_from)
    wallet_to_uuid, _ = await wallet_factory("50.00")  # Target wallet doesn't matter much here

    payload = {
        "wallet_from": {"uuid": str(wallet_from_uuid), "amount": transfer_amount},
        "wallet_to": {"uuid": str(wallet_to_uuid)},
    }

    response = await ac_client.post(
        f"/api/v1/wallets/{wallet_from_uuid}/transfer", json=payload
    )

    assert response.status_code == expected_status
    # Optional: Check error message in response.json() if API provides one

    # Verify balances haven't changed
    resp_from = await ac_client.get(f"/api/v1/wallets/{wallet_from_uuid}")
    resp_to = await ac_client.get(f"/api/v1/wallets/{wallet_to_uuid}")
    assert resp_from.status_code == 200
    assert resp_to.status_code == 200
    assert resp_from.json()["balance"] == initial_balance_from  # Should be unchanged
    assert resp_to.json()["balance"] == "50.00"  # Should be unchanged


@pytest.mark.parametrize(
    "transfer_amount, expected_status",
    [
        ("-50.00", 422),  # Negative amount (violates schema ge=0)
        # Add other invalid amount cases if needed (e.g., non-numeric)
    ],
)
async def test_transfer_invalid_amount(
        two_wallets,
        transfer_amount,
        expected_status,
        ac_client: AsyncClient,
):
    """Tests transfers with invalid amounts."""
    wallet_from_uuid, wallet_to_uuid = two_wallets

    payload = {
        "wallet_from": {"uuid": str(wallet_from_uuid), "amount": transfer_amount},
        "wallet_to": {"uuid": str(wallet_to_uuid)},
    }

    response = await ac_client.post(
        f"/api/v1/wallets/{wallet_from_uuid}/transfer", json=payload
    )

    assert response.status_code == expected_status


async def test_transfer_non_existent_wallet(
        wallet_factory, ac_client: AsyncClient
):
    """Tests transfer involving non-existent wallets."""
    wallet_from_uuid, _ = await wallet_factory("100.00")
    non_existent_uuid = str(uuid_pkg.uuid4())

    # Case 1: Source wallet in path exists, target in payload does not
    payload_non_existent_to = {
        "wallet_from": {"uuid": str(wallet_from_uuid), "amount": "10.00"},
        "wallet_to": {"uuid": non_existent_uuid},
    }
    response = await ac_client.post(
        f"/api/v1/wallets/{wallet_from_uuid}/transfer", json=payload_non_existent_to
    )
    # Assuming 404 Not Found if the 'to' wallet doesn't exist
    assert response.status_code == 404

    # Case 2: Source wallet in path does not exist
    payload_valid_to = {
        "wallet_from": {"uuid": non_existent_uuid, "amount": "10.00"},
        "wallet_to": {"uuid": str(wallet_from_uuid)},  # Using the valid one as target now
    }
    response = await ac_client.post(
        f"/api/v1/wallets/{non_existent_uuid}/transfer", json=payload_valid_to
    )
    # The path parameter check likely happens first
    assert response.status_code == 404

    # Case 3: Source wallet in path exists, but source UUID in payload does not
    payload_non_existent_from_in_payload = {
        "wallet_from": {"uuid": non_existent_uuid, "amount": "10.00"},
        "wallet_to": {"uuid": str(wallet_from_uuid)},
    }
    response = await ac_client.post(
        f"/api/v1/wallets/{wallet_from_uuid}/transfer", json=payload_non_existent_from_in_payload
    )
    # This might be a 404 (service checks wallet_from.uuid) or 400/422 (mismatch with path)
    # Let's assume 404 for now, adjust based on actual API behavior
    assert response.status_code == 404  # Or potentially 400/422


async def test_transfer_to_self(wallet_factory, ac_client: AsyncClient):
    """Tests transferring funds from a wallet to itself."""
    wallet_uuid, initial_balance = await wallet_factory("100.00")
    initial_balance_str = f"{initial_balance:.2f}"

    payload = {
        "wallet_from": {"uuid": str(wallet_uuid), "amount": "10.00"},
        "wallet_to": {"uuid": str(wallet_uuid)},
    }

    response = await ac_client.post(
        f"/api/v1/wallets/{wallet_uuid}/transfer", json=payload
    )

    # Behavior depends on implementation:
    # 1. Allow: Status 200, balance unchanged.
    # 2. Disallow: Status 400/422/etc.
    # Assuming it's disallowed as a bad request for this test:
    assert response.status_code == 400  # Adjust if API allows it (then check status 200)

    # Verify balance is unchanged regardless
    resp_wallet = await ac_client.get(f"/api/v1/wallets/{wallet_uuid}")
    assert resp_wallet.status_code == 200
    assert resp_wallet.json()["balance"] == initial_balance_str


# --- Race Condition Tests ---

async def test_parallel_transfers_same_direction(two_wallets, ac_client: AsyncClient):
    """Tests multiple parallel transfers from wallet A to wallet B."""
    wallet_a_uuid, wallet_b_uuid = two_wallets
    initial_a_balance = Decimal("100.00")
    initial_b_balance = Decimal("50.00")
    transfer_amount = Decimal("10.00")
    num_transfers = 5  # A should have enough funds (5 * 10 = 50 <= 100)

    async def single_transfer():
        payload = {
            "wallet_from": {"uuid": str(wallet_a_uuid), "amount": str(transfer_amount)},
            "wallet_to": {"uuid": str(wallet_b_uuid)},
        }
        # Use a small delay to increase chance of interleaving, similar to deposit test
        await asyncio.sleep(0.01)
        response = await ac_client.post(
            f"/api/v1/wallets/{wallet_a_uuid}/transfer", json=payload
        )
        return response

    tasks = [single_transfer() for _ in range(num_transfers)]
    results = await asyncio.gather(*tasks)

    # Check all individual transfers succeeded
    successful_transfers = 0
    for r in results:
        if r.status_code == 200:
            successful_transfers += 1
        else:
            print(f"Transfer failed: {r.status_code} - {r.text}")  # Debug output

    # Ensure all transfers were successful (if the logic is correct and funds suffice)
    assert successful_transfers == num_transfers
    for r in results:
        assert r.status_code == 200

    # Verify final balances
    expected_a_balance = initial_a_balance - (num_transfers * transfer_amount)
    expected_b_balance = initial_b_balance + (num_transfers * transfer_amount)

    resp_a = await ac_client.get(f"/api/v1/wallets/{wallet_a_uuid}")
    resp_b = await ac_client.get(f"/api/v1/wallets/{wallet_b_uuid}")

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json()["balance"] == f"{expected_a_balance:.2f}"
    assert resp_b.json()["balance"] == f"{expected_b_balance:.2f}"


async def test_parallel_transfers_opposite_directions(two_wallets, ac_client: AsyncClient):
    """Tests multiple parallel transfers happening in both directions (A->B and B->A)."""
    wallet_a_uuid, wallet_b_uuid = two_wallets
    initial_a_balance = Decimal("100.00")
    initial_b_balance = Decimal("50.00")

    amount_a_to_b = Decimal("10.00")
    amount_b_to_a = Decimal("5.00")
    num_transfers_each_direction = 5  # A: 100 - 5*10 + 5*5 = 75; B: 50 + 5*10 - 5*5 = 75

    async def transfer_a_to_b():
        payload = {
            "wallet_from": {"uuid": str(wallet_a_uuid), "amount": str(amount_a_to_b)},
            "wallet_to": {"uuid": str(wallet_b_uuid)},
        }
        await asyncio.sleep(0.01)  # Small delay
        response = await ac_client.post(
            f"/api/v1/wallets/{wallet_a_uuid}/transfer", json=payload
        )
        return response

    async def transfer_b_to_a():
        payload = {
            "wallet_from": {"uuid": str(wallet_b_uuid), "amount": str(amount_b_to_a)},
            "wallet_to": {"uuid": str(wallet_a_uuid)},
        }
        await asyncio.sleep(0.01)  # Small delay
        response = await ac_client.post(
            f"/api/v1/wallets/{wallet_b_uuid}/transfer", json=payload
        )
        return response

    tasks = []
    for _ in range(num_transfers_each_direction):
        tasks.append(transfer_a_to_b())
        tasks.append(transfer_b_to_a())

    results = await asyncio.gather(*tasks)

    # Check all individual transfers succeeded
    successful_transfers = 0
    for r in results:
        if r.status_code == 200:
            successful_transfers += 1
        else:
            # It's possible some B->A might fail if A->B hasn't completed fast enough
            # depending on transaction isolation. For a strict test, assert all 200.
            # If some failures are expected/possible under race conditions, adjust assert.
            print(f"Transfer failed: {r.status_code} - {r.text}")  # Debug output

    # Assert all transfers were successful if atomicity is guaranteed
    assert successful_transfers == len(tasks)
    for r in results:
        assert r.status_code == 200

    # Verify final balances
    expected_a_balance = initial_a_balance - (num_transfers_each_direction * amount_a_to_b) + (
                num_transfers_each_direction * amount_b_to_a)
    expected_b_balance = initial_b_balance + (num_transfers_each_direction * amount_a_to_b) - (
                num_transfers_each_direction * amount_b_to_a)

    resp_a = await ac_client.get(f"/api/v1/wallets/{wallet_a_uuid}")
    resp_b = await ac_client.get(f"/api/v1/wallets/{wallet_b_uuid}")

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json()["balance"] == f"{expected_a_balance:.2f}"
    assert resp_b.json()["balance"] == f"{expected_b_balance:.2f}"