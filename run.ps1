# Start backend (FastAPI)
Start-Process powershell -ArgumentList "-NoExit -Command cd backend; .\.venv\Scripts\Activate.ps1; uvicorn server:app --reload"

# Start frontend local server
Start-Process powershell -ArgumentList "-NoExit -Command python -m http.server 5500"

# Wait a few seconds
Start-Sleep -Seconds 3

# Open frontend
Start-Process "http://localhost:5500/index.html"

# Open API docs
Start-Process "http://127.0.0.1:8000/docs"