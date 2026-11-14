"""Los resultados se conservan cuando se borra su caso al regenerar (RF-11).

resultado_caso.caso_id pasa de ON DELETE CASCADE a ON DELETE SET NULL: regenerar ya no
borra los resultados de ejecuciones pasadas de un caso que volvió a pendiente.

Revision ID: d0d7069ccc61
Revises: 94ce088fe468
Create Date: 2026-11-14 19:28:45.001476

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d0d7069ccc61"
down_revision: str | Sequence[str] | None = "94ce088fe468"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FK = "fk_resultado_caso_caso_id_caso_prueba"


def upgrade() -> None:
    op.alter_column("resultado_caso", "caso_id", existing_type=sa.INTEGER(), nullable=True)
    op.drop_constraint(op.f(FK), "resultado_caso", type_="foreignkey")
    op.create_foreign_key(
        op.f(FK), "resultado_caso", "caso_prueba", ["caso_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    # Con CASCADE estos resultados se habrían borrado junto con su caso.
    op.execute("DELETE FROM resultado_caso WHERE caso_id IS NULL")
    op.drop_constraint(op.f(FK), "resultado_caso", type_="foreignkey")
    op.create_foreign_key(
        op.f(FK), "resultado_caso", "caso_prueba", ["caso_id"], ["id"], ondelete="CASCADE"
    )
    op.alter_column("resultado_caso", "caso_id", existing_type=sa.INTEGER(), nullable=False)
