"""Roles de estudiante, contexto del reparto y alias de identidades Canvas."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "estudiante",
        sa.Column(
            "fusionada_en_id",
            UUID(as_uuid=True),
            sa.ForeignKey("estudiante.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column("asignacion_correccion", sa.Column("criterio_contexto", JSONB(), nullable=True))
    op.add_column(
        "curso", sa.Column("roles_estudiante_extra", JSONB(), nullable=False, server_default="[]")
    )
    op.create_check_constraint(
        op.f("ck_curso_roles_extra_lista"),
        "curso",
        "jsonb_typeof(roles_estudiante_extra) = 'array'",
    )


def downgrade() -> None:
    op.drop_column("estudiante", "fusionada_en_id")
    op.drop_column("asignacion_correccion", "criterio_contexto")
    op.drop_constraint(op.f("ck_curso_roles_extra_lista"), "curso", type_="check")
    op.drop_column("curso", "roles_estudiante_extra")
