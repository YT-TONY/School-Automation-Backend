"""create_payment_tables

Revision ID: 6f111b10d13c
Revises: 2efe472e3a2d
Create Date: 2026-10-23 07:04:01.650045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6f111b10d13c'
down_revision: Union[str, None] = '2efe472e3a2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure Enum types exist safely in PostgreSQL first
    payment_type_enum = postgresql.ENUM('SCHOOL_FEES', 'ONLINE_PIN', 'HOSTEL_FEE', name='paymenttype')
    payment_type_enum.create(op.get_bind(), checkfirst=True)

    payment_status_enum = postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', 'ABANDONED', name='paymentstatus')
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    # 2. Create grading_scales table
    op.create_table('grading_scales',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('grade_letter', sa.String(length=10), nullable=False),
        sa.Column('min_score', sa.Float(), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('remark', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_grading_scale_school_min', 'grading_scales', ['school_id', 'min_score'], unique=False)
    op.create_index(op.f('ix_grading_scales_school_id'), 'grading_scales', ['school_id'], unique=False)

    # 3. Create payment_transactions table (using create_type=False for existing ENUMs)
    op.create_table('payment_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=True),
        sa.Column('invoice_id', sa.UUID(), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=False),
        sa.Column('paystack_access_code', sa.String(length=100), nullable=True),
        sa.Column('amount_total', sa.Float(), nullable=False),
        sa.Column('amount_school', sa.Float(), nullable=False),
        sa.Column('platform_fee', sa.Float(), nullable=False),
        sa.Column('payment_type', postgresql.ENUM('SCHOOL_FEES', 'ONLINE_PIN', 'HOSTEL_FEE', name='paymenttype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'SUCCESS', 'FAILED', 'ABANDONED', name='paymentstatus', create_type=False), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=True),
        sa.Column('payer_email', sa.String(length=255), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_transactions_invoice_id'), 'payment_transactions', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_payment_transactions_reference'), 'payment_transactions', ['reference'], unique=True)
    op.create_index(op.f('ix_payment_transactions_school_id'), 'payment_transactions', ['school_id'], unique=False)
    op.create_index(op.f('ix_payment_transactions_status'), 'payment_transactions', ['status'], unique=False)
    op.create_index(op.f('ix_payment_transactions_student_id'), 'payment_transactions', ['student_id'], unique=False)

    # 4. Create payment_receipts table
    op.create_table('payment_receipts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('transaction_id', sa.UUID(), nullable=False),
        sa.Column('receipt_number', sa.String(length=50), nullable=False),
        sa.Column('payer_name', sa.String(length=255), nullable=False),
        sa.Column('payer_email', sa.String(length=255), nullable=False),
        sa.Column('amount_paid', sa.Float(), nullable=False),
        sa.Column('items_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['transaction_id'], ['payment_transactions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
    op.create_index(op.f('ix_payment_receipts_receipt_number'), 'payment_receipts', ['receipt_number'], unique=True)
    op.create_index(op.f('ix_payment_receipts_school_id'), 'payment_receipts', ['school_id'], unique=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_payment_receipts_school_id'), table_name='payment_receipts')
    op.drop_index(op.f('ix_payment_receipts_receipt_number'), table_name='payment_receipts')
    op.drop_table('payment_receipts')
    op.drop_index(op.f('ix_payment_transactions_student_id'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_status'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_school_id'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_reference'), table_name='payment_transactions')
    op.drop_index(op.f('ix_payment_transactions_invoice_id'), table_name='payment_transactions')
    op.drop_table('payment_transactions')
    op.drop_index(op.f('ix_grading_scales_school_id'), table_name='grading_scales')
    op.drop_index('idx_grading_scale_school_min', table_name='grading_scales')
    op.drop_table('grading_scales')
    # ### end Alembic commands ###