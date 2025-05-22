import uuid
from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.transaction import Action, Model, Transaction
from app.schemas.transaction import TransactionCreate, TransactionMetaData
from app.utils.decorators import with_async_db_session


@with_async_db_session
async def log_transaction(
    *,
    session: AsyncSession,
    model: Model,
    action: Action,
    user_id: uuid.UUID,
    record_id: str | None = None,
    description: str,
    meta_data: TransactionMetaData,
) -> Transaction:
    transaction = Transaction(
        model=model,
        action=action,
        user_id=user_id,
        description=description,
        record_id=record_id,
        meta_data=meta_data.model_dump() if meta_data else {},
    )
    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


@with_async_db_session
async def log_multiple_transactions(
    *, session: AsyncSession, transactions_in: list[TransactionCreate]
) -> Sequence[Transaction]:
    transactions = []
    for t in transactions_in:
        new_tx = Transaction(
            model=t.model,
            action=t.action,
            user_id=t.user_id,
            record_id=t.record_id,
            description=t.description,
            meta_data=t.meta_data.model_dump() if t.meta_data else {},
        )
        transactions.append(new_tx)
    session.add_all(transactions)
    await session.commit()
    transaction_ids = [tx.id for tx in transactions]
    if transaction_ids:
        refreshed = await session.exec(
            select(Transaction).where(Transaction.id.in_(transaction_ids))
        )
        transactions = refreshed.all()
    return transactions
