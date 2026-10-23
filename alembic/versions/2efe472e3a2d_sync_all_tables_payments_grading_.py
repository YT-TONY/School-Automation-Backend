"""sync_all_tables_payments_grading_permissions

Revision ID: 2efe472e3a2d
Revises: 91c5d44c6558
Create Date: 2026-10-20 18:14:08.418507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2efe472e3a2d'
down_revision: Union[str, None] = '91c5d44c6558'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create missing Enum types in PostgreSQL first
    school_type_enum = sa.Enum('DAY', 'BOARDING', 'MIXED', name='school_type_enum')
    school_type_enum.create(op.get_bind(), checkfirst=True)

    payment_type_enum = sa.Enum('SCHOOL_FEES', 'ONLINE_PIN', 'HOSTEL_FEE', name='paymenttype')
    payment_type_enum.create(op.get_bind(), checkfirst=True)

    payment_status_enum = sa.Enum('PENDING', 'SUCCESS', 'FAILED', 'ABANDONED', name='paymentstatus')
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    op.create_table('fee_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('fee_type', sa.Enum('MANDATORY', 'OPTIONAL', 'CONDITIONAL', name='fee_type_enum'), nullable=False),
        sa.Column('session', sa.String(length=20), nullable=False),
        sa.Column('term', sa.String(length=20), nullable=False),
        sa.Column('applicable_classes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_new_student_only', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fee_items_school_id'), 'fee_items', ['school_id'], unique=False)

    op.create_table('hostels',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('gender', sa.Enum('MALE', 'FEMALE', 'MIXED', name='gender_restriction_enum'), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hostels_school_id'), 'hostels', ['school_id'], unique=False)

    op.create_table('hostel_rooms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('hostel_id', sa.UUID(), nullable=False),
        sa.Column('room_number', sa.String(length=50), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('termly_fee', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['hostel_id'], ['hostels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hostel_rooms_hostel_id'), 'hostel_rooms', ['hostel_id'], unique=False)
    op.create_index(op.f('ix_hostel_rooms_school_id'), 'hostel_rooms', ['school_id'], unique=False)

    op.create_table('result_status_audits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('session', sa.String(length=20), nullable=False),
        sa.Column('term', sa.String(length=20), nullable=False),
        sa.Column('class_arm_id', sa.UUID(), nullable=True),
        sa.Column('student_id', sa.UUID(), nullable=True),
        sa.Column('previous_status', sa.String(length=50), nullable=False),
        sa.Column('target_status', sa.Enum('DRAFT', 'SUBMITTED_BY_TEACHER', 'COMPILED_BY_CLASS_TEACHER', 'APPROVED_BY_VP', 'PUBLISHED', name='resultstatus'), nullable=False),
        sa.Column('records_affected', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_result_status_audits_school_id'), 'result_status_audits', ['school_id'], unique=False)
    op.create_index(op.f('ix_result_status_audits_user_id'), 'result_status_audits', ['user_id'], unique=False)

    op.create_table('teacher_assignments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('class_arm_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['class_arm_id'], ['class_arms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_teacher_assignment_unique', 'teacher_assignments', ['school_id', 'teacher_id', 'subject_id', 'class_arm_id'], unique=True)
    op.create_index(op.f('ix_teacher_assignments_school_id'), 'teacher_assignments', ['school_id'], unique=False)
    op.create_index(op.f('ix_teacher_assignments_teacher_id'), 'teacher_assignments', ['teacher_id'], unique=False)

    op.create_table('affective_psychomotor_domains',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('session', sa.String(length=20), nullable=False),
        sa.Column('term', sa.String(length=20), nullable=False),
        sa.Column('punctuality', sa.Integer(), nullable=False),
        sa.Column('neatness', sa.Integer(), nullable=False),
        sa.Column('leadership', sa.Integer(), nullable=False),
        sa.Column('honesty', sa.Integer(), nullable=False),
        sa.Column('politeness', sa.Integer(), nullable=False),
        sa.Column('handwriting', sa.Integer(), nullable=False),
        sa.Column('sports_and_games', sa.Integer(), nullable=False),
        sa.Column('craft_and_art', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_affective_unique', 'affective_psychomotor_domains', ['school_id', 'student_id', 'session', 'term'], unique=True)
    op.create_index(op.f('ix_affective_psychomotor_domains_school_id'), 'affective_psychomotor_domains', ['school_id'], unique=False)
    op.create_index(op.f('ix_affective_psychomotor_domains_student_id'), 'affective_psychomotor_domains', ['student_id'], unique=False)

    op.create_table('bed_allocations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('session', sa.String(length=20), nullable=False),
        sa.Column('term', sa.String(length=20), nullable=False),
        sa.Column('status', sa.Enum('RESERVED', 'CONFIRMED', 'VACATED', name='reservation_status_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['hostel_rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_bed_allocation_unique', 'bed_allocations', ['school_id', 'student_id', 'session', 'term'], unique=True)
    op.create_index(op.f('ix_bed_allocations_room_id'), 'bed_allocations', ['room_id'], unique=False)
    op.create_index(op.f('ix_bed_allocations_school_id'), 'bed_allocations', ['school_id'], unique=False)
    op.create_index(op.f('ix_bed_allocations_student_id'), 'bed_allocations', ['student_id'], unique=False)

    op.create_table('student_fee_selections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('fee_item_id', sa.UUID(), nullable=False),
        sa.Column('is_selected', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['fee_item_id'], ['fee_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_student_fee_selection_unique', 'student_fee_selections', ['school_id', 'student_id', 'fee_item_id'], unique=True)
    op.create_index(op.f('ix_student_fee_selections_school_id'), 'student_fee_selections', ['school_id'], unique=False)
    op.create_index(op.f('ix_student_fee_selections_student_id'), 'student_fee_selections', ['student_id'], unique=False)

    op.create_table('terminal_remarks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('session', sa.String(length=20), nullable=False),
        sa.Column('term', sa.String(length=20), nullable=False),
        sa.Column('form_teacher_remark', sa.String(length=500), nullable=True),
        sa.Column('principal_remark', sa.String(length=500), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_terminal_remark_unique', 'terminal_remarks', ['school_id', 'student_id', 'session', 'term'], unique=True)
    op.create_index(op.f('ix_terminal_remarks_school_id'), 'terminal_remarks', ['school_id'], unique=False)
    op.create_index(op.f('ix_terminal_remarks_student_id'), 'terminal_remarks', ['student_id'], unique=False)

    op.add_column('class_arms', sa.Column('form_teacher_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_class_arms_form_teacher_id'), 'class_arms', ['form_teacher_id'], unique=False)
    op.create_foreign_key('fk_class_arms_form_teacher', 'class_arms', 'users', ['form_teacher_id'], ['id'], ondelete='SET NULL')

    op.add_column('results', sa.Column('test1_score', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('results', sa.Column('test2_score', sa.Float(), server_default='0.0', nullable=False))
    op.add_column('results', sa.Column('assignment_score', sa.Float(), server_default='0.0', nullable=False))

    op.add_column('schools', sa.Column('paystack_subaccount_code', sa.String(length=100), nullable=True))
    op.add_column('schools', sa.Column('school_type', sa.Enum('DAY', 'BOARDING', 'MIXED', name='school_type_enum'), server_default='MIXED', nullable=False))
    op.create_index(op.f('ix_schools_paystack_subaccount_code'), 'schools', ['paystack_subaccount_code'], unique=False)

    op.add_column('users', sa.Column('is_exam_officer', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('is_class_teacher', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('can_enroll_students', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('can_manage_fees', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('can_approve_results', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'can_approve_results')
    op.drop_column('users', 'can_manage_fees')
    op.drop_column('users', 'can_enroll_students')
    op.drop_column('users', 'is_class_teacher')
    op.drop_column('users', 'is_exam_officer')
    op.drop_index(op.f('ix_schools_paystack_subaccount_code'), table_name='schools')
    op.drop_column('schools', 'school_type')
    op.drop_column('schools', 'paystack_subaccount_code')
    op.drop_column('results', 'assignment_score')
    op.drop_column('results', 'test2_score')
    op.drop_column('results', 'test1_score')
    # WARNING: constraint name is None; this directive will fail as
    # rendered.  Add a name, or use a naming convention; see
    # https://alembic.sqlalchemy.org/en/latest/naming.html
    op.drop_constraint(None, 'class_arms', type_='foreignkey')
    op.drop_index(op.f('ix_class_arms_form_teacher_id'), table_name='class_arms')
    op.drop_column('class_arms', 'form_teacher_id')
    op.drop_index(op.f('ix_terminal_remarks_student_id'), table_name='terminal_remarks')
    op.drop_index(op.f('ix_terminal_remarks_school_id'), table_name='terminal_remarks')
    op.drop_index('idx_terminal_remark_unique', table_name='terminal_remarks')
    op.drop_table('terminal_remarks')
    op.drop_index(op.f('ix_student_fee_selections_student_id'), table_name='student_fee_selections')
    op.drop_index(op.f('ix_student_fee_selections_school_id'), table_name='student_fee_selections')
    op.drop_index('idx_student_fee_selection_unique', table_name='student_fee_selections')
    op.drop_table('student_fee_selections')
    op.drop_index(op.f('ix_bed_allocations_student_id'), table_name='bed_allocations')
    op.drop_index(op.f('ix_bed_allocations_school_id'), table_name='bed_allocations')
    op.drop_index(op.f('ix_bed_allocations_room_id'), table_name='bed_allocations')
    op.drop_index('idx_bed_allocation_unique', table_name='bed_allocations')
    op.drop_table('bed_allocations')
    op.drop_index(op.f('ix_affective_psychomotor_domains_student_id'), table_name='affective_psychomotor_domains')
    op.drop_index(op.f('ix_affective_psychomotor_domains_school_id'), table_name='affective_psychomotor_domains')
    op.drop_index('idx_affective_unique', table_name='affective_psychomotor_domains')
    op.drop_table('affective_psychomotor_domains')
    op.drop_index(op.f('ix_teacher_assignments_teacher_id'), table_name='teacher_assignments')
    op.drop_index(op.f('ix_teacher_assignments_school_id'), table_name='teacher_assignments')
    op.drop_index('idx_teacher_assignment_unique', table_name='teacher_assignments')
    op.drop_table('teacher_assignments')
    op.drop_index(op.f('ix_result_status_audits_user_id'), table_name='result_status_audits')
    op.drop_index(op.f('ix_result_status_audits_school_id'), table_name='result_status_audits')
    op.drop_table('result_status_audits')
    op.drop_index(op.f('ix_hostel_rooms_school_id'), table_name='hostel_rooms')
    op.drop_index(op.f('ix_hostel_rooms_hostel_id'), table_name='hostel_rooms')
    op.drop_table('hostel_rooms')
    op.drop_index(op.f('ix_hostels_school_id'), table_name='hostels')
    op.drop_table('hostels')
    op.drop_index(op.f('ix_fee_items_school_id'), table_name='fee_items')
    op.drop_table('fee_items')
    # ### end Alembic commands ###