"""Etapa F3: `regla_fecha.retirada_en`.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-25

Un override que desaparece de Canvas ya no se borra: queda marcado con
`retirada_en`, para que el historial de `fecha_efectiva` siga diciendo que
regla justifico cada fecha superseda (SPEC 09 S9.4.1, Ley 2). Cambio aditivo,
como exige S14.8.2 despues del 16-sep: una columna nueva y nula.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "regla_fecha", sa.Column("retirada_en", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("regla_fecha", "retirada_en")
