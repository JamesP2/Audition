"""no_show

Revision ID: a84d840590be
Revises: bbc04efdde74
Create Date: 2017-09-09 17:14:43.078476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a84d840590be'
down_revision = 'bbc04efdde74'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('audition', sa.Column('no_show', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('audition', 'no_show')
    # ### end Alembic commands ###
