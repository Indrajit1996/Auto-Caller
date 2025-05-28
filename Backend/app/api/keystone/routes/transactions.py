from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import AsyncSessionDep, Authenticated, IsSuperUser
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionRead, TransactionsRead

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"],
    dependencies=[Authenticated, IsSuperUser],
)


@router.get("/")
async def read_transactions(session: AsyncSessionDep) -> TransactionsRead:
    statement = await session.exec(select(Transaction))
    transactions = statement.all()

    return TransactionsRead.model_validate(
        {"data": transactions, "count": len(transactions)}
    )


@router.get("/{id}")
async def read_transaction_by_id(session: AsyncSessionDep, id: int) -> TransactionRead:
    transaction = await session.get(Transaction, id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionRead.model_validate(transaction)
