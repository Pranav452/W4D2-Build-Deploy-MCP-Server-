"""
Sample data generator for Smart Meeting Assistant
Creates 60+ meetings across multiple users with different timezones and realistic patterns
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlmodel import Session, select
import pytz

from models import (
    User, Meeting, Participant, AvailabilityWindow, MeetingAnalysis,
    MeetingPattern, MeetingType, MeetingStatus, UserRole,
    engine, create_db_and_tables
)


class SampleDataGenerator:
    """Generate realistic sample data for the meeting assistant"""
    
    def __init__(self):
        self.users = []
        self.meetings = []
        self.timezones = [
            "America/New_York", "America/Los_Angeles", "America/Chicago",
            "Europe/London", "Europe/Paris", "Europe/Berlin",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata",
            "Australia/Sydney", "America/Toronto", "UTC"
        ]
        
        # Meeting topics for different types
        self.meeting_topics = {
            MeetingType.ONE_ON_ONE: [
                "Weekly Check-in", "Performance Review", "Career Development",
                "Project Update", "Feedback Session", "Goal Setting",
                "Mentoring Session", "Problem Solving", "Status Update"
            ],
            MeetingType.TEAM_MEETING: [
                "Sprint Planning", "Daily Standup", "Sprint Review",
                "Team Retrospective", "Weekly Team Sync", "Project Kickoff",
                "Quarterly Planning", "Team Building", "Knowledge Sharing"
            ],
            MeetingType.ALL_HANDS: [
                "Company All-Hands", "Quarterly Review", "Product Launch",
                "Town Hall", "Strategy Update", "Annual Planning",
                "Company Updates", "Leadership Q&A"
            ],
            MeetingType.CLIENT_MEETING: [
                "Client Presentation", "Requirements Gathering", "Status Update",
                "Project Review", "Contract Discussion", "Proposal Meeting",
                "Feedback Session", "Partnership Discussion"
            ],
            MeetingType.INTERVIEW: [
                "Technical Interview", "Behavioral Interview", "Panel Interview",
                "Phone Screening", "Final Round", "Culture Fit Interview",
                "Reference Check", "Offer Discussion"
            ],
            MeetingType.TRAINING: [
                "Technical Training", "Onboarding Session", "Skills Workshop",
                "Certification Training", "Security Training", "Compliance Training",
                "Leadership Development", "Product Training"
            ]
        }
        
        # Company departments
        self.departments = [
            "Engineering", "Product", "Design", "Marketing", "Sales",
            "Customer Success", "Human Resources", "Finance", "Operations"
        ]
        
        # Meeting descriptions
        self.descriptions = {
            MeetingType.ONE_ON_ONE: [
                "Regular check-in to discuss progress and challenges",
                "Performance review and career development discussion",
                "Project status update and next steps planning"
            ],
            MeetingType.TEAM_MEETING: [
                "Weekly team sync to align on priorities and blockers",
                "Sprint planning for the upcoming development cycle",
                "Retrospective to improve team processes and collaboration"
            ],
            MeetingType.ALL_HANDS: [
                "Company-wide meeting to share updates and strategic direction",
                "Quarterly review of company performance and goals",
                "Product launch announcement and roadmap presentation"
            ],
            MeetingType.CLIENT_MEETING: [
                "Client presentation of project progress and deliverables",
                "Requirements gathering session for new project phase",
                "Regular check-in with client stakeholders"
            ],
            MeetingType.INTERVIEW: [
                "Technical interview to assess candidate's skills and experience",
                "Behavioral interview focusing on culture fit and soft skills",
                "Final round interview with senior leadership"
            ],
            MeetingType.TRAINING: [
                "Technical training session on new tools and technologies",
                "Onboarding session for new team members",
                "Skills development workshop for professional growth"
            ]
        }
    
    def create_users(self, count: int = 25) -> List[User]:
        """Create sample users with diverse profiles"""
        
        first_names = [
            "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
            "Ivy", "Jack", "Karen", "Leo", "Maya", "Noah", "Olivia", "Paul",
            "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yuki"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez",
            "Moore", "Martin", "Jackson", "Thompson", "White", "Lopez", "Lee", "Gonzalez",
            "Harris", "Clark"
        ]
        
        roles = [UserRole.ADMIN, UserRole.MANAGER, UserRole.EMPLOYEE, UserRole.GUEST]
        role_weights = [0.1, 0.2, 0.65, 0.05]  # Most are employees
        
        users = []
        
        for i in range(count):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]
            
            # Ensure unique combinations
            if i >= len(first_names):
                first_name = f"{first_name}{i // len(first_names)}"
            
            user = User(
                name=f"{first_name} {last_name}",
                email=f"{first_name.lower()}.{last_name.lower()}{i}@company.com",
                role=random.choices(roles, weights=role_weights)[0],
                timezone=random.choice(self.timezones),
                work_start_hour=random.choice([8, 9, 10]),
                work_end_hour=random.choice([16, 17, 18]),
                work_days=random.choice([
                    "1,2,3,4,5",  # Monday-Friday
                    "1,2,3,4,5,6",  # Monday-Saturday
                    "2,3,4,5,6"  # Tuesday-Saturday
                ]),
                max_meetings_per_day=random.choice([6, 8, 10, 12]),
                preferred_meeting_duration=random.choice([30, 45, 60]),
                buffer_time=random.choice([10, 15, 20])
            )
            
            users.append(user)
        
        return users
    
    def create_meetings(self, users: List[User], count: int = 80) -> List[Meeting]:
        """Create sample meetings with realistic patterns"""
        
        meetings = []
        now = datetime.now()
        
        # Create meetings spread over past 3 months and next 1 month
        start_date = now - timedelta(days=90)
        end_date = now + timedelta(days=30)
        
        meeting_types = list(MeetingType)
        
        # Weight distribution for meeting types (more realistic)
        type_weights = [0.25, 0.35, 0.05, 0.15, 0.10, 0.10]  # team_meeting most common
        
        for i in range(count):
            meeting_type = random.choices(meeting_types, weights=type_weights)[0]
            
            # Generate meeting time
            meeting_date = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            
            # Prefer business hours
            hour = random.choices(
                range(8, 18),
                weights=[1, 3, 5, 5, 5, 3, 3, 5, 5, 3]  # Peak at 10-11 AM and 2-3 PM
            )[0]
            
            minute = random.choice([0, 15, 30, 45])
            
            meeting_start = meeting_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )
            
            # Duration based on meeting type
            duration_map = {
                MeetingType.ONE_ON_ONE: [30, 45],
                MeetingType.TEAM_MEETING: [30, 60, 90],
                MeetingType.ALL_HANDS: [45, 60],
                MeetingType.CLIENT_MEETING: [45, 60, 90],
                MeetingType.INTERVIEW: [30, 45, 60],
                MeetingType.TRAINING: [60, 90, 120]
            }
            
            duration = random.choice(duration_map[meeting_type])
            meeting_end = meeting_start + timedelta(minutes=duration)
            
            # Select organizer
            organizer = random.choice(users)
            
            # Select participants based on meeting type
            if meeting_type == MeetingType.ONE_ON_ONE:
                participants = random.sample(users, 2)
            elif meeting_type == MeetingType.ALL_HANDS:
                participants = random.sample(users, random.randint(15, len(users)))
            elif meeting_type == MeetingType.TEAM_MEETING:
                participants = random.sample(users, random.randint(4, 8))
            elif meeting_type == MeetingType.CLIENT_MEETING:
                participants = random.sample(users, random.randint(3, 6))
            elif meeting_type == MeetingType.INTERVIEW:
                participants = random.sample(users, random.randint(2, 4))
            else:  # TRAINING
                participants = random.sample(users, random.randint(8, 15))
            
            # Ensure organizer is in participants
            if organizer not in participants:
                participants.append(organizer)
            
            # Select topic and description
            topic = random.choice(self.meeting_topics[meeting_type])
            description = random.choice(self.descriptions[meeting_type])
            
            # Create meeting
            meeting = Meeting(
                title=topic,
                description=description,
                meeting_type=meeting_type,
                start_time=meeting_start,
                end_time=meeting_end,
                timezone=organizer.timezone,
                location=self._generate_location(meeting_type),
                organizer_id=organizer.id,
                status=MeetingStatus.COMPLETED if meeting_start < now else MeetingStatus.SCHEDULED,
                effectiveness_score=random.uniform(4.0, 9.5) if meeting_start < now else None,
                productivity_rating=random.uniform(3.5, 9.0) if meeting_start < now else None,
                engagement_level=random.uniform(5.0, 9.5) if meeting_start < now else None
            )
            
            # Store participant IDs for later use
            meeting._participant_ids = [p.id for p in participants]
            
            meetings.append(meeting)
        
        return meetings
    
    def create_participants(self, meetings: List[Meeting]) -> List[Participant]:
        """Create participant records for meetings"""
        
        participants = []
        response_statuses = ["accepted", "pending", "declined", "tentative"]
        status_weights = [0.7, 0.15, 0.1, 0.05]  # Most accept meetings
        
        for meeting in meetings:
            for user_id in meeting._participant_ids:
                participant = Participant(
                    user_id=user_id,
                    meeting_id=meeting.id,
                    is_required=random.choice([True, True, True, False]),  # Most are required
                    response_status=random.choices(response_statuses, weights=status_weights)[0],
                    attended=random.choice([True, False]) if meeting.status == MeetingStatus.COMPLETED else None,
                    participation_level=random.uniform(5.0, 10.0) if meeting.status == MeetingStatus.COMPLETED else None,
                    contribution_score=random.uniform(4.0, 9.5) if meeting.status == MeetingStatus.COMPLETED else None
                )
                
                participants.append(participant)
        
        return participants
    
    def create_availability_windows(self, users: List[User]) -> List[AvailabilityWindow]:
        """Create availability windows for users"""
        
        availability_windows = []
        now = datetime.now()
        
        for user in users:
            # Create some unavailable periods (out of office, focus time, etc.)
            for _ in range(random.randint(2, 5)):
                # Random date in the next 30 days
                start_date = now + timedelta(days=random.randint(0, 30))
                
                # Random time during the day
                start_hour = random.randint(8, 16)
                start_minute = random.choice([0, 30])
                
                start_time = start_date.replace(
                    hour=start_hour,
                    minute=start_minute,
                    second=0,
                    microsecond=0
                )
                
                # Duration (30 minutes to 4 hours)
                duration = random.choice([30, 60, 90, 120, 180, 240])
                end_time = start_time + timedelta(minutes=duration)
                
                reasons = [
                    "Out of office", "Focus time", "Travel", "Training",
                    "Client visit", "Conference", "Personal appointment"
                ]
                
                availability = AvailabilityWindow(
                    user_id=user.id,
                    start_time=start_time,
                    end_time=end_time,
                    timezone=user.timezone,
                    is_available=False,
                    priority=random.randint(1, 5),
                    reason=random.choice(reasons)
                )
                
                availability_windows.append(availability)
        
        return availability_windows
    
    def create_meeting_analyses(self, meetings: List[Meeting]) -> List[MeetingAnalysis]:
        """Create meeting analysis records for completed meetings"""
        
        analyses = []
        
        for meeting in meetings:
            if meeting.status == MeetingStatus.COMPLETED:
                analysis = MeetingAnalysis(
                    meeting_id=meeting.id,
                    meeting_frequency_score=random.uniform(5.0, 9.0),
                    duration_appropriateness=random.uniform(6.0, 9.5),
                    timing_effectiveness=random.uniform(5.5, 9.0),
                    organizer_workload_impact=random.uniform(3.0, 8.0),
                    participant_workload_impact=random.uniform(4.0, 8.5),
                    agenda_quality_score=random.uniform(4.0, 9.0),
                    participant_balance_score=random.uniform(5.0, 9.0),
                    follow_up_clarity=random.uniform(4.5, 8.5),
                    suggested_duration=random.choice([30, 45, 60, 90]),
                    improvement_suggestions='["Prepare detailed agenda", "Limit participants", "Set clear objectives"]',
                    analysis_version="1.0"
                )
                
                analyses.append(analysis)
        
        return analyses
    
    def _generate_location(self, meeting_type: MeetingType) -> str:
        """Generate appropriate location based on meeting type"""
        
        if meeting_type == MeetingType.ONE_ON_ONE:
            return random.choice([
                "Conference Room A", "Manager's Office", "Quiet Corner",
                "Coffee Area", "Zoom", "Teams Meeting"
            ])
        elif meeting_type == MeetingType.ALL_HANDS:
            return random.choice([
                "Main Auditorium", "Large Conference Room", "Zoom Webinar",
                "Town Hall", "Teams Live Event"
            ])
        elif meeting_type == MeetingType.CLIENT_MEETING:
            return random.choice([
                "Client Conference Room", "Presentation Room", "Zoom",
                "Client Office", "Teams Meeting", "Google Meet"
            ])
        else:
            return random.choice([
                "Conference Room B", "Meeting Room 1", "Team Room",
                "Zoom", "Teams", "Google Meet", "Slack Huddle"
            ])
    
    def generate_all_data(self):
        """Generate all sample data and save to database"""
        
        print("Creating database and tables...")
        create_db_and_tables()
        
        with Session(engine) as session:
            print("Generating users...")
            users = self.create_users(25)
            session.add_all(users)
            session.commit()
            
            # Refresh to get IDs
            for user in users:
                session.refresh(user)
            
            print("Generating meetings...")
            meetings = self.create_meetings(users, 80)
            session.add_all(meetings)
            session.commit()
            
            # Refresh to get IDs
            for meeting in meetings:
                session.refresh(meeting)
            
            print("Generating participants...")
            participants = self.create_participants(meetings)
            session.add_all(participants)
            session.commit()
            
            print("Generating availability windows...")
            availability_windows = self.create_availability_windows(users)
            session.add_all(availability_windows)
            session.commit()
            
            print("Generating meeting analyses...")
            analyses = self.create_meeting_analyses(meetings)
            session.add_all(analyses)
            session.commit()
            
            print(f"✅ Sample data generated successfully!")
            print(f"   - Users: {len(users)}")
            print(f"   - Meetings: {len(meetings)}")
            print(f"   - Participants: {len(participants)}")
            print(f"   - Availability Windows: {len(availability_windows)}")
            print(f"   - Meeting Analyses: {len(analyses)}")
            
            # Print some statistics
            meeting_types = {}
            for meeting in meetings:
                meeting_types[meeting.meeting_type.value] = meeting_types.get(meeting.meeting_type.value, 0) + 1
            
            print(f"\n📊 Meeting Distribution:")
            for meeting_type, count in meeting_types.items():
                print(f"   - {meeting_type}: {count}")
            
            # Print timezone distribution
            timezones = {}
            for user in users:
                timezones[user.timezone] = timezones.get(user.timezone, 0) + 1
            
            print(f"\n🌍 Timezone Distribution:")
            for timezone, count in timezones.items():
                print(f"   - {timezone}: {count}")


def main():
    """Main entry point"""
    generator = SampleDataGenerator()
    generator.generate_all_data()


if __name__ == "__main__":
    main() 