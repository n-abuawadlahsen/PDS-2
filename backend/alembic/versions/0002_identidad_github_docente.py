"""Identidad numerica estable para cuentas GitHub docentes, sin borrar datos.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Esta columna preexistente era INTEGER, sin FK y sin escritor. Se conserva
    # su indice unico y ahora guarda el id numerico retornado por GitHub.
    op.alter_column(
        "usuario",
        "cuenta_github_id",
        type_=sa.BigInteger(),
        existing_type=sa.Integer(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # PostgreSQL rechaza la conversion si algun ID no cabe; nunca lo trunca.
    op.alter_column(
        "usuario",
        "cuenta_github_id",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        existing_nullable=True,
    )
