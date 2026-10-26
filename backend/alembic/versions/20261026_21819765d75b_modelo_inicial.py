"""Modelo inicial: las 5 tablas de la sección 8 de la spec.

Revisada a mano: CheckConstraint de estados, server_default, FK en cascada
(generacion_id con SET NULL) e índices en todas las FK.

Revision ID: 21819765d75b
Revises:
Create Date: 2026-10-26 00:09:28.032034

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "21819765d75b"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "historia_usuario",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("titulo", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("criterios_aceptacion", sa.Text(), nullable=True),
        sa.Column(
            "creada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizada_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_historia_usuario")),
    )
    op.create_table(
        "ejecucion",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("historia_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="en_curso", nullable=False),
        sa.Column(
            "iniciada_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finalizada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("aprobados", sa.Integer(), server_default="0", nullable=False),
        sa.Column("fallidos", sa.Integer(), server_default="0", nullable=False),
        sa.Column("omitidos", sa.Integer(), server_default="0", nullable=False),
        sa.Column("log", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "estado IN ('en_curso', 'finalizada', 'error')", name=op.f("ck_ejecucion_estado_valido")
        ),
        sa.ForeignKeyConstraint(
            ["historia_id"],
            ["historia_usuario.id"],
            name=op.f("fk_ejecucion_historia_id_historia_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ejecucion")),
    )
    op.create_index(op.f("ix_ejecucion_historia_id"), "ejecucion", ["historia_id"], unique=False)
    op.create_table(
        "generacion",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("historia_id", sa.Integer(), nullable=False),
        sa.Column("proveedor", sa.String(length=50), nullable=False),
        sa.Column("modelo", sa.String(length=100), nullable=False),
        sa.Column("version_prompt", sa.String(length=20), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("duracion_ms", sa.Integer(), nullable=True),
        sa.Column("respuesta_cruda", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("mensaje_error", sa.Text(), nullable=True),
        sa.Column(
            "creada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint("estado IN ('ok', 'error')", name=op.f("ck_generacion_estado_valido")),
        sa.ForeignKeyConstraint(
            ["historia_id"],
            ["historia_usuario.id"],
            name=op.f("fk_generacion_historia_id_historia_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generacion")),
    )
    op.create_index(op.f("ix_generacion_historia_id"), "generacion", ["historia_id"], unique=False)
    op.create_table(
        "caso_prueba",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("historia_id", sa.Integer(), nullable=False),
        sa.Column("generacion_id", sa.Integer(), nullable=True),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("gherkin", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(length=20), server_default="pendiente", nullable=False),
        sa.Column("valido", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("errores_validacion", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'aprobado', 'descartado')",
            name=op.f("ck_caso_prueba_estado_valido"),
        ),
        sa.CheckConstraint(
            "tipo IN ('positivo', 'negativo', 'limite')", name=op.f("ck_caso_prueba_tipo_valido")
        ),
        sa.ForeignKeyConstraint(
            ["generacion_id"],
            ["generacion.id"],
            name=op.f("fk_caso_prueba_generacion_id_generacion"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["historia_id"],
            ["historia_usuario.id"],
            name=op.f("fk_caso_prueba_historia_id_historia_usuario"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_caso_prueba")),
    )
    op.create_index(
        op.f("ix_caso_prueba_generacion_id"), "caso_prueba", ["generacion_id"], unique=False
    )
    op.create_index(
        op.f("ix_caso_prueba_historia_id"), "caso_prueba", ["historia_id"], unique=False
    )
    op.create_table(
        "resultado_caso",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("ejecucion_id", sa.Integer(), nullable=False),
        sa.Column("caso_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("duracion_ms", sa.Integer(), nullable=True),
        sa.Column("mensaje_error", sa.Text(), nullable=True),
        sa.Column("ruta_captura", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            "estado IN ('aprobado', 'fallido', 'omitido')",
            name=op.f("ck_resultado_caso_estado_valido"),
        ),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["caso_prueba.id"],
            name=op.f("fk_resultado_caso_caso_id_caso_prueba"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ejecucion_id"],
            ["ejecucion.id"],
            name=op.f("fk_resultado_caso_ejecucion_id_ejecucion"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resultado_caso")),
    )
    op.create_index(op.f("ix_resultado_caso_caso_id"), "resultado_caso", ["caso_id"], unique=False)
    op.create_index(
        op.f("ix_resultado_caso_ejecucion_id"), "resultado_caso", ["ejecucion_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_resultado_caso_ejecucion_id"), table_name="resultado_caso")
    op.drop_index(op.f("ix_resultado_caso_caso_id"), table_name="resultado_caso")
    op.drop_table("resultado_caso")
    op.drop_index(op.f("ix_caso_prueba_historia_id"), table_name="caso_prueba")
    op.drop_index(op.f("ix_caso_prueba_generacion_id"), table_name="caso_prueba")
    op.drop_table("caso_prueba")
    op.drop_index(op.f("ix_generacion_historia_id"), table_name="generacion")
    op.drop_table("generacion")
    op.drop_index(op.f("ix_ejecucion_historia_id"), table_name="ejecucion")
    op.drop_table("ejecucion")
    op.drop_table("historia_usuario")
