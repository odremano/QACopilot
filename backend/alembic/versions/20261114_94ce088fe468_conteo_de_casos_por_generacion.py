"""Conteo de casos válidos e inválidos guardado en cada generación (RF-12).

Se guarda al generar porque los casos cambian después (editar revalida, regenerar borra
pendientes). Las generaciones anteriores quedan en nulo: recalcularlas daría números falsos.

Revision ID: 94ce088fe468
Revises: 1a9f20b58901
Create Date: 2026-11-14 18:25:13.813884

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "94ce088fe468"
down_revision: str | Sequence[str] | None = "1a9f20b58901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("generacion", sa.Column("casos_validos", sa.Integer(), nullable=True))
    op.add_column("generacion", sa.Column("casos_invalidos", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("generacion", "casos_invalidos")
    op.drop_column("generacion", "casos_validos")
