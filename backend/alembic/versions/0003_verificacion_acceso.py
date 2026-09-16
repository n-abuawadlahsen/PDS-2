"""Fecha real de comprobacion del acceso del estudiante en GitHub.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Los accesos historicos quedan sin fecha: no inventar una comprobacion.
    op.add_column(
        "acceso_repositorio", sa.Column("verificado_en", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("acceso_repositorio", "verificado_en")
