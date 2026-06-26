import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from langchain_google_genai import ChatGoogleGenerativeAI
from composio_crewai import ComposioToolSet, Action, App
from crewai import Agent, Task, Crew

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

composio_toolset = ComposioToolSet(
    api_key=os.getenv("COMPOSIO_API_KEY"),
)
tools = composio_toolset.get_tools(apps=[App.GOOGLECALENDAR, App.SLACK, App.GITHUB])

agent = Agent(
    role="Website Support Assistant",
    goal="Answer user queries and execute actions using integrated tools",
    backstory="You are an AI assistant integrated with Google Calendar, Slack, and GitHub to help users manage tasks.",
    llm=llm,
    tools=tools,
    allow_delegation=False,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", StaticFiles(directory="static", html=True), name="static")


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
def chat(request: ChatRequest):
    task = Task(
        description=request.message,
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
    )
    result = crew.kickoff()
    return {"reply": str(result)}


@app.get("/health")
def health():
    return {"status": "running"}
