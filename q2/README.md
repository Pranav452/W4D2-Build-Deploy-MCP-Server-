# Smart Meeting Assistant with AI Scheduling

An intelligent meeting management system that leverages AI to optimize scheduling, detect conflicts, and provide actionable insights for better meeting productivity.

## 🚀 Features

### Core AI Capabilities
- **Intelligent Scheduling**: AI-powered conflict detection and optimal time slot recommendations
- **Multi-timezone Support**: Seamless scheduling across global teams
- **Pattern Analysis**: Deep insights into meeting behaviors and productivity trends
- **Workload Balancing**: Automatic distribution analysis and recommendations
- **Effectiveness Scoring**: AI-driven meeting quality assessment
- **Smart Agenda Generation**: Context-aware agenda suggestions

### MCP Tools (Model Context Protocol)
- `create_meeting` - Schedule meetings with intelligent conflict detection
- `find_optimal_slots` - AI-powered time recommendations
- `detect_scheduling_conflicts` - Comprehensive conflict identification
- `analyze_meeting_patterns` - Meeting behavior analysis
- `generate_agenda_suggestions` - Smart agenda creation
- `calculate_workload_balance` - Team meeting load distribution
- `score_meeting_effectiveness` - Productivity assessment
- `optimize_meeting_schedule` - Schedule optimization recommendations

## 🏗️ Architecture

```
├── models.py              # SQLModel database models
├── ai_scheduler.py        # AI scheduling core algorithms
├── mcp_server.py          # MCP server implementation
├── meeting_assistant_api.py # FastAPI REST endpoints
├── populate_sample_data.py # Sample data generator
├── requirements.txt       # Python dependencies
└── README.md             # This documentation
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- pip package manager

### Step 1: Install Dependencies
```bash
cd q2
pip install -r requirements.txt
```

### Step 2: Generate Sample Data
```bash
python populate_sample_data.py
```

This creates:
- 25 users across 12 different timezones
- 80+ meetings with realistic patterns
- Comprehensive participant and availability data
- Meeting effectiveness scores and analyses

### Step 3: Start the MCP Server
```bash
python mcp_server.py
```

### Step 4: Start the FastAPI Server
```bash
python meeting_assistant_api.py
```

The API will be available at `http://localhost:8000`

## 📊 Sample Data Overview

The system generates realistic sample data including:

### Users (25 total)
- **Roles**: Admin (10%), Manager (20%), Employee (65%), Guest (5%)
- **Timezones**: 12 global timezones including EST, PST, GMT, JST, etc.
- **Work Patterns**: Varied working hours and meeting preferences

### Meetings (80+ total)
- **Types**: Team meetings (35%), One-on-ones (25%), Client meetings (15%)
- **Distribution**: Past 3 months + next 1 month
- **Realistic Patterns**: Business hours, appropriate durations, timezone-aware

### Analytics Data
- Meeting effectiveness scores (4.0-9.5 scale)
- Productivity ratings and engagement levels
- Availability windows and conflict patterns
- Workload distribution metrics

## 🔧 API Usage Examples

### Create a Meeting
```bash
curl -X POST "http://localhost:8000/meetings" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Project Kickoff",
    "participants": [1, 2, 3, 4],
    "duration": 60,
    "start_time": "2024-01-15T10:00:00",
    "timezone": "America/New_York",
    "meeting_type": "team_meeting",
    "organizer_id": 1
  }'
```

### Find Optimal Time Slots
```bash
curl -X POST "http://localhost:8000/schedule/find-optimal-slots" \
  -H "Content-Type: application/json" \
  -d '{
    "participants": [1, 2, 3],
    "duration": 45,
    "start_date": "2024-01-15",
    "end_date": "2024-01-19",
    "timezone": "UTC",
    "max_results": 5
  }'
```

### Detect Conflicts
```bash
curl -X POST "http://localhost:8000/schedule/detect-conflicts" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "start_time": "2024-01-15T10:00:00",
    "end_time": "2024-01-15T11:00:00"
  }'
```

### Analyze Meeting Patterns
```bash
curl -X POST "http://localhost:8000/analytics/meeting-patterns" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "period": 30
  }'
```

### Generate Agenda Suggestions
```bash
curl -X POST "http://localhost:8000/ai/generate-agenda" \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_topic": "Sprint Planning",
    "participants": [1, 2, 3, 4, 5],
    "duration": 90
  }'
```

## 🤖 MCP Tools Usage

### Using with MCP Client
```python
from mcp import Client

# Connect to MCP server
client = Client("meeting-assistant")

# Create a meeting
result = await client.call_tool("create_meeting", {
    "title": "Weekly Standup",
    "participants": [1, 2, 3],
    "duration": 30,
    "start_time": "2024-01-15T09:00:00",
    "organizer_id": 1
})

# Find optimal slots
slots = await client.call_tool("find_optimal_slots", {
    "participants": [1, 2, 3, 4],
    "duration": 60,
    "date_range": {
        "start_date": "2024-01-15",
        "end_date": "2024-01-19"
    }
})
```

## 🧠 AI Scheduling Algorithms

### Conflict Detection
- **Meeting Overlaps**: Identifies direct scheduling conflicts
- **Availability Windows**: Respects out-of-office and focus time blocks
- **Workload Analysis**: Detects excessive meeting loads
- **Severity Scoring**: Prioritizes conflicts by impact level

### Optimal Time Finding
- **Multi-factor Scoring**: Considers availability, preferences, and productivity
- **Timezone Optimization**: Finds times that work across global teams
- **Pattern Recognition**: Learns from successful meeting times
- **Participant Weighting**: Balances individual vs. group preferences

