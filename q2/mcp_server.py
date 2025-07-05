import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from sqlmodel import Session, select
from datetime import datetime, timedelta
import pytz

from models import (
    User, Meeting, Participant, AvailabilityWindow, MeetingAnalysis, 
    MeetingPattern, MeetingType, MeetingStatus, UserRole, 
    engine, create_db_and_tables
)
from ai_scheduler import AIScheduler


class MeetingAssistantServer:
    """MCP Server for Smart Meeting Assistant with AI Scheduling"""
    
    def __init__(self):
        self.server = Server("meeting-assistant")
        self.ai_scheduler = AIScheduler()
        self.setup_tools()
        
    def setup_tools(self):
        """Setup all MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name="create_meeting",
                    description="Schedule a new meeting with intelligent conflict detection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the meeting"
                            },
                            "participants": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of participant user IDs"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Duration in minutes"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                            },
                            "timezone": {
                                "type": "string",
                                "description": "Timezone (e.g., 'America/New_York')",
                                "default": "UTC"
                            },
                            "meeting_type": {
                                "type": "string",
                                "description": "Type of meeting",
                                "enum": ["one_on_one", "team_meeting", "all_hands", "client_meeting", "interview", "training"],
                                "default": "team_meeting"
                            },
                            "description": {
                                "type": "string",
                                "description": "Meeting description",
                                "default": None
                            },
                            "location": {
                                "type": "string",
                                "description": "Meeting location or URL",
                                "default": None
                            },
                            "organizer_id": {
                                "type": "integer",
                                "description": "ID of the meeting organizer"
                            }
                        },
                        "required": ["title", "participants", "duration", "start_time", "organizer_id"]
                    }
                ),
                Tool(
                    name="find_optimal_slots",
                    description="Find optimal time slots for a meeting based on participant availability",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "participants": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of participant user IDs"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Duration in minutes"
                            },
                            "date_range": {
                                "type": "object",
                                "properties": {
                                    "start_date": {
                                        "type": "string",
                                        "description": "Start date in ISO format (YYYY-MM-DD)"
                                    },
                                    "end_date": {
                                        "type": "string",
                                        "description": "End date in ISO format (YYYY-MM-DD)"
                                    }
                                },
                                "required": ["start_date", "end_date"]
                            },
                            "timezone": {
                                "type": "string",
                                "description": "Timezone for the search",
                                "default": "UTC"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 10
                            }
                        },
                        "required": ["participants", "duration", "date_range"]
                    }
                ),
                Tool(
                    name="detect_scheduling_conflicts",
                    description="Detect scheduling conflicts for a user in a given time range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID to check conflicts for"
                            },
                            "time_range": {
                                "type": "object",
                                "properties": {
                                    "start_time": {
                                        "type": "string",
                                        "description": "Start time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                                    },
                                    "end_time": {
                                        "type": "string",
                                        "description": "End time in ISO format (YYYY-MM-DDTHH:MM:SS)"
                                    }
                                },
                                "required": ["start_time", "end_time"]
                            }
                        },
                        "required": ["user_id", "time_range"]
                    }
                ),
                Tool(
                    name="analyze_meeting_patterns",
                    description="Analyze meeting patterns and behavior for a user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID to analyze patterns for"
                            },
                            "period": {
                                "type": "integer",
                                "description": "Analysis period in days",
                                "default": 30
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="generate_agenda_suggestions",
                    description="Generate intelligent agenda suggestions for a meeting",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "meeting_topic": {
                                "type": "string",
                                "description": "Main topic or purpose of the meeting"
                            },
                            "participants": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of participant user IDs"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Meeting duration in minutes"
                            }
                        },
                        "required": ["meeting_topic", "participants", "duration"]
                    }
                ),
                Tool(
                    name="calculate_workload_balance",
                    description="Calculate meeting workload balance across team members",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team_members": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "List of team member user IDs"
                            }
                        },
                        "required": ["team_members"]
                    }
                ),
                Tool(
                    name="score_meeting_effectiveness",
                    description="Score meeting effectiveness and provide improvement suggestions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "meeting_id": {
                                "type": "integer",
                                "description": "ID of the meeting to score"
                            }
                        },
                        "required": ["meeting_id"]
                    }
                ),
                Tool(
                    name="optimize_meeting_schedule",
                    description="Provide schedule optimization recommendations for a user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID to optimize schedule for"
                            }
                        },
                        "required": ["user_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            try:
                if name == "create_meeting":
                    return await self._create_meeting(arguments)
                elif name == "find_optimal_slots":
                    return await self._find_optimal_slots(arguments)
                elif name == "detect_scheduling_conflicts":
                    return await self._detect_scheduling_conflicts(arguments)
                elif name == "analyze_meeting_patterns":
                    return await self._analyze_meeting_patterns(arguments)
                elif name == "generate_agenda_suggestions":
                    return await self._generate_agenda_suggestions(arguments)
                elif name == "calculate_workload_balance":
                    return await self._calculate_workload_balance(arguments)
                elif name == "score_meeting_effectiveness":
                    return await self._score_meeting_effectiveness(arguments)
                elif name == "optimize_meeting_schedule":
                    return await self._optimize_meeting_schedule(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
            finally:
                # Clean up scheduler session
                self.ai_scheduler.close_session()
    
    async def _create_meeting(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new meeting with conflict detection"""
        
        # Parse arguments
        title = arguments["title"]
        participant_ids = arguments["participants"]
        duration = arguments["duration"]
        start_time_str = arguments["start_time"]
        timezone = arguments.get("timezone", "UTC")
        meeting_type = arguments.get("meeting_type", "team_meeting")
        description = arguments.get("description")
        location = arguments.get("location")
        organizer_id = arguments["organizer_id"]
        
        # Parse start time
        try:
            start_time = datetime.fromisoformat(start_time_str)
            if start_time.tzinfo is None:
                start_time = pytz.timezone(timezone).localize(start_time)
        except ValueError:
            return [TextContent(
                type="text",
                text="Invalid start_time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )]
        
        end_time = start_time + timedelta(minutes=duration)
        
        with Session(engine) as session:
            # Verify organizer exists
            organizer = session.get(User, organizer_id)
            if not organizer:
                return [TextContent(
                    type="text",
                    text=f"Organizer with ID {organizer_id} not found"
                )]
            
            # Verify all participants exist
            participants = session.exec(
                select(User).where(User.id.in_(participant_ids))
            ).all()
            
            if len(participants) != len(participant_ids):
                found_ids = [p.id for p in participants]
                missing_ids = [id for id in participant_ids if id not in found_ids]
                return [TextContent(
                    type="text",
                    text=f"Participants not found: {missing_ids}"
                )]
            
            # Check for conflicts for all participants
            conflicts = []
            for participant_id in participant_ids:
                participant_conflicts = self.ai_scheduler.detect_scheduling_conflicts(
                    participant_id, start_time, end_time
                )
                conflicts.extend(participant_conflicts)
            
            # Create meeting
            meeting = Meeting(
                title=title,
                description=description,
                meeting_type=MeetingType(meeting_type),
                start_time=start_time,
                end_time=end_time,
                timezone=timezone,
                location=location,
                organizer_id=organizer_id,
                status=MeetingStatus.SCHEDULED
            )
            
            session.add(meeting)
            session.commit()
            session.refresh(meeting)
            
            # Add participants
            for participant_id in participant_ids:
                participant = Participant(
                    user_id=participant_id,
                    meeting_id=meeting.id,
                    is_required=True,
                    response_status="pending"
                )
                session.add(participant)
            
            session.commit()
            
            # Prepare response
            result = {
                "meeting_id": meeting.id,
                "title": meeting.title,
                "start_time": meeting.start_time.isoformat(),
                "end_time": meeting.end_time.isoformat(),
                "duration_minutes": duration,
                "organizer": organizer.name,
                "participants": [p.name for p in participants],
                "conflicts_detected": len(conflicts) > 0,
                "conflicts": [
                    {
                        "user_name": c.user_name,
                        "type": c.conflict_type,
                        "severity": c.severity,
                        "details": c.conflict_details
                    }
                    for c in conflicts
                ] if conflicts else [],
                "status": "created_with_conflicts" if conflicts else "created_successfully"
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
    
    async def _find_optimal_slots(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Find optimal time slots for a meeting"""
        
        participant_ids = arguments["participants"]
        duration = arguments["duration"]
        date_range = arguments["date_range"]
        timezone = arguments.get("timezone", "UTC")
        max_results = arguments.get("max_results", 10)
        
        # Parse date range
        try:
            start_date = datetime.fromisoformat(date_range["start_date"])
            end_date = datetime.fromisoformat(date_range["end_date"])
            
            # Localize to timezone
            tz = pytz.timezone(timezone)
            start_date = tz.localize(start_date)
            end_date = tz.localize(end_date)
            
        except ValueError:
            return [TextContent(
                type="text",
                text="Invalid date format. Use ISO format (YYYY-MM-DD)"
            )]
        
        # Find optimal slots
        optimal_slots = self.ai_scheduler.find_optimal_time_slots(
            participant_ids, duration, start_date, end_date, timezone, max_results
        )
        
        if not optimal_slots:
            return [TextContent(
                type="text",
                text="No suitable time slots found for the given criteria"
            )]
        
        # Format results
        result = {
            "search_criteria": {
                "participants": len(participant_ids),
                "duration_minutes": duration,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "timezone": timezone
            },
            "recommended_slots": [
                {
                    "rank": i + 1,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "score": round(slot.score, 2),
                    "participants_available": len(slot.participants_available),
                    "total_participants": len(participant_ids),
                    "availability_percentage": round(
                        (len(slot.participants_available) / len(participant_ids)) * 100, 1
                    ),
                    "conflicts": slot.conflicts[:3] if slot.conflicts else []  # Limit conflicts shown
                }
                for i, slot in enumerate(optimal_slots)
            ]
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _detect_scheduling_conflicts(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Detect scheduling conflicts for a user"""
        
        user_id = arguments["user_id"]
        time_range = arguments["time_range"]
        
        # Parse time range
        try:
            start_time = datetime.fromisoformat(time_range["start_time"])
            end_time = datetime.fromisoformat(time_range["end_time"])
        except ValueError:
            return [TextContent(
                type="text",
                text="Invalid time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )]
        
        # Detect conflicts
        conflicts = self.ai_scheduler.detect_scheduling_conflicts(
            user_id, start_time, end_time
        )
        
        result = {
            "user_id": user_id,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "conflicts_found": len(conflicts),
            "conflicts": [
                {
                    "type": c.conflict_type,
                    "severity": c.severity,
                    "time": c.conflict_time.isoformat(),
                    "details": c.conflict_details
                }
                for c in conflicts
            ]
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _analyze_meeting_patterns(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Analyze meeting patterns for a user"""
        
        user_id = arguments["user_id"]
        period = arguments.get("period", 30)
        
        # Analyze patterns
        patterns = self.ai_scheduler.analyze_meeting_patterns(user_id, period)
        
        return [TextContent(
            type="text",
            text=json.dumps(patterns, indent=2)
        )]
    
    async def _generate_agenda_suggestions(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate agenda suggestions for a meeting"""
        
        meeting_topic = arguments["meeting_topic"]
        participant_ids = arguments["participants"]
        duration = arguments["duration"]
        
        # Generate suggestions
        agenda_items = self.ai_scheduler.generate_agenda_suggestions(
            meeting_topic, participant_ids, duration
        )
        
        result = {
            "meeting_topic": meeting_topic,
            "duration_minutes": duration,
            "participant_count": len(participant_ids),
            "suggested_agenda": agenda_items,
            "agenda_structure": {
                "total_items": len(agenda_items),
                "estimated_time_per_item": duration // len(agenda_items) if agenda_items else 0
            }
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    async def _calculate_workload_balance(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Calculate workload balance across team members"""
        
        team_member_ids = arguments["team_members"]
        
        # Calculate balance
        balance_data = self.ai_scheduler.calculate_workload_balance(team_member_ids)
        
        return [TextContent(
            type="text",
            text=json.dumps(balance_data, indent=2)
        )]
    
    async def _score_meeting_effectiveness(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Score meeting effectiveness"""
        
        meeting_id = arguments["meeting_id"]
        
        # Score effectiveness
        effectiveness_data = self.ai_scheduler.score_meeting_effectiveness(meeting_id)
        
        return [TextContent(
            type="text",
            text=json.dumps(effectiveness_data, indent=2)
        )]
    
    async def _optimize_meeting_schedule(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Optimize meeting schedule for a user"""
        
        user_id = arguments["user_id"]
        
        # Get optimization recommendations
        optimization_data = self.ai_scheduler.optimize_meeting_schedule(user_id)
        
        return [TextContent(
            type="text",
            text=json.dumps(optimization_data, indent=2)
        )]
    
    async def run(self):
        """Run the MCP server"""
        try:
            # Initialize database
            create_db_and_tables()
            
            # Run server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="meeting-assistant",
                        server_version="1.0.0",
                        capabilities={}
                    )
                )
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.ai_scheduler.close_session()


async def main():
    """Main entry point"""
    server = MeetingAssistantServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 