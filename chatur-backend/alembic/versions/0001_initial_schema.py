"""Initial CHATUR schema migration.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-01 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Schools
    op.create_table(
        'schools',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_schools_code', 'schools', ['code'], unique=True)

    # 2. Boards
    op.create_table(
        'boards',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_boards_code', 'boards', ['code'], unique=True)

    # 3. User Accounts
    op.create_table(
        'user_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('preferred_lang', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_accounts_username', 'user_accounts', ['username'], unique=True)
    op.create_index('ix_user_accounts_email', 'user_accounts', ['email'], unique=True)
    op.create_index('ix_user_accounts_role', 'user_accounts', ['role'])
    op.create_index('ix_user_accounts_school_id', 'user_accounts', ['school_id'])

    # 4. Auth Tokens
    op.create_table(
        'auth_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False),
        sa.Column('token_type', sa.String(length=50), nullable=False, server_default='refresh'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auth_tokens_token', 'auth_tokens', ['token'], unique=True)
    op.create_index('ix_auth_tokens_user_id', 'auth_tokens', ['user_id'])

    # 5. Student Profiles
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=True),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(length=10), nullable=False),
        sa.Column('roll_no', sa.String(length=50), nullable=True),
        sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index('ix_student_profiles_school_id', 'student_profiles', ['school_id'])

    # 6. Class Sections
    op.create_table(
        'class_sections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False, server_default='2026-27'),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_class_sections_school_id', 'class_sections', ['school_id'])

    # 7. Student Enrollments
    op.create_table(
        'student_enrollments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('section_id', sa.String(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['section_id'], ['class_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_student_enrollments_section_id', 'student_enrollments', ['section_id'])
    op.create_index('ix_student_enrollments_student_id', 'student_enrollments', ['student_id'])

    # 8. Parent-Child Links
    op.create_table(
        'parent_child_links',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('parent_user_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('relationship', sa.String(length=50), nullable=False, server_default='parent'),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('consent_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_parent_child_links_parent_user_id', 'parent_child_links', ['parent_user_id'])
    op.create_index('ix_parent_child_links_student_id', 'parent_child_links', ['student_id'])

    # 9. Curriculum Subjects
    op.create_table(
        'curriculum_subjects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('board_id', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_te', sa.String(length=255), nullable=True),
        sa.Column('name_hi', sa.String(length=255), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['board_id'], ['boards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_curriculum_subjects_board_id', 'curriculum_subjects', ['board_id'])
    op.create_index('ix_curriculum_subjects_code', 'curriculum_subjects', ['code'])

    # 10. Teacher Assignments
    op.create_table(
        'teacher_assignments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('teacher_user_id', sa.String(length=36), nullable=False),
        sa.Column('section_id', sa.String(length=36), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=True),
        sa.Column('is_class_teacher', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['section_id'], ['class_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['curriculum_subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_teacher_assignments_teacher_user_id', 'teacher_assignments', ['teacher_user_id'])
    op.create_index('ix_teacher_assignments_section_id', 'teacher_assignments', ['section_id'])
    op.create_index('ix_teacher_assignments_subject_id', 'teacher_assignments', ['subject_id'])

    # 11. Curriculum Units
    op.create_table(
        'curriculum_units',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False, server_default='2026-27'),
        sa.Column('unit_no', sa.Integer(), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_te', sa.String(length=255), nullable=True),
        sa.Column('name_hi', sa.String(length=255), nullable=True),
        sa.Column('source_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['curriculum_subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_curriculum_units_subject_id', 'curriculum_units', ['subject_id'])

    # 12. Curriculum Chapters
    op.create_table(
        'curriculum_chapters',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('unit_id', sa.String(length=36), nullable=False),
        sa.Column('chapter_no', sa.Integer(), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_te', sa.String(length=255), nullable=True),
        sa.Column('name_hi', sa.String(length=255), nullable=True),
        sa.Column('source_ref', sa.String(length=255), nullable=True),
        sa.Column('ncert_verified', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['unit_id'], ['curriculum_units.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_curriculum_chapters_unit_id', 'curriculum_chapters', ['unit_id'])

    # 13. Curriculum Topics
    op.create_table(
        'curriculum_topics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('chapter_id', sa.String(length=36), nullable=False),
        sa.Column('topic_no', sa.Integer(), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_te', sa.String(length=255), nullable=True),
        sa.Column('name_hi', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['curriculum_chapters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_curriculum_topics_chapter_id', 'curriculum_topics', ['chapter_id'])

    # 14. Concepts
    op.create_table(
        'concepts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('topic_id', sa.String(length=36), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name_en', sa.String(length=255), nullable=False),
        sa.Column('name_te', sa.String(length=255), nullable=True),
        sa.Column('name_hi', sa.String(length=255), nullable=True),
        sa.Column('grade', sa.Integer(), nullable=False),
        sa.Column('difficulty_band', sa.String(length=50), nullable=False, server_default='medium'),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('common_misconceptions', sa.JSON(), nullable=True),
        sa.Column('content_status', sa.String(length=50), nullable=False, server_default='approved'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['curriculum_topics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_concepts_code', 'concepts', ['code'], unique=True)
    op.create_index('ix_concepts_topic_id', 'concepts', ['topic_id'])

    # 15. Concept Prerequisites
    op.create_table(
        'concept_prerequisites',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('concept_id', sa.String(length=36), nullable=False),
        sa.Column('prerequisite_id', sa.String(length=36), nullable=False),
        sa.Column('is_strict', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['prerequisite_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_concept_prerequisites_concept_id', 'concept_prerequisites', ['concept_id'])
    op.create_index('ix_concept_prerequisites_prerequisite_id', 'concept_prerequisites', ['prerequisite_id'])

    # 16. Questions
    op.create_table(
        'questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('concept_id', sa.String(length=36), nullable=False),
        sa.Column('qtype', sa.String(length=50), nullable=False, server_default='mcq'),
        sa.Column('difficulty', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('usage_tag', sa.String(length=50), nullable=False, server_default='practice'),
        sa.Column('bloom_level', sa.String(length=50), nullable=False, server_default='understand'),
        sa.Column('body_en', sa.JSON(), nullable=False),
        sa.Column('body_te', sa.JSON(), nullable=True),
        sa.Column('body_hi', sa.JSON(), nullable=True),
        sa.Column('answer_data', sa.JSON(), nullable=False),
        sa.Column('primary_error_type', sa.String(length=100), nullable=True),
        sa.Column('explanation_en', sa.Text(), nullable=True),
        sa.Column('explanation_te', sa.Text(), nullable=True),
        sa.Column('explanation_hi', sa.Text(), nullable=True),
        sa.Column('hints', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='ncert'),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='approved'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('correct_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_questions_concept_id', 'questions', ['concept_id'])
    op.create_index('ix_questions_approval_status', 'questions', ['approval_status'])

    # 17. Learning Resources
    op.create_table(
        'learning_resources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('concept_id', sa.String(length=36), nullable=False),
        sa.Column('rtype', sa.String(length=50), nullable=False, server_default='explainer'),
        sa.Column('title_en', sa.String(length=255), nullable=False),
        sa.Column('title_te', sa.String(length=255), nullable=True),
        sa.Column('title_hi', sa.String(length=255), nullable=True),
        sa.Column('content_en', sa.Text(), nullable=True),
        sa.Column('content_te', sa.Text(), nullable=True),
        sa.Column('content_hi', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(length=512), nullable=True),
        sa.Column('duration_secs', sa.Integer(), nullable=False, server_default='180'),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='approved'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_learning_resources_concept_id', 'learning_resources', ['concept_id'])

    # 18. Student Mastery
    op.create_table(
        'student_mastery',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('concept_id', sa.String(length=36), nullable=False),
        sa.Column('p_know', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('p_learn', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('p_guess', sa.Float(), nullable=False, server_default='0.2'),
        sa.Column('p_slip', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('working_concept_id', sa.String(length=36), nullable=True),
        sa.Column('recent_scores', sa.JSON(), nullable=True),
        sa.Column('total_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_correct', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_low', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('consecutive_high', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['working_concept_id'], ['concepts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_student_mastery_student_id', 'student_mastery', ['student_id'])
    op.create_index('ix_student_mastery_concept_id', 'student_mastery', ['concept_id'])

    # 19. Mastery History
    op.create_table(
        'mastery_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('mastery_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('concept_id', sa.String(length=36), nullable=False),
        sa.Column('p_know_before', sa.Float(), nullable=False),
        sa.Column('p_know_after', sa.Float(), nullable=False),
        sa.Column('trigger_event', sa.String(length=50), nullable=False, server_default='question_response'),
        sa.Column('answer_correct', sa.Boolean(), nullable=False),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mastery_id'], ['student_mastery.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_mastery_history_mastery_id', 'mastery_history', ['mastery_id'])
    op.create_index('ix_mastery_history_student_id', 'mastery_history', ['student_id'])
    op.create_index('ix_mastery_history_concept_id', 'mastery_history', ['concept_id'])

    # 20. Level Change Proposals
    op.create_table(
        'level_change_proposals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('target_concept_id', sa.String(length=36), nullable=False),
        sa.Column('proposed_level_concept_id', sa.String(length=36), nullable=False),
        sa.Column('proposal_type', sa.String(length=50), nullable=False, server_default='remediation'),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('narrative_en', sa.Text(), nullable=True),
        sa.Column('narrative_te', sa.Text(), nullable=True),
        sa.Column('narrative_hi', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('decided_by', sa.String(length=36), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('teacher_notes', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['decided_by'], ['user_accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['proposed_level_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_level_change_proposals_student_id', 'level_change_proposals', ['student_id'])
    op.create_index('ix_level_change_proposals_status', 'level_change_proposals', ['status'])

    # 21. Assessments
    op.create_table(
        'assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('assessment_type', sa.String(length=50), nullable=False, server_default='diagnostic'),
        sa.Column('concept_id', sa.String(length=36), nullable=True),
        sa.Column('total_marks', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('time_limit_mins', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_assessments_school_id', 'assessments', ['school_id'])

    # 22. Assessment Attempts
    op.create_table(
        'assessment_attempts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('assessment_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='in_progress'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_assessment_attempts_assessment_id', 'assessment_attempts', ['assessment_id'])
    op.create_index('ix_assessment_attempts_student_id', 'assessment_attempts', ['student_id'])

    # 23. Attempt Responses
    op.create_table(
        'attempt_responses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('attempt_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('student_response', sa.JSON(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('points_awarded', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('time_spent_secs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['assessment_attempts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_attempt_responses_attempt_id', 'attempt_responses', ['attempt_id'])
    op.create_index('ix_attempt_responses_question_id', 'attempt_responses', ['question_id'])

    # 24. Remedial Groups
    op.create_table(
        'remedial_groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('teacher_user_id', sa.String(length=36), nullable=False),
        sa.Column('section_id', sa.String(length=36), nullable=True),
        sa.Column('concept_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['concepts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['class_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_remedial_groups_teacher_user_id', 'remedial_groups', ['teacher_user_id'])
    op.create_index('ix_remedial_groups_section_id', 'remedial_groups', ['section_id'])
    op.create_index('ix_remedial_groups_concept_id', 'remedial_groups', ['concept_id'])

    # 25. Remedial Group Members
    op.create_table(
        'remedial_group_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exit_p_know', sa.Float(), nullable=True),
        sa.Column('exited_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['remedial_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_remedial_group_members_group_id', 'remedial_group_members', ['group_id'])
    op.create_index('ix_remedial_group_members_student_id', 'remedial_group_members', ['student_id'])

    # 26. Teacher Activity Logs
    op.create_table(
        'teacher_activity_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('teacher_user_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id', sa.String(length=36), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['teacher_user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_teacher_activity_logs_teacher_user_id', 'teacher_activity_logs', ['teacher_user_id'])

    # 27. Worksheets
    op.create_table(
        'worksheets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('teacher_user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('concept_ids', sa.JSON(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['teacher_user_id'], ['user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_worksheets_teacher_user_id', 'worksheets', ['teacher_user_id'])

    # 28. Pilot Cohorts
    op.create_table(
        'pilot_cohorts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('target_grade', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pilot_cohorts_school_id', 'pilot_cohorts', ['school_id'])

    # 29. Pilot Cohort Members
    op.create_table(
        'pilot_cohort_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('cohort_id', sa.String(length=36), nullable=False),
        sa.Column('student_id', sa.String(length=36), nullable=False),
        sa.Column('baseline_score', sa.Float(), nullable=True),
        sa.Column('midline_score', sa.Float(), nullable=True),
        sa.Column('endline_score', sa.Float(), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cohort_id'], ['pilot_cohorts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pilot_cohort_members_cohort_id', 'pilot_cohort_members', ['cohort_id'])
    op.create_index('ix_pilot_cohort_members_student_id', 'pilot_cohort_members', ['student_id'])

    # 30. Impact Snapshots
    op.create_table(
        'impact_snapshots',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('cohort_id', sa.String(length=36), nullable=True),
        sa.Column('school_id', sa.String(length=36), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('avg_mastery', sa.Float(), nullable=True),
        sa.Column('total_active_students', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('learning_gain_pct', sa.Float(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['cohort_id'], ['pilot_cohorts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_impact_snapshots_cohort_id', 'impact_snapshots', ['cohort_id'])
    op.create_index('ix_impact_snapshots_school_id', 'impact_snapshots', ['school_id'])

    # 31. Audit Logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user_accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('impact_snapshots')
    op.drop_table('pilot_cohort_members')
    op.drop_table('pilot_cohorts')
    op.drop_table('worksheets')
    op.drop_table('teacher_activity_logs')
    op.drop_table('remedial_group_members')
    op.drop_table('remedial_groups')
    op.drop_table('attempt_responses')
    op.drop_table('assessment_attempts')
    op.drop_table('assessments')
    op.drop_table('level_change_proposals')
    op.drop_table('mastery_history')
    op.drop_table('student_mastery')
    op.drop_table('learning_resources')
    op.drop_table('questions')
    op.drop_table('concept_prerequisites')
    op.drop_table('concepts')
    op.drop_table('curriculum_topics')
    op.drop_table('curriculum_chapters')
    op.drop_table('curriculum_units')
    op.drop_table('teacher_assignments')
    op.drop_table('curriculum_subjects')
    op.drop_table('parent_child_links')
    op.drop_table('student_enrollments')
    op.drop_table('class_sections')
    op.drop_table('student_profiles')
    op.drop_table('auth_tokens')
    op.drop_table('user_accounts')
    op.drop_table('boards')
    op.drop_table('schools')
