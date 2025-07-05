from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import Session, select, func
import pytz
import json
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

from models import (
    User, Meeting, Participant, AvailabilityWindow, MeetingAnalysis, 
    MeetingPattern, MeetingType, MeetingStatus, engine
)


@dataclass
class TimeSlot:
    """Represents a potential meeting time slot"""
    start_time: datetime
    end_time: datetime
    timezone: str
    score: float = 0.0
    conflicts: List[str] = None
    participants_available: List[int] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
        if self.participants_available is None:
            self.participants_available = []


@dataclass
class SchedulingConflict:
    """Represents a scheduling conflict"""
    user_id: int
    user_name: str
    conflict_type: str  # "meeting", "availability", "workload"
    conflict_time: datetime
    conflict_details: str
    severity: str  # "high", "medium", "low"


class AIScheduler:
    """AI-powered meeting scheduler with conflict detection and optimization"""
    
    def __init__(self):
        self.session = None
    
    def get_session(self) -> Session:
        """Get database session"""
        if self.session is None:
            self.session = Session(engine)
        return self.session
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()
            self.session = None
    
    def find_optimal_time_slots(
        self, 
        participant_ids: List[int], 
        duration_minutes: int,
        start_date: datetime,
        end_date: datetime,
        timezone: str = "UTC",
        max_results: int = 10
    ) -> List[TimeSlot]:
        """Find optimal time slots for a meeting with given participants"""
        
        session = self.get_session()
        
        # Get all participants
        participants = session.exec(
            select(User).where(User.id.in_(participant_ids))
        ).all()
        
        if not participants:
            return []
        
        # Generate potential time slots
        potential_slots = self._generate_potential_slots(
            start_date, end_date, duration_minutes, timezone
        )
        
        # Score each slot
        scored_slots = []
        for slot in potential_slots:
            score = self._calculate_slot_score(slot, participants, session)
            if score > 0:  # Only include viable slots
                slot.score = score
                scored_slots.append(slot)
        
        # Sort by score (highest first) and return top results
        scored_slots.sort(key=lambda x: x.score, reverse=True)
        return scored_slots[:max_results]
    
    def detect_scheduling_conflicts(
        self, 
        user_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[SchedulingConflict]:
        """Detect scheduling conflicts for a user in a given time range"""
        
        session = self.get_session()
        conflicts = []
        
        # Get user
        user = session.get(User, user_id)
        if not user:
            return conflicts
        
        # Check for existing meeting conflicts
        meeting_conflicts = session.exec(
            select(Meeting)
            .join(Participant)
            .where(
                Participant.user_id == user_id,
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.start_time < end_time,
                Meeting.end_time > start_time
            )
        ).all()
        
        for meeting in meeting_conflicts:
            conflicts.append(SchedulingConflict(
                user_id=user_id,
                user_name=user.name,
                conflict_type="meeting",
                conflict_time=meeting.start_time,
                conflict_details=f"Overlaps with meeting: {meeting.title}",
                severity="high"
            ))
        
        # Check availability windows
        availability_conflicts = session.exec(
            select(AvailabilityWindow)
            .where(
                AvailabilityWindow.user_id == user_id,
                AvailabilityWindow.is_available == False,
                AvailabilityWindow.start_time < end_time,
                AvailabilityWindow.end_time > start_time
            )
        ).all()
        
        for availability in availability_conflicts:
            conflicts.append(SchedulingConflict(
                user_id=user_id,
                user_name=user.name,
                conflict_type="availability",
                conflict_time=availability.start_time,
                conflict_details=f"Unavailable: {availability.reason or 'Not specified'}",
                severity="medium"
            ))
        
        # Check workload (too many meetings in a day)
        day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        daily_meetings = session.exec(
            select(func.count(Meeting.id))
            .join(Participant)
            .where(
                Participant.user_id == user_id,
                Meeting.status == MeetingStatus.SCHEDULED,
                Meeting.start_time >= day_start,
                Meeting.start_time < day_end
            )
        ).first()
        
        if daily_meetings >= user.max_meetings_per_day:
            conflicts.append(SchedulingConflict(
                user_id=user_id,
                user_name=user.name,
                conflict_type="workload",
                conflict_time=start_time,
                conflict_details=f"Already has {daily_meetings} meetings today (limit: {user.max_meetings_per_day})",
                severity="medium"
            ))
        
        return conflicts
    
    def analyze_meeting_patterns(
        self, 
        user_id: int, 
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze meeting patterns for a user over a specified period"""
        
        session = self.get_session()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Get user's meetings in the period
        meetings = session.exec(
            select(Meeting)
            .join(Participant)
            .where(
                Participant.user_id == user_id,
                Meeting.start_time >= start_date,
                Meeting.start_time <= end_date
            )
        ).all()
        
        if not meetings:
            return {"error": "No meetings found for analysis"}
        
        # Analyze patterns
        patterns = {
            "total_meetings": len(meetings),
            "period_days": period_days,
            "average_meetings_per_day": len(meetings) / period_days,
            "meeting_types": self._analyze_meeting_types(meetings),
            "time_preferences": self._analyze_time_preferences(meetings),
            "duration_patterns": self._analyze_duration_patterns(meetings),
            "day_of_week_patterns": self._analyze_day_patterns(meetings),
            "productivity_trends": self._analyze_productivity_trends(meetings)
        }
        
        return patterns
    
    def calculate_workload_balance(self, team_member_ids: List[int]) -> Dict[str, Any]:
        """Calculate meeting workload balance across team members"""
        
        session = self.get_session()
        
        # Get recent meetings for all team members
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last week
        
        workload_data = {}
        
        for user_id in team_member_ids:
            user = session.get(User, user_id)
            if not user:
                continue
                
            # Get meetings
            meetings = session.exec(
                select(Meeting)
                .join(Participant)
                .where(
                    Participant.user_id == user_id,
                    Meeting.start_time >= start_date,
                    Meeting.start_time <= end_date
                )
            ).all()
            
            # Calculate workload metrics
            total_meeting_time = sum(m.duration_minutes for m in meetings)
            meeting_count = len(meetings)
            
            # Calculate organized meetings (higher workload)
            organized_meetings = session.exec(
                select(Meeting)
                .where(
                    Meeting.organizer_id == user_id,
                    Meeting.start_time >= start_date,
                    Meeting.start_time <= end_date
                )
            ).all()
            
            workload_data[user_id] = {
                "user_name": user.name,
                "total_meetings": meeting_count,
                "total_meeting_minutes": total_meeting_time,
                "organized_meetings": len(organized_meetings),
                "average_meeting_duration": total_meeting_time / meeting_count if meeting_count > 0 else 0,
                "meetings_per_day": meeting_count / 7,
                "workload_score": self._calculate_workload_score(
                    total_meeting_time, meeting_count, len(organized_meetings)
                )
            }
        
        # Calculate balance metrics
        workload_scores = [data["workload_score"] for data in workload_data.values()]
        
        return {
            "team_workload": workload_data,
            "balance_metrics": {
                "average_workload": np.mean(workload_scores) if workload_scores else 0,
                "workload_std": np.std(workload_scores) if workload_scores else 0,
                "balance_score": self._calculate_balance_score(workload_scores),
                "most_loaded_user": max(workload_data.items(), key=lambda x: x[1]["workload_score"])[0] if workload_data else None,
                "least_loaded_user": min(workload_data.items(), key=lambda x: x[1]["workload_score"])[0] if workload_data else None
            }
        }
    
    def generate_agenda_suggestions(
        self, 
        meeting_topic: str, 
        participant_ids: List[int], 
        duration_minutes: int
    ) -> List[str]:
        """Generate AI-powered agenda suggestions"""
        
        session = self.get_session()
        
        # Get participants
        participants = session.exec(
            select(User).where(User.id.in_(participant_ids))
        ).all()
        
        # Basic agenda structure based on duration and participants
        agenda_items = []
        
        # Opening (5 minutes for meetings > 15 min)
        if duration_minutes > 15:
            agenda_items.append("Opening & Introductions (5 min)")
        
        # Main content allocation
        main_content_time = duration_minutes - (10 if duration_minutes > 15 else 0)
        
        # Topic-based suggestions
        if "review" in meeting_topic.lower():
            agenda_items.extend([
                f"Review Progress & Updates ({main_content_time // 2} min)",
                f"Discussion & Feedback ({main_content_time // 2} min)"
            ])
        elif "planning" in meeting_topic.lower():
            agenda_items.extend([
                f"Goal Setting & Planning ({main_content_time // 2} min)",
                f"Timeline & Resource Allocation ({main_content_time // 2} min)"
            ])
        elif "brainstorm" in meeting_topic.lower():
            agenda_items.extend([
                f"Idea Generation ({main_content_time * 2 // 3} min)",
                f"Idea Evaluation & Selection ({main_content_time // 3} min)"
            ])
        else:
            # Generic structure
            agenda_items.extend([
                f"Topic Discussion: {meeting_topic} ({main_content_time * 2 // 3} min)",
                f"Decision Making & Next Steps ({main_content_time // 3} min)"
            ])
        
        # Closing (5 minutes for meetings > 15 min)
        if duration_minutes > 15:
            agenda_items.append("Action Items & Closing (5 min)")
        
        # Add participant-specific suggestions
        if len(participants) > 5:
            agenda_items.insert(1, "Round-robin updates (limit 2 min per person)")
        
        return agenda_items
    
    def score_meeting_effectiveness(self, meeting_id: int) -> Dict[str, Any]:
        """Score meeting effectiveness based on various factors"""
        
        session = self.get_session()
        
        meeting = session.get(Meeting, meeting_id)
        if not meeting:
            return {"error": "Meeting not found"}
        
        # Get participants
        participants = session.exec(
            select(Participant).where(Participant.meeting_id == meeting_id)
        ).all()
        
        # Calculate effectiveness metrics
        effectiveness_score = 0.0
        factors = {}
        
        # Duration appropriateness (20% weight)
        duration_score = self._score_duration_appropriateness(meeting, participants)
        factors["duration_appropriateness"] = duration_score
        effectiveness_score += duration_score * 0.2
        
        # Timing effectiveness (20% weight)
        timing_score = self._score_timing_effectiveness(meeting, participants)
        factors["timing_effectiveness"] = timing_score
        effectiveness_score += timing_score * 0.2
        
        # Participant engagement (25% weight)
        engagement_score = self._score_participant_engagement(participants)
        factors["participant_engagement"] = engagement_score
        effectiveness_score += engagement_score * 0.25
        
        # Agenda quality (15% weight)
        agenda_score = self._score_agenda_quality(meeting)
        factors["agenda_quality"] = agenda_score
        effectiveness_score += agenda_score * 0.15
        
        # Follow-up clarity (20% weight)
        followup_score = self._score_followup_clarity(meeting)
        factors["followup_clarity"] = followup_score
        effectiveness_score += followup_score * 0.2
        
        # Update meeting with effectiveness score
        meeting.effectiveness_score = effectiveness_score
        session.add(meeting)
        session.commit()
        
        return {
            "meeting_id": meeting_id,
            "overall_effectiveness_score": effectiveness_score,
            "score_breakdown": factors,
            "recommendations": self._generate_effectiveness_recommendations(factors)
        }
    
    def optimize_meeting_schedule(self, user_id: int) -> Dict[str, Any]:
        """Provide schedule optimization recommendations for a user"""
        
        session = self.get_session()
        
        user = session.get(User, user_id)
        if not user:
            return {"error": "User not found"}
        
        # Get upcoming meetings
        now = datetime.now()
        upcoming_meetings = session.exec(
            select(Meeting)
            .join(Participant)
            .where(
                Participant.user_id == user_id,
                Meeting.start_time > now,
                Meeting.status == MeetingStatus.SCHEDULED
            )
        ).all()
        
        recommendations = []
        
        # Check for back-to-back meetings
        back_to_back = self._find_back_to_back_meetings(upcoming_meetings)
        if back_to_back:
            recommendations.append({
                "type": "buffer_time",
                "priority": "high",
                "description": f"Found {len(back_to_back)} back-to-back meetings. Consider adding buffer time.",
                "affected_meetings": back_to_back
            })
        
        # Check for meeting-heavy days
        heavy_days = self._find_heavy_meeting_days(upcoming_meetings, user)
        if heavy_days:
            recommendations.append({
                "type": "workload_balance",
                "priority": "medium",
                "description": f"Found {len(heavy_days)} days with heavy meeting load.",
                "affected_days": heavy_days
            })
        
        # Check for optimal timing
        timing_suggestions = self._suggest_optimal_timing(upcoming_meetings, user)
        if timing_suggestions:
            recommendations.extend(timing_suggestions)
        
        return {
            "user_id": user_id,
            "user_name": user.name,
            "optimization_recommendations": recommendations,
            "current_schedule_score": self._calculate_schedule_score(upcoming_meetings, user)
        }
    
    # Helper methods
    def _generate_potential_slots(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        duration_minutes: int, 
        timezone: str
    ) -> List[TimeSlot]:
        """Generate potential time slots within the given date range"""
        
        slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Generate slots for business hours (9 AM to 5 PM)
            for hour in range(9, 17):
                for minute in [0, 30]:  # 30-minute intervals
                    slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=hour, minute=minute))
                    slot_start = pytz.timezone(timezone).localize(slot_start)
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Don't create slots that extend beyond business hours
                    if slot_end.hour <= 17:
                        slots.append(TimeSlot(
                            start_time=slot_start,
                            end_time=slot_end,
                            timezone=timezone
                        ))
            
            current_date += timedelta(days=1)
        
        return slots
    
    def _calculate_slot_score(self, slot: TimeSlot, participants: List[User], session: Session) -> float:
        """Calculate score for a potential time slot"""
        
        score = 10.0  # Base score
        available_participants = 0
        
        for participant in participants:
            # Check if participant is available
            conflicts = self.detect_scheduling_conflicts(
                participant.id, slot.start_time, slot.end_time
            )
            
            if not conflicts:
                available_participants += 1
                slot.participants_available.append(participant.id)
                
                # Bonus for preferred working hours
                user_tz = pytz.timezone(participant.timezone)
                local_time = slot.start_time.astimezone(user_tz)
                
                if participant.work_start_hour <= local_time.hour <= participant.work_end_hour:
                    score += 2.0
                
                # Bonus for preferred meeting times (assuming 10 AM and 2 PM are optimal)
                if local_time.hour in [10, 14]:
                    score += 1.0
            else:
                # Penalty for conflicts
                high_severity_conflicts = sum(1 for c in conflicts if c.severity == "high")
                score -= (high_severity_conflicts * 5.0) + (len(conflicts) * 2.0)
                
                slot.conflicts.extend([f"{participant.name}: {c.conflict_details}" for c in conflicts])
        
        # Penalty if not all participants are available
        availability_ratio = available_participants / len(participants)
        score *= availability_ratio
        
        return max(0, score)  # Ensure non-negative score
    
    def _analyze_meeting_types(self, meetings: List[Meeting]) -> Dict[str, int]:
        """Analyze distribution of meeting types"""
        type_counts = defaultdict(int)
        for meeting in meetings:
            type_counts[meeting.meeting_type.value] += 1
        return dict(type_counts)
    
    def _analyze_time_preferences(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze time preferences from meeting history"""
        hour_counts = defaultdict(int)
        for meeting in meetings:
            hour_counts[meeting.start_time.hour] += 1
        
        most_common_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 9
        
        return {
            "hourly_distribution": dict(hour_counts),
            "preferred_start_hour": most_common_hour,
            "morning_meetings": sum(1 for m in meetings if m.start_time.hour < 12),
            "afternoon_meetings": sum(1 for m in meetings if m.start_time.hour >= 12)
        }
    
    def _analyze_duration_patterns(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze meeting duration patterns"""
        durations = [m.duration_minutes for m in meetings]
        
        return {
            "average_duration": np.mean(durations) if durations else 0,
            "median_duration": np.median(durations) if durations else 0,
            "most_common_duration": max(set(durations), key=durations.count) if durations else 0,
            "duration_distribution": dict(zip(*np.unique(durations, return_counts=True))) if durations else {}
        }
    
    def _analyze_day_patterns(self, meetings: List[Meeting]) -> Dict[str, int]:
        """Analyze day of week patterns"""
        day_counts = defaultdict(int)
        for meeting in meetings:
            day_name = meeting.start_time.strftime("%A")
            day_counts[day_name] += 1
        return dict(day_counts)
    
    def _analyze_productivity_trends(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze productivity trends from meeting effectiveness scores"""
        scored_meetings = [m for m in meetings if m.effectiveness_score is not None]
        
        if not scored_meetings:
            return {"message": "No effectiveness scores available"}
        
        scores = [m.effectiveness_score for m in scored_meetings]
        
        return {
            "average_effectiveness": np.mean(scores),
            "effectiveness_trend": "improving" if scores[-1] > scores[0] else "declining",
            "best_performing_type": self._find_best_performing_meeting_type(scored_meetings),
            "score_distribution": {
                "high": sum(1 for s in scores if s >= 8.0),
                "medium": sum(1 for s in scores if 5.0 <= s < 8.0),
                "low": sum(1 for s in scores if s < 5.0)
            }
        }
    
    def _calculate_workload_score(self, total_minutes: int, meeting_count: int, organized_count: int) -> float:
        """Calculate workload score based on various factors"""
        # Base score from total meeting time
        base_score = total_minutes / 60.0  # Convert to hours
        
        # Add penalty for too many meetings
        if meeting_count > 20:  # More than 20 meetings per week
            base_score += (meeting_count - 20) * 0.5
        
        # Add penalty for organizing meetings (more responsibility)
        base_score += organized_count * 0.3
        
        return base_score
    
    def _calculate_balance_score(self, workload_scores: List[float]) -> float:
        """Calculate team balance score (0-10, 10 being perfectly balanced)"""
        if not workload_scores:
            return 0.0
        
        # Calculate coefficient of variation
        mean_score = np.mean(workload_scores)
        std_score = np.std(workload_scores)
        
        if mean_score == 0:
            return 10.0
        
        cv = std_score / mean_score
        
        # Convert to 0-10 scale (lower CV = better balance)
        balance_score = max(0, 10 - (cv * 10))
        return balance_score
    
    def _score_duration_appropriateness(self, meeting: Meeting, participants: List[Participant]) -> float:
        """Score how appropriate the meeting duration is"""
        duration = meeting.duration_minutes
        participant_count = len(participants)
        
        # Base score
        score = 5.0
        
        # Optimal durations by meeting type
        optimal_durations = {
            MeetingType.ONE_ON_ONE: 30,
            MeetingType.TEAM_MEETING: 60,
            MeetingType.ALL_HANDS: 45,
            MeetingType.CLIENT_MEETING: 60,
            MeetingType.INTERVIEW: 45,
            MeetingType.TRAINING: 90
        }
        
        optimal = optimal_durations.get(meeting.meeting_type, 60)
        
        # Score based on deviation from optimal
        deviation = abs(duration - optimal) / optimal
        score -= deviation * 5.0
        
        # Adjust for participant count
        if participant_count > 5 and duration < 45:
            score -= 2.0  # Too short for large group
        
        return max(0, min(10, score))
    
    def _score_timing_effectiveness(self, meeting: Meeting, participants: List[Participant]) -> float:
        """Score how effective the meeting timing is"""
        # This is a simplified version - in practice, you'd check participant timezones
        score = 5.0
        
        hour = meeting.start_time.hour
        
        # Optimal meeting times
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            score += 3.0
        elif 8 <= hour <= 9 or 16 <= hour <= 17:
            score += 1.0
        else:
            score -= 2.0
        
        return max(0, min(10, score))
    
    def _score_participant_engagement(self, participants: List[Participant]) -> float:
        """Score participant engagement"""
        if not participants:
            return 0.0
        
        # Check participation levels if available
        engagement_scores = [p.participation_level for p in participants if p.participation_level is not None]
        
        if engagement_scores:
            return np.mean(engagement_scores)
        
        # Fallback: score based on response status
        responses = [p.response_status for p in participants]
        accepted = sum(1 for r in responses if r == "accepted")
        
        return (accepted / len(participants)) * 10.0
    
    def _score_agenda_quality(self, meeting: Meeting) -> float:
        """Score agenda quality"""
        if not meeting.agenda:
            return 2.0  # Low score for no agenda
        
        # Simple scoring based on agenda content
        agenda_length = len(meeting.agenda)
        
        if agenda_length < 50:
            return 3.0
        elif agenda_length < 200:
            return 7.0
        else:
            return 9.0
    
    def _score_followup_clarity(self, meeting: Meeting) -> float:
        """Score follow-up clarity"""
        # In practice, this would analyze follow-up actions
        # For now, return a base score
        return 6.0
    
    def _generate_effectiveness_recommendations(self, factors: Dict[str, float]) -> List[str]:
        """Generate recommendations based on effectiveness factors"""
        recommendations = []
        
        if factors["duration_appropriateness"] < 5.0:
            recommendations.append("Consider adjusting meeting duration to be more appropriate for the meeting type")
        
        if factors["timing_effectiveness"] < 5.0:
            recommendations.append("Schedule meetings during optimal hours (9-11 AM or 2-4 PM)")
        
        if factors["participant_engagement"] < 5.0:
            recommendations.append("Improve participant engagement through better preparation and interaction")
        
        if factors["agenda_quality"] < 5.0:
            recommendations.append("Create detailed agendas with clear objectives and time allocations")
        
        return recommendations
    
    def _find_back_to_back_meetings(self, meetings: List[Meeting]) -> List[Dict[str, Any]]:
        """Find back-to-back meetings"""
        meetings_sorted = sorted(meetings, key=lambda x: x.start_time)
        back_to_back = []
        
        for i in range(len(meetings_sorted) - 1):
            current = meetings_sorted[i]
            next_meeting = meetings_sorted[i + 1]
            
            if current.end_time >= next_meeting.start_time:
                back_to_back.append({
                    "meeting1": current.title,
                    "meeting2": next_meeting.title,
                    "gap_minutes": (next_meeting.start_time - current.end_time).total_seconds() / 60
                })
        
        return back_to_back
    
    def _find_heavy_meeting_days(self, meetings: List[Meeting], user: User) -> List[Dict[str, Any]]:
        """Find days with heavy meeting load"""
        daily_counts = defaultdict(int)
        daily_minutes = defaultdict(int)
        
        for meeting in meetings:
            day_key = meeting.start_time.date()
            daily_counts[day_key] += 1
            daily_minutes[day_key] += meeting.duration_minutes
        
        heavy_days = []
        for day, count in daily_counts.items():
            if count > user.max_meetings_per_day or daily_minutes[day] > 480:  # 8 hours
                heavy_days.append({
                    "date": day.isoformat(),
                    "meeting_count": count,
                    "total_minutes": daily_minutes[day]
                })
        
        return heavy_days
    
    def _suggest_optimal_timing(self, meetings: List[Meeting], user: User) -> List[Dict[str, Any]]:
        """Suggest optimal timing for meetings"""
        suggestions = []
        
        for meeting in meetings:
            hour = meeting.start_time.hour
            
            # Check if meeting is outside optimal hours
            if hour < 9 or hour > 16:
                suggestions.append({
                    "type": "timing_optimization",
                    "priority": "medium",
                    "description": f"Meeting '{meeting.title}' scheduled outside optimal hours",
                    "suggestion": "Consider rescheduling to 9-11 AM or 2-4 PM",
                    "meeting_id": meeting.id
                })
        
        return suggestions
    
    def _calculate_schedule_score(self, meetings: List[Meeting], user: User) -> float:
        """Calculate overall schedule score"""
        if not meetings:
            return 10.0
        
        score = 10.0
        
        # Penalty for back-to-back meetings
        back_to_back = self._find_back_to_back_meetings(meetings)
        score -= len(back_to_back) * 0.5
        
        # Penalty for heavy days
        heavy_days = self._find_heavy_meeting_days(meetings, user)
        score -= len(heavy_days) * 1.0
        
        # Penalty for off-hours meetings
        off_hours = sum(1 for m in meetings if m.start_time.hour < 9 or m.start_time.hour > 16)
        score -= off_hours * 0.3
        
        return max(0, score)
    
    def _find_best_performing_meeting_type(self, meetings: List[Meeting]) -> str:
        """Find the meeting type with best average effectiveness score"""
        type_scores = defaultdict(list)
        
        for meeting in meetings:
            type_scores[meeting.meeting_type.value].append(meeting.effectiveness_score)
        
        best_type = max(type_scores.items(), key=lambda x: np.mean(x[1]))[0] if type_scores else "unknown"
        return best_type 