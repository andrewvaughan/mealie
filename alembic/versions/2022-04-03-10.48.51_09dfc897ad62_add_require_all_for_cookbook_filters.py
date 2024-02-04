"""add require_all for cookbook filters

Revision ID: 09dfc897ad62
Revises: 59eb59135381
Create Date: 2022-04-03 10:48:51.379968

"""

import sqlalchemy as sa

import mealie.db.migration_types  # noqa: F401
from alembic import op

# revision identifiers, used by Alembic.
revision = "09dfc897ad62"
down_revision = "59eb59135381"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("cookbooks", sa.Column("require_all_categories", sa.Boolean(), nullable=True))
    op.add_column("cookbooks", sa.Column("require_all_tags", sa.Boolean(), nullable=True))
    op.add_column("cookbooks", sa.Column("require_all_tools", sa.Boolean(), nullable=True))

    # Set Defaults for Existing Cookbooks
    op.execute(
        """
        UPDATE cookbooks
        SET require_all_categories = TRUE,
            require_all_tags = TRUE,
            require_all_tools = TRUE
        """
    )

    # ### end Alembic commands ###
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("cookbooks", "require_all_tools")
    op.drop_column("cookbooks", "require_all_tags")
    op.drop_column("cookbooks", "require_all_categories")
    # ### end Alembic commands ###
