# InstaVibe: Multi-Agent AI System on Google Cloud

A cloud-native multi-agent system that supercharges group event planning. Built with Google's Agent Development Kit (ADK), powered by Vertex AI, and deployed using Cloud Run, this project demonstrates how intelligent agents can collaborate to enhance social applications.

## Overview

InstaVibe is a prototype social event planning app that uses multiple AI agents to:
- Recommend events based on user preferences
- Analyze social connections for compatibility
- Automate backend event coordination

This project follows the official Google Codelab with practical extensions.

## Architecture

### Agents
- Event Planner Agent – suggests local events
- Social Profiling Agent – finds mutual interests and connections
- Platform Interaction Agent – handles backend interactions
- Orchestrator Agent – coordinates everything

### Google Cloud Stack

| Component                    | GCP Service Used                 |
|-----------------------------|----------------------------------|
| Agent Hosting               | Cloud Run                        |
| AI Agent Management         | Vertex AI Agent Builder / Engine |
| Orchestration               | ADK + Vertex AI                  |
| Data Layer                  | Cloud Spanner                    |
| App Hosting                 | Cloud Run                        |
| Build Automation            | Cloud Build                      |
| Container Registry          | Artifact Registry                |
| Dev Environment             | Cloud Shell                      |
| Maps Integration            | Google Maps API                  |

## Getting Started

### 1. Clone the Bootstrap Project
```
git clone https://github.com/google/instavibe-bootstrap
cd instavibe-bootstrap
```

### 2. Setup Project in GCP
- Enable Cloud Run, Spanner, Maps API, etc.
- Use Cloud Shell for CLI setup
- Follow ADK CLI to deploy agents

### 3. Deploy Agents & App
- Containerize and push each agent to Artifact Registry
- Deploy using `gcloud run deploy` or Cloud Build triggers
- Use `gcloud builds submit` for automation

### 4. Run Demo
- Launch frontend on Cloud Run
- Trigger planner and social agents
- Watch AI agents collaborate

## Tech Stack

- Python (agents)
- JavaScript (frontend)
- Google Cloud Platform
- Vertex AI + ADK
- Cloud Spanner
- Google Maps API

## Features

- Real-time multi-agent collaboration
- Event suggestions tailored to friend groups
- Orchestrator for dynamic task routing
- GCP-native CI/CD + deployment flow

## Learnings

- How agents collaborate using A2A (Agent-to-Agent) protocol
- Using Vertex AI Agent Builder for intelligent workflows
- Orchestrating multiple services on Cloud Run
- Integrating external APIs (Maps) into agent pipelines

## License

This project is based on Google’s Codelab and is open for educational use.

## Acknowledgments

Thanks to Google Cloud Codelabs for the brilliant ADK tutorial.
