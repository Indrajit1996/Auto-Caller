from fastapi import status
from fastapi.testclient import TestClient


def test_read_transactions(
    superuser_client: TestClient,
) -> None:
    """Test reading transactions with superuser."""
    response = superuser_client.get("/transactions/")
    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.json()
    assert "count" in response.json()


def test_read_transactions_unauthorized(authorized_client: TestClient) -> None:
    """Test reading transactions without superuser privileges."""
    response = authorized_client.get("/transactions/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_read_transaction_by_id_not_found(superuser_client: TestClient) -> None:
    """Test reading a transaction by ID that does not exist."""
    response = superuser_client.get("/transactions/9999")  # Non-existent ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Transaction not found"


def test_read_transaction_by_id_unauthorized(authorized_client: TestClient) -> None:
    """Test reading a transaction by ID without superuser privileges."""
    response = authorized_client.get("/transactions/1")
    assert response.status_code == status.HTTP_403_FORBIDDEN
