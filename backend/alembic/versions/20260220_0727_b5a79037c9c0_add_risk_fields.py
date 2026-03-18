"""add_risk_fields

Revision ID: b5a79037c9c0
Revises: ebe68779daaf
Create Date: 2026-02-20 07:27:40.882560+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5a79037c9c0'
down_revision: Union[str, None] = 'ebe68779daaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types first (Postgres requires them to exist before column use)
    urgency_enum = sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='urgencylevel')
    impact_enum = sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='impactlevel')
    prep_enum = sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'READY', name='preparationstatus')

    urgency_enum.create(op.get_bind(), checkfirst=True)
    impact_enum.create(op.get_bind(), checkfirst=True)
    prep_enum.create(op.get_bind(), checkfirst=True)

    # Add columns with server_default so existing rows don't fail on NOT NULL
    op.add_column('responsibilities', sa.Column(
        'urgency', urgency_enum, nullable=False, server_default='LOW'
    ))
    op.add_column('responsibilities', sa.Column(
        'impact', impact_enum, nullable=False, server_default='LOW'
    ))
    op.add_column('responsibilities', sa.Column(
        'preparation_status', prep_enum, nullable=False, server_default='NOT_STARTED'
    ))

    # Remove server defaults after backfilling (they were just for the migration)
    op.alter_column('responsibilities', 'urgency', server_default=None)
    op.alter_column('responsibilities', 'impact', server_default=None)
    op.alter_column('responsibilities', 'preparation_status', server_default=None)


def downgrade() -> None:
    op.drop_column('responsibilities', 'preparation_status')
    op.drop_column('responsibilities', 'impact')
    op.drop_column('responsibilities', 'urgency')

    # Drop enum types on downgrade
    sa.Enum(name='preparationstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='impactlevel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='urgencylevel').drop(op.get_bind(), checkfirst=True)
