"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('encrypted_password', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100)),
        sa.Column('full_name', sa.String(200)),
        sa.Column('phone', sa.String(50)),
        sa.Column('job_title', sa.String(100)),
        sa.Column('department', sa.String(100)),
        sa.Column('global_role', sa.String(50), server_default='sales_rep'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('email_verified', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    
    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(255), nullable=False, unique=True),
        sa.Column('subscription_tier', sa.String(50), server_default='starter'),
        sa.Column('max_storage_gb', sa.Integer, server_default='5'),
        sa.Column('billing_email', sa.String(255)),
        sa.Column('support_email', sa.String(255)),
        sa.Column('phone', sa.String(50)),
        sa.Column('company_address', sa.String(500)),
        sa.Column('primary_color', sa.String(20), server_default='#3B82F6'),
        sa.Column('environment', sa.String(50), server_default='production'),
        sa.Column('description', sa.String(1000)),
        sa.Column('max_users', sa.Integer, server_default='10'),
        sa.Column('max_monthly_prospects', sa.Integer, server_default='1000'),
        sa.Column('max_monthly_emails', sa.Integer, server_default='5000'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('features', JSON, server_default='{}'),
        sa.Column('settings', JSON, server_default='{}'),
        sa.Column('security_settings', JSON, server_default='{}'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('idx_organizations_url', 'organizations', ['url'])
    
    # Create user_organizations junction table
    op.create_table(
        'user_organizations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), server_default='sales_rep'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_primary', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_user_orgs_user', 'user_organizations', ['user_id'])
    op.create_index('idx_user_orgs_org', 'user_organizations', ['organization_id'])
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('target', sa.String(50), server_default='all_users'),
        sa.Column('target_spec', JSON, server_default='{}'),
        sa.Column('priority', sa.Integer, server_default='1'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    op.create_index('idx_notifications_type', 'notifications', ['type'])
    op.create_index('idx_notifications_active', 'notifications', ['is_active'])

    # Create sync_events table - tracks cross-service synchronization
    op.create_table(
        'sync_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('payload', JSON, server_default='{}'),
        sa.Column('response_status_code', sa.Integer),
        sa.Column('response_body', sa.Text),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('last_attempted_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
    )
    op.create_index('idx_sync_events_entity_type', 'sync_events', ['entity_type'])
    op.create_index('idx_sync_events_entity_id', 'sync_events', ['entity_id'])
    op.create_index('idx_sync_events_status', 'sync_events', ['status'])


def downgrade() -> None:
    op.drop_table('sync_events')
    op.drop_table('notifications')
    op.drop_table('user_organizations')
    op.drop_table('organizations')
    op.drop_table('users')
