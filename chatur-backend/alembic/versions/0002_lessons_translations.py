"""Add structured lessons, translation cache, generation log (additive only).

Revision ID: 0002_lessons_translations
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_lessons_translations'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if 'concept_lessons' in existing:  # DB was bootstrapped via create_all; nothing to do
        return
    op.create_table('concept_lessons',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('concept_id', sa.String(36), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='generated'),
        sa.Column('validation_report', sa.JSON, nullable=True),
        sa.Column('sources', sa.JSON, nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('approved_by', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('concept_id', 'version', name='uq_lesson_concept_version'))
    op.create_index('ix_concept_lessons_concept_id', 'concept_lessons', ['concept_id'])
    op.create_index('ix_concept_lessons_status', 'concept_lessons', ['status'])
    op.create_table('lesson_translations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('lesson_id', sa.String(36), sa.ForeignKey('concept_lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lang', sa.String(5), nullable=False),
        sa.Column('source_version', sa.Integer, nullable=False),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('lesson_id', 'lang', name='uq_translation_lesson_lang'))
    op.create_index('ix_lesson_translations_lesson_id', 'lesson_translations', ['lesson_id'])
    op.create_index('ix_lesson_translations_lang', 'lesson_translations', ['lang'])
    op.create_table('content_generation_log',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('concept_id', sa.String(36), nullable=True),
        sa.Column('action', sa.String(30), nullable=False),
        sa.Column('ok', sa.Integer, nullable=False, server_default='1'),
        sa.Column('detail', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_content_generation_log_concept_id', 'content_generation_log', ['concept_id'])


def downgrade() -> None:
    op.drop_table('content_generation_log')
    op.drop_table('lesson_translations')
    op.drop_table('concept_lessons')
