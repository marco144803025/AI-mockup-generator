"""
Feedback Layer - Human oversight and approval workflows
"""

import time
import logging
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class ApprovalStatus(Enum):
    """Approval status for feedback items"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class FeedbackType(Enum):
    """Types of feedback that can be requested"""
    TEMPLATE_SELECTION = "template_selection"
    DESIGN_CHANGES = "design_changes"
    FUNCTIONALITY_APPROVAL = "functionality_approval"
    FINAL_APPROVAL = "final_approval"
    CONTENT_REVIEW = "content_review"

@dataclass
class FeedbackRequest:
    """Represents a feedback request"""
    id: str
    type: FeedbackType
    title: str
    description: str
    data: Dict[str, Any]
    status: ApprovalStatus
    created_at: datetime
    deadline: Optional[datetime] = None
    assigned_to: Optional[str] = None
    priority: str = "medium"
    metadata: Dict[str, Any] = None

class FeedbackLayer:
    """Handles human oversight and approval workflows"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.feedback_requests: Dict[str, FeedbackRequest] = {}
        self.approval_callbacks: Dict[str, Callable] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        
    def create_feedback_request(
        self,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        data: Dict[str, Any],
        deadline_hours: int = 24,
        assigned_to: Optional[str] = None,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackRequest:
        """Create a new feedback request"""
        
        request_id = f"feedback_{int(time.time())}_{feedback_type.value}"
        deadline = datetime.now() + timedelta(hours=deadline_hours)
        
        feedback_request = FeedbackRequest(
            id=request_id,
            type=feedback_type,
            title=title,
            description=description,
            data=data,
            status=ApprovalStatus.PENDING,
            created_at=datetime.now(),
            deadline=deadline,
            assigned_to=assigned_to,
            priority=priority,
            metadata=metadata or {}
        )
        
        self.feedback_requests[request_id] = feedback_request
        self.logger.info(f"Created feedback request: {request_id} - {title}")
        
        return feedback_request
    
    def get_pending_feedback(self, feedback_type: Optional[FeedbackType] = None) -> List[FeedbackRequest]:
        """Get all pending feedback requests"""
        pending = [
            req for req in self.feedback_requests.values()
            if req.status == ApprovalStatus.PENDING
        ]
        
        if feedback_type:
            pending = [req for req in pending if req.type == feedback_type]
        
        return sorted(pending, key=lambda x: x.created_at)
    
    def approve_feedback(self, request_id: str, approver: str, comments: str = "") -> bool:
        """Approve a feedback request"""
        if request_id not in self.feedback_requests:
            self.logger.error(f"Feedback request {request_id} not found")
            return False
        
        request = self.feedback_requests[request_id]
        request.status = ApprovalStatus.APPROVED
        
        # Record approval
        approval_record = {
            "request_id": request_id,
            "action": "approved",
            "approver": approver,
            "comments": comments,
            "timestamp": datetime.now(),
            "request_data": request.data
        }
        self.feedback_history.append(approval_record)
        
        # Execute callback if registered
        if request_id in self.approval_callbacks:
            try:
                self.approval_callbacks[request_id](request.data, approval_record)
            except Exception as e:
                self.logger.error(f"Error executing approval callback: {e}")
        
        self.logger.info(f"Feedback request {request_id} approved by {approver}")
        return True
    
    def reject_feedback(self, request_id: str, rejector: str, reason: str, revision_notes: str = "") -> bool:
        """Reject a feedback request"""
        if request_id not in self.feedback_requests:
            self.logger.error(f"Feedback request {request_id} not found")
            return False
        
        request = self.feedback_requests[request_id]
        request.status = ApprovalStatus.REJECTED
        
        # Record rejection
        rejection_record = {
            "request_id": request_id,
            "action": "rejected",
            "rejector": rejector,
            "reason": reason,
            "revision_notes": revision_notes,
            "timestamp": datetime.now(),
            "request_data": request.data
        }
        self.feedback_history.append(rejection_record)
        
        self.logger.info(f"Feedback request {request_id} rejected by {rejector}: {reason}")
        return True
    
    def request_revision(self, request_id: str, reviewer: str, revision_notes: str) -> bool:
        """Request revision for a feedback request"""
        if request_id not in self.feedback_requests:
            self.logger.error(f"Feedback request {request_id} not found")
            return False
        
        request = self.feedback_requests[request_id]
        request.status = ApprovalStatus.NEEDS_REVISION
        
        # Record revision request
        revision_record = {
            "request_id": request_id,
            "action": "revision_requested",
            "reviewer": reviewer,
            "revision_notes": revision_notes,
            "timestamp": datetime.now(),
            "request_data": request.data
        }
        self.feedback_history.append(revision_record)
        
        self.logger.info(f"Revision requested for {request_id} by {reviewer}")
        return True
    
    def register_approval_callback(self, request_id: str, callback: Callable):
        """Register a callback to be executed when feedback is approved"""
        self.approval_callbacks[request_id] = callback
    
    def get_feedback_history(self, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get feedback history"""
        if request_id:
            return [record for record in self.feedback_history if record["request_id"] == request_id]
        return self.feedback_history
    
    def check_deadlines(self) -> List[FeedbackRequest]:
        """Check for overdue feedback requests"""
        now = datetime.now()
        overdue = [
            req for req in self.feedback_requests.values()
            if req.status == ApprovalStatus.PENDING and req.deadline and req.deadline < now
        ]
        return overdue
    
    def auto_approve_low_priority(self, auto_approver: str = "system") -> List[str]:
        """Auto-approve low priority feedback requests that are close to deadline"""
        now = datetime.now()
        auto_approved = []
        
        for request in self.feedback_requests.values():
            if (request.status == ApprovalStatus.PENDING and 
                request.priority == "low" and 
                request.deadline and 
                (request.deadline - now).total_seconds() < 3600):  # 1 hour before deadline
                
                self.approve_feedback(request.id, auto_approver, "Auto-approved due to low priority and deadline")
                auto_approved.append(request.id)
        
        return auto_approved
    
    def create_template_selection_feedback(self, templates: List[Dict[str, Any]], reasoning: str) -> FeedbackRequest:
        """Create feedback request for template selection"""
        return self.create_feedback_request(
            feedback_type=FeedbackType.TEMPLATE_SELECTION,
            title="Template Selection Approval",
            description=f"Please review and approve the selected template. Reasoning: {reasoning}",
            data={
                "templates": templates,
                "reasoning": reasoning,
                "recommended_template": templates[0] if templates else None
            },
            deadline_hours=48,
            priority="high"
        )
    
    def create_design_changes_feedback(self, changes: List[Dict[str, Any]], before_data: Dict[str, Any], after_data: Dict[str, Any]) -> FeedbackRequest:
        """Create feedback request for design changes"""
        return self.create_feedback_request(
            feedback_type=FeedbackType.DESIGN_CHANGES,
            title="Design Changes Approval",
            description=f"Please review {len(changes)} design changes",
            data={
                "changes": changes,
                "before": before_data,
                "after": after_data,
                "summary": f"{len(changes)} changes proposed"
            },
            deadline_hours=24,
            priority="medium"
        )
    
    def create_final_approval_feedback(self, final_template: Dict[str, Any], project_summary: str) -> FeedbackRequest:
        """Create feedback request for final approval"""
        return self.create_feedback_request(
            feedback_type=FeedbackType.FINAL_APPROVAL,
            title="Final Project Approval",
            description="Please review and approve the final UI mockup",
            data={
                "final_template": final_template,
                "project_summary": project_summary,
                "deliverables": ["HTML", "CSS", "Preview Images"]
            },
            deadline_hours=72,
            priority="high"
        ) 