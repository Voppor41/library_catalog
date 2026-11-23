from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8c4f9d2a1b73"
down_revision: str | Sequence[str] | None = "3a33543328b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("books", "year", existing_type=sa.Integer(), nullable=False)
    op.alter_column("books", "pages", existing_type=sa.Integer(), nullable=False)
    op.drop_index("ix_books_book_id", table_name="books")


def downgrade() -> None:
    op.create_index("ix_books_book_id", "books", ["book_id"], unique=False)
    op.alter_column("books", "pages", existing_type=sa.Integer(), nullable=True)
    op.alter_column("books", "year", existing_type=sa.Integer(), nullable=True)
