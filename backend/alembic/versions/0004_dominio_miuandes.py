"""Admite cuentas institucionales miuandes.cl."""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_usuario_email_dominio_gmail", "usuario", type_="check")
    op.create_check_constraint(
        "ck_usuario_email_dominio_admitido",
        "usuario",
        "email LIKE '%@gmail.com' OR email LIKE '%@miuandes.cl'",
    )


def downgrade() -> None:
    op.drop_constraint("ck_usuario_email_dominio_admitido", "usuario", type_="check")
    op.create_check_constraint(
        "ck_usuario_email_dominio_gmail", "usuario", "email LIKE '%@gmail.com'"
    )
