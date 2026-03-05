"""Policy versioning service for tracking and comparing policy versions."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from healthcare_insurance_platform.core.logging import get_logger
from healthcare_insurance_platform.db.models import PolicyVersionDB, AffectedAnalysisDB
from healthcare_insurance_platform.models.policy import PolicyDocument
from healthcare_insurance_platform.models.policy_version import (
    AffectedAnalysis,
    PolicyVersion,
    PolicyVersionChange,
    PolicyVersionHistory,
    VersionChangeType,
    VersionComparison,
)
from healthcare_insurance_platform.services.base import BaseService

logger = get_logger(__name__)


class PolicyVersioningService(BaseService):
    """
    Service for managing policy versions and tracking changes.
    
    Handles version history tracking, version comparison, and flagging
    affected analyses when policies are updated.
    
    Validates: Requirements 12.3, 12.4
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None, *args, **kwargs):
        """Initialize policy versioning service."""
        super().__init__(*args, **kwargs)
        self.db_session = db_session
    
    async def create_version(
        self,
        policy_document: PolicyDocument,
        previous_version: Optional[PolicyDocument] = None,
        created_by: Optional[str] = None,
    ) -> PolicyVersion:
        """
        Create a new version entry for a policy document.
        
        This method:
        1. Creates a version snapshot of the policy
        2. Compares with previous version if provided
        3. Identifies and categorizes changes
        4. Stores version in database
        
        Args:
            policy_document: Current policy document
            previous_version: Previous version for comparison (if exists)
            created_by: User who created this version
            
        Returns:
            PolicyVersion instance
            
        Requirements: 12.3
        """
        self._log_operation(
            "create_version",
            policy_id=policy_document.policy_id,
            version=policy_document.version,
        )
        
        try:
            # Detect changes from previous version
            changes = []
            if previous_version:
                changes = self._detect_changes(previous_version, policy_document)
            
            # Create version object
            version = PolicyVersion(
                version_id=str(uuid.uuid4()),
                policy_id=policy_document.policy_id,
                version_number=policy_document.version,
                effective_date=datetime.combine(
                    policy_document.effective_date,
                    datetime.min.time()
                ).replace(tzinfo=timezone.utc),
                created_at=datetime.now(timezone.utc),
                created_by=created_by,
                coverage_amount=policy_document.coverage_amount,
                premium=policy_document.premium,
                exclusions_count=len(policy_document.exclusions),
                inclusions_count=len(policy_document.inclusions),
                changes_from_previous=changes,
                document_snapshot=policy_document.full_text,
                is_current=True,
            )
            
            # Store in database if session available
            if self.db_session:
                await self._store_version_in_db(version)
                
                # Mark previous versions as not current
                if previous_version:
                    await self._mark_previous_versions_as_old(policy_document.policy_id)
            
            logger.info(
                f"Created policy version: {version.version_number}",
                policy_id=policy_document.policy_id,
                changes_count=len(changes),
            )
            
            return version
            
        except Exception as e:
            self._log_error("create_version", e, policy_id=policy_document.policy_id)
            raise
    
    def _detect_changes(
        self,
        old_policy: PolicyDocument,
        new_policy: PolicyDocument,
    ) -> List[PolicyVersionChange]:
        """
        Detect changes between two policy versions.
        
        Args:
            old_policy: Previous policy version
            new_policy: New policy version
            
        Returns:
            List of detected changes
            
        Requirements: 12.4
        """
        changes = []
        
        # Check coverage amount change
        if old_policy.coverage_amount != new_policy.coverage_amount:
            change_pct = (
                (new_policy.coverage_amount - old_policy.coverage_amount) /
                old_policy.coverage_amount * 100
            )
            impact = 'critical' if abs(change_pct) > 20 else 'high' if abs(change_pct) > 10 else 'medium'
            
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.COVERAGE_CHANGE,
                field_name="coverage_amount",
                old_value=f"Rs. {old_policy.coverage_amount:,.0f}",
                new_value=f"Rs. {new_policy.coverage_amount:,.0f}",
                description=f"Coverage amount changed by {change_pct:+.1f}%",
                impact_level=impact,
            ))
        
        # Check premium change
        if old_policy.premium != new_policy.premium:
            change_pct = (
                (new_policy.premium - old_policy.premium) /
                old_policy.premium * 100
            )
            impact = 'high' if abs(change_pct) > 20 else 'medium' if abs(change_pct) > 10 else 'low'
            
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.PREMIUM_CHANGE,
                field_name="premium",
                old_value=f"Rs. {old_policy.premium:,.0f}",
                new_value=f"Rs. {new_policy.premium:,.0f}",
                description=f"Premium changed by {change_pct:+.1f}%",
                impact_level=impact,
            ))
        
        # Check exclusions changes
        old_exclusions = set(old_policy.exclusions)
        new_exclusions = set(new_policy.exclusions)
        
        added_exclusions = new_exclusions - old_exclusions
        removed_exclusions = old_exclusions - new_exclusions
        
        for exclusion in added_exclusions:
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.EXCLUSION_ADDED,
                field_name="exclusions",
                old_value=None,
                new_value=exclusion,
                description=f"New exclusion added: {exclusion}",
                impact_level='critical',  # Adding exclusions is critical
            ))
        
        for exclusion in removed_exclusions:
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.EXCLUSION_REMOVED,
                field_name="exclusions",
                old_value=exclusion,
                new_value=None,
                description=f"Exclusion removed: {exclusion}",
                impact_level='high',  # Removing exclusions is positive but still high impact
            ))
        
        # Check inclusions changes
        old_inclusions = set(old_policy.inclusions)
        new_inclusions = set(new_policy.inclusions)
        
        added_inclusions = new_inclusions - old_inclusions
        removed_inclusions = old_inclusions - new_inclusions
        
        for inclusion in added_inclusions:
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.INCLUSION_ADDED,
                field_name="inclusions",
                old_value=None,
                new_value=inclusion,
                description=f"New coverage added: {inclusion}",
                impact_level='high',  # Adding coverage is positive and high impact
            ))
        
        for inclusion in removed_inclusions:
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.INCLUSION_REMOVED,
                field_name="inclusions",
                old_value=inclusion,
                new_value=None,
                description=f"Coverage removed: {inclusion}",
                impact_level='critical',  # Removing coverage is critical
            ))
        
        # Check waiting period changes
        if (old_policy.waiting_periods.general != new_policy.waiting_periods.general or
            old_policy.waiting_periods.pre_existing != new_policy.waiting_periods.pre_existing):
            
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.WAITING_PERIOD_CHANGE,
                field_name="waiting_periods",
                old_value=f"General: {old_policy.waiting_periods.general} days, "
                          f"Pre-existing: {old_policy.waiting_periods.pre_existing} days",
                new_value=f"General: {new_policy.waiting_periods.general} days, "
                          f"Pre-existing: {new_policy.waiting_periods.pre_existing} days",
                description="Waiting periods have changed",
                impact_level='high',
            ))
        
        # Check PED policy changes
        if old_policy.ped_policy != new_policy.ped_policy:
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.TERMS_CHANGE,
                field_name="ped_policy",
                old_value=old_policy.ped_policy[:100] + "..." if len(old_policy.ped_policy) > 100 else old_policy.ped_policy,
                new_value=new_policy.ped_policy[:100] + "..." if len(new_policy.ped_policy) > 100 else new_policy.ped_policy,
                description="Pre-existing disease policy terms have changed",
                impact_level='critical',
            ))
        
        # Check claim process changes
        if old_policy.claim_process != new_policy.claim_process:
            changes.append(PolicyVersionChange(
                change_type=VersionChangeType.TERMS_CHANGE,
                field_name="claim_process",
                old_value=old_policy.claim_process[:100] + "..." if len(old_policy.claim_process) > 100 else old_policy.claim_process,
                new_value=new_policy.claim_process[:100] + "..." if len(new_policy.claim_process) > 100 else new_policy.claim_process,
                description="Claim process requirements have changed",
                impact_level='high',
            ))
        
        return changes
    
    async def compare_versions(
        self,
        policy_id: str,
        old_version_number: str,
        new_version_number: str,
    ) -> VersionComparison:
        """
        Compare two versions of a policy.
        
        Args:
            policy_id: Policy identifier
            old_version_number: Old version number
            new_version_number: New version number
            
        Returns:
            VersionComparison with detailed changes
            
        Requirements: 12.4
        """
        self._log_operation(
            "compare_versions",
            policy_id=policy_id,
            old_version=old_version_number,
            new_version=new_version_number,
        )
        
        try:
            # Retrieve versions from database
            old_version = await self._get_version_from_db(policy_id, old_version_number)
            new_version = await self._get_version_from_db(policy_id, new_version_number)
            
            if not old_version or not new_version:
                raise ValueError(f"Version not found for policy {policy_id}")
            
            # Get changes from the new version
            changes = new_version.changes_from_previous
            
            # Determine if changes affect analyses
            affects_analyses = any(change.affects_analyses() for change in changes)
            
            # Generate summary
            summary = self._generate_comparison_summary(changes)
            
            comparison = VersionComparison(
                policy_id=policy_id,
                policy_name="",  # Would need to fetch from policy document
                old_version=old_version_number,
                new_version=new_version_number,
                old_effective_date=old_version.effective_date,
                new_effective_date=new_version.effective_date,
                changes=changes,
                summary=summary,
                affects_existing_analyses=affects_analyses,
            )
            
            logger.info(
                f"Compared policy versions",
                policy_id=policy_id,
                changes_count=len(changes),
                affects_analyses=affects_analyses,
            )
            
            return comparison
            
        except Exception as e:
            self._log_error("compare_versions", e, policy_id=policy_id)
            raise
    
    def _generate_comparison_summary(self, changes: List[PolicyVersionChange]) -> str:
        """Generate a human-readable summary of changes."""
        if not changes:
            return "No changes detected between versions."
        
        critical_count = sum(1 for c in changes if c.impact_level == 'critical')
        high_count = sum(1 for c in changes if c.impact_level == 'high')
        
        summary_parts = [
            f"Total changes: {len(changes)}",
        ]
        
        if critical_count > 0:
            summary_parts.append(f"{critical_count} critical changes")
        if high_count > 0:
            summary_parts.append(f"{high_count} high impact changes")
        
        # Highlight key changes
        key_changes = []
        for change in changes[:3]:  # Top 3 changes
            key_changes.append(f"- {change.description}")
        
        summary = ". ".join(summary_parts) + ".\n\nKey changes:\n" + "\n".join(key_changes)
        
        return summary
    
    async def get_version_history(
        self,
        policy_id: str,
    ) -> PolicyVersionHistory:
        """
        Get complete version history for a policy.
        
        Args:
            policy_id: Policy identifier
            
        Returns:
            PolicyVersionHistory with all versions
            
        Requirements: 12.3
        """
        self._log_operation("get_version_history", policy_id=policy_id)
        
        try:
            if not self.db_session:
                raise RuntimeError("Database session not available")
            
            # Query all versions for this policy
            stmt = (
                select(PolicyVersionDB)
                .where(PolicyVersionDB.policy_id == policy_id)
                .order_by(PolicyVersionDB.effective_date.desc())
            )
            result = await self.db_session.execute(stmt)
            version_dbs = result.scalars().all()
            
            # Convert to PolicyVersion objects
            versions = [self._db_to_version(v) for v in version_dbs]
            
            history = PolicyVersionHistory(
                policy_id=policy_id,
                policy_name="",  # Would need to fetch from policy document
                provider_id="",  # Would need to fetch from policy document
                versions=versions,
            )
            
            logger.info(
                f"Retrieved version history",
                policy_id=policy_id,
                versions_count=len(versions),
            )
            
            return history
            
        except Exception as e:
            self._log_error("get_version_history", e, policy_id=policy_id)
            raise
    
    async def flag_affected_analyses(
        self,
        policy_id: str,
        new_version: PolicyVersion,
        analysis_ids: List[str],
    ) -> List[AffectedAnalysis]:
        """
        Flag analyses that are affected by a policy update.
        
        This method identifies analyses that used an older version of the policy
        and flags them as potentially outdated.
        
        Args:
            policy_id: Policy identifier
            new_version: New policy version
            analysis_ids: List of analysis IDs to check
            
        Returns:
            List of affected analyses
            
        Requirements: 12.4
        """
        self._log_operation(
            "flag_affected_analyses",
            policy_id=policy_id,
            new_version=new_version.version_number,
            analysis_count=len(analysis_ids),
        )
        
        try:
            affected = []
            
            # Get changes that affect analyses
            affecting_changes = [
                change for change in new_version.changes_from_previous
                if change.affects_analyses()
            ]
            
            if not affecting_changes:
                logger.info("No changes affect existing analyses")
                return affected
            
            # For each analysis, create an affected analysis record
            for analysis_id in analysis_ids:
                affected_analysis = AffectedAnalysis(
                    analysis_id=analysis_id,
                    analysis_type="unknown",  # Would need to fetch from analysis record
                    user_id=None,
                    created_at=datetime.now(timezone.utc),
                    policy_id=policy_id,
                    old_version="previous",  # Would need to fetch from analysis record
                    new_version=new_version.version_number,
                    affected_by_changes=affecting_changes,
                    flagged_at=datetime.now(timezone.utc),
                    notification_sent=False,
                )
                
                affected.append(affected_analysis)
                
                # Store in database if session available
                if self.db_session:
                    await self._store_affected_analysis_in_db(affected_analysis)
            
            logger.info(
                f"Flagged affected analyses",
                policy_id=policy_id,
                affected_count=len(affected),
            )
            
            return affected
            
        except Exception as e:
            self._log_error("flag_affected_analyses", e, policy_id=policy_id)
            raise
    
    async def get_affected_analyses(
        self,
        policy_id: str,
        user_id: Optional[str] = None,
    ) -> List[AffectedAnalysis]:
        """
        Get all analyses affected by policy updates.
        
        Args:
            policy_id: Policy identifier
            user_id: Optional user ID to filter by
            
        Returns:
            List of affected analyses
            
        Requirements: 12.4
        """
        self._log_operation(
            "get_affected_analyses",
            policy_id=policy_id,
            user_id=user_id,
        )
        
        try:
            if not self.db_session:
                raise RuntimeError("Database session not available")
            
            # Build query
            conditions = [AffectedAnalysisDB.policy_id == policy_id]
            if user_id:
                conditions.append(AffectedAnalysisDB.user_id == user_id)
            
            stmt = (
                select(AffectedAnalysisDB)
                .where(and_(*conditions))
                .order_by(AffectedAnalysisDB.flagged_at.desc())
            )
            result = await self.db_session.execute(stmt)
            affected_dbs = result.scalars().all()
            
            # Convert to AffectedAnalysis objects
            affected = [self._db_to_affected_analysis(a) for a in affected_dbs]
            
            logger.info(
                f"Retrieved affected analyses",
                policy_id=policy_id,
                count=len(affected),
            )
            
            return affected
            
        except Exception as e:
            self._log_error("get_affected_analyses", e, policy_id=policy_id)
            raise
    
    # Database helper methods
    
    async def _store_version_in_db(self, version: PolicyVersion) -> None:
        """Store version in database."""
        if not self.db_session:
            return
        
        version_db = PolicyVersionDB(
            version_id=version.version_id,
            policy_id=version.policy_id,
            version_number=version.version_number,
            effective_date=version.effective_date,
            created_at=version.created_at,
            created_by=version.created_by,
            coverage_amount=version.coverage_amount,
            premium=version.premium,
            exclusions_count=version.exclusions_count,
            inclusions_count=version.inclusions_count,
            changes_from_previous=[c.model_dump() for c in version.changes_from_previous],
            document_snapshot=version.document_snapshot,
            is_current=version.is_current,
        )
        
        self.db_session.add(version_db)
        await self.db_session.flush()
    
    async def _mark_previous_versions_as_old(self, policy_id: str) -> None:
        """Mark all previous versions as not current."""
        if not self.db_session:
            return
        
        stmt = (
            select(PolicyVersionDB)
            .where(PolicyVersionDB.policy_id == policy_id)
        )
        result = await self.db_session.execute(stmt)
        versions = result.scalars().all()
        
        for version in versions:
            version.is_current = False
        
        await self.db_session.flush()
    
    async def _get_version_from_db(
        self,
        policy_id: str,
        version_number: str,
    ) -> Optional[PolicyVersion]:
        """Retrieve version from database."""
        if not self.db_session:
            return None
        
        stmt = (
            select(PolicyVersionDB)
            .where(
                and_(
                    PolicyVersionDB.policy_id == policy_id,
                    PolicyVersionDB.version_number == version_number,
                )
            )
        )
        result = await self.db_session.execute(stmt)
        version_db = result.scalar_one_or_none()
        
        if not version_db:
            return None
        
        return self._db_to_version(version_db)
    
    def _db_to_version(self, version_db: PolicyVersionDB) -> PolicyVersion:
        """Convert database model to PolicyVersion."""
        changes = [
            PolicyVersionChange(**change_data)
            for change_data in version_db.changes_from_previous
        ]
        
        return PolicyVersion(
            version_id=version_db.version_id,
            policy_id=version_db.policy_id,
            version_number=version_db.version_number,
            effective_date=version_db.effective_date,
            created_at=version_db.created_at,
            created_by=version_db.created_by,
            coverage_amount=version_db.coverage_amount,
            premium=version_db.premium,
            exclusions_count=version_db.exclusions_count,
            inclusions_count=version_db.inclusions_count,
            changes_from_previous=changes,
            document_snapshot=version_db.document_snapshot,
            is_current=version_db.is_current,
        )
    
    async def _store_affected_analysis_in_db(self, affected: AffectedAnalysis) -> None:
        """Store affected analysis in database."""
        if not self.db_session:
            return
        
        affected_db = AffectedAnalysisDB(
            analysis_id=affected.analysis_id,
            analysis_type=affected.analysis_type,
            user_id=affected.user_id,
            created_at=affected.created_at,
            policy_id=affected.policy_id,
            old_version=affected.old_version,
            new_version=affected.new_version,
            affected_by_changes=[c.model_dump() for c in affected.affected_by_changes],
            flagged_at=affected.flagged_at,
            notification_sent=affected.notification_sent,
        )
        
        self.db_session.add(affected_db)
        await self.db_session.flush()
    
    def _db_to_affected_analysis(self, affected_db: AffectedAnalysisDB) -> AffectedAnalysis:
        """Convert database model to AffectedAnalysis."""
        changes = [
            PolicyVersionChange(**change_data)
            for change_data in affected_db.affected_by_changes
        ]
        
        return AffectedAnalysis(
            analysis_id=affected_db.analysis_id,
            analysis_type=affected_db.analysis_type,
            user_id=affected_db.user_id,
            created_at=affected_db.created_at,
            policy_id=affected_db.policy_id,
            old_version=affected_db.old_version,
            new_version=affected_db.new_version,
            affected_by_changes=changes,
            flagged_at=affected_db.flagged_at,
            notification_sent=affected_db.notification_sent,
        )
