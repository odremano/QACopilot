"""Una sola ejecución en curso a la vez (RF-07, RNF-09): índice único parcial.

Revision ID: 1a9f20b58901
Revises: 21819765d75b
Create Date: 2026-11-05 17:41:25.167343

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1a9f20b58901"
down_revision: str | Sequence[str] | None = "21819765d75b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ux_ejecucion_una_en_curso",
        "ejecucion",
        ["estado"],
        unique=True,
        postgresql_where=sa.text("estado = 'en_curso'"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_ejecucion_una_en_curso",
        table_name="ejecucion",
        postgresql_where=sa.text("estado = 'en_curso'"),
    )