### Effectiveness Scoring
- **Duration Appropriateness**: Matches meeting length to type and participants
- **Timing Effectiveness**: Evaluates optimal scheduling windows
- **Engagement Metrics**: Analyzes participation and contribution levels
- **Agenda Quality**: Assesses meeting preparation and structure

## 📈 Analytics & Insights

### Meeting Pattern Analysis
```json
{
  "total_meetings": 45,
  "average_meetings_per_day": 2.1,
  "meeting_types": {
    "team_meeting": 18,
    "one_on_one": 12,
    "client_meeting": 8
  },
  "time_preferences": {
    "preferred_start_hour": 10,
    "morning_meetings": 28,
    "afternoon_meetings": 17
  },
  "productivity_trends": {
    "average_effectiveness": 7.2,
    "effectiveness_trend": "improving"
  }
}
```

### Workload Balance Assessment
```json
{
  "team_workload": {
    "1": {
      "user_name": "Alice Johnson",
      "total_meetings": 12,
      "total_meeting_minutes": 720,
      "workload_score": 8.5
    }
  },
  "balance_metrics": {
    "average_workload": 7.2,
    "balance_score": 8.1,
    "most_loaded_user": 3,
    "least_loaded_user": 7
  }
}
```

## 🔍 Advanced Features

### Timezone Intelligence
- Automatic timezone detection and conversion
- Optimal meeting time suggestions across timezones
- Respect for local working hours and preferences
- Holiday and cultural consideration (future enhancement)

### Smart Agenda Generation
- Context-aware agenda item suggestions
- Duration-based time allocation
- Participant-specific considerations
- Meeting type optimization

### Predictive Analytics
- Meeting success prediction
- Optimal participant combinations
- Seasonal pattern recognition
- Productivity trend analysis

## 🚀 Performance Optimization

### Database Optimization
- Efficient SQLModel relationships
- Indexed queries for fast lookups
- Session management for concurrent access
- Optimized data structures for analytics

### AI Algorithm Efficiency
- Vectorized operations with NumPy
- Caching of frequently accessed data
- Parallel processing for large datasets
- Incremental pattern learning

## 🛡️ Security & Privacy

### Data Protection
- No sensitive personal information stored
- Timezone and preference data only
- Secure session management
- API rate limiting (production ready)

### Privacy Considerations
- User consent for analytics
- Data retention policies
- Anonymization of sensitive patterns
- GDPR compliance ready

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./meeting_assistant.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# MCP Settings
MCP_SERVER_NAME=meeting-assistant
MCP_SERVER_VERSION=1.0.0
```

### User Preferences
```python
# Configure user working hours
user.work_start_hour = 9
user.work_end_hour = 17
user.work_days = "1,2,3,4,5"  # Monday-Friday

# Meeting preferences
user.max_meetings_per_day = 8
user.preferred_meeting_duration = 30
user.buffer_time = 15
```

## 🧪 Testing

### Run Sample Operations
```bash
# Test conflict detection
python -c "
from ai_scheduler import AIScheduler
from datetime import datetime
scheduler = AIScheduler()
conflicts = scheduler.detect_scheduling_conflicts(1, datetime.now(), datetime.now() + timedelta(hours=1))
print(f'Conflicts found: {len(conflicts)}')
"

# Test optimal slot finding
python -c "
from ai_scheduler import AIScheduler
from datetime import datetime, timedelta
scheduler = AIScheduler()
slots = scheduler.find_optimal_time_slots([1,2,3], 60, datetime.now(), datetime.now() + timedelta(days=7))
print(f'Optimal slots: {len(slots)}')
"
```

### API Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:8000/stats
```

## 📚 API Documentation

When the FastAPI server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🛠️ Development

### Project Structure
```
q2/
├── models.py              # Database models and schemas
├── ai_scheduler.py        # Core AI scheduling algorithms
├── mcp_server.py          # MCP server implementation
├── meeting_assistant_api.py # FastAPI REST endpoints
├── populate_sample_data.py # Sample data generator
├── requirements.txt       # Python dependencies
└── README.md             # Documentation
```

### Key Components

#### AIScheduler Class
- **Core Algorithm**: Intelligent scheduling with multi-factor optimization
- **Conflict Detection**: Comprehensive conflict analysis
- **Pattern Analysis**: Meeting behavior insights
- **Optimization**: Schedule improvement recommendations

#### Database Models
- **User**: Profile, preferences, and timezone information
- **Meeting**: Complete meeting details with AI insights
- **Participant**: Attendance and engagement tracking
- **AvailabilityWindow**: Time-based availability management

#### MCP Integration
- **Tool Registration**: All 8 required MCP tools
- **Schema Validation**: Comprehensive input validation
- **Error Handling**: Graceful error management
- **Session Management**: Efficient database operations

## 🔮 Future Enhancements

### Planned Features
- **Machine Learning**: Enhanced pattern recognition
- **Calendar Integration**: Google Calendar, Outlook sync
- **Video Conferencing**: Auto-generated meeting links
- **Mobile App**: iOS and Android applications
- **Slack/Teams Integration**: Bot-based scheduling

### Technical Improvements
- **Microservices Architecture**: Scalable service separation
- **Real-time Updates**: WebSocket-based notifications
- **Advanced Analytics**: Predictive meeting outcomes
- **Multi-language Support**: Internationalization

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLModel for intuitive database modeling
- MCP for the model context protocol
- PyTZ for timezone handling
- NumPy for efficient numerical operations

---