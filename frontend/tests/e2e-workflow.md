# End-to-End Workflow Testing

## Prerequisites

1. Backend running: `docker-compose up -d` or `uvicorn backend.main:app --reload`
2. Frontend running: `npm run dev`
3. Check health: `curl http://localhost:8000/health`

## Environment Setup

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

## Test Workflow

### 1. Sign Up

- Go to: http://localhost:3000/auth/signup
- Enter: name, email, password
- Expected: ✅ Redirected to dashboard

### 2. View Dashboard

- Check: Profile loaded from API (or mock data fallback)
- Check: Progress data displayed
- Expected: ✅ Real data displayed

### 3. Start Tutor Session

- Click: "Start Today's Learning"
- Expected: ✅ Real guidance from Tutor Agent

### 4. Submit Answer

- Type: Your answer
- Click: "Submit Answer"
- Expected: ✅ Real evaluation from Evaluator Agent

### 5. View Feedback

- Check: Score from evaluation
- Check: Misconception detection
- Check: Personalized feedback
- Expected: ✅ All from real API (with mock fallback)

### 6. Check Progress

- Go to: http://localhost:3000/progress
- Expected: ✅ Real progress data

### 7. Verify System Learning

- Check: KAG Agent analyzed patterns
- Expected: ✅ Course improvements recommended

## API Endpoints Tested

| Endpoint                      | Method | Purpose            |
| ----------------------------- | ------ | ------------------ |
| `/health`                     | GET    | Health check       |
| `/api/v1/agents/profiler`     | POST   | Create profile     |
| `/api/v1/learners/{id}`       | GET    | Get profile        |
| `/api/v1/paths/learner/{id}`  | GET    | Get learning path  |
| `/api/v1/tutoring/ask`        | POST   | Get tutor guidance |
| `/api/v1/evaluation/evaluate` | POST   | Evaluate answer    |
| `/api/v1/progress/{id}`       | GET    | Get progress       |
| `/api/v1/analysis/analyze`    | POST   | KAG analysis       |

## Troubleshooting

### CORS Errors

Backend should have CORS configured. Check `backend/main.py` for:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Not Responding

1. Check backend logs: `docker logs backend`
2. Check if port 8000 is in use
3. Verify database connections

### Mock Data Fallback

Frontend hooks include mock data fallback if API fails.
This ensures the UI works even without backend.

## Success Criteria

- [ ] Sign up creates profile in backend
- [ ] Dashboard loads learner data
- [ ] Tutor provides Socratic guidance
- [ ] Evaluator scores responses correctly
- [ ] Progress updates after learning
- [ ] All 6 agents are accessible
