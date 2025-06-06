# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# mypy: disable-error-code="attr-defined"
import copy
import datetime
import json
import logging # Keep logging import
import os
from collections.abc import Mapping, Sequence
from typing import Any

import google.auth
import vertexai
import google.api_core.exceptions # For specific exception handling
from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from app.utils.gcs import create_bucket_if_not_exists
from app.utils.tracing import CloudTraceLoggingSpanExporter
from app.utils.typing import Feedback
from vertexai.preview.reasoning_engines import AdkApp


GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Set up logging and tracing for the agent engine app."""
        super().set_up()
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        provider = TracerProvider()
        processor = export.BatchSpanProcessor(
            CloudTraceLoggingSpanExporter(
                project_id=GOOGLE_CLOUD_PROJECT
            )
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> Mapping[str, Sequence]:
        """Registers the operations of the Agent.

        Extends the base operations to include feedback registration functionality.
        """
        operations = super().register_operations()
        operations[""] = operations[""] + ["register_feedback"]
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the ADK application."""
        template_attributes = self._tmpl_attrs
        return self.__class__(
            agent=copy.deepcopy(template_attributes.get("agent")),
            enable_tracing=template_attributes.get("enable_tracing"),
            session_service_builder=template_attributes.get("session_service_builder"),
            artifact_service_builder=template_attributes.get(
                "artifact_service_builder"
            ),
            env_vars=template_attributes.get("env_vars"),
        )


def deploy_agent_engine_app(
    project: str,
    location: str,
    agent_name: str | None = None,
    requirements_file: str = "requirements.txt",
    extra_packages: list[str] = ["./app","./orchestrate","a2a_common-0.1.0-py3-none-any.whl"],
    env_vars: dict[str, str] | None = None,
) -> agent_engines.AgentEngine:
    """Deploy the agent engine aEngine backing LRO:pp to Vertex AI."""

    staging_bucket = f"gs://{project}-agent-engine"

    create_bucket_if_not_exists(
        bucket_name=staging_bucket, project=project, location=location
    )
    vertexai.init(project=project, location=location, staging_bucket=staging_bucket)

    # Read requirements
    with open(requirements_file) as f:
        requirements = f.read().strip().split("\n")

    from orchestrate.agent import root_agent
    agent_engine = AgentEngineApp(
        agent=root_agent,
        env_vars=env_vars,
    )

    # Common configuration for both create and update operations
    agent_config = {
        "agent_engine": agent_engine,
        "display_name": agent_name,
        "description": "A base ReAct agent built with Google's Agent Development Kit (ADK)",
        "extra_packages": extra_packages,
    }
    logging.info(f"Agent config: {agent_config}")
    agent_config["requirements"] = requirements
    # Log the complete configuration that will be sent
    logging.info(
        "Complete agent_config being used for deployment (excluding agent_engine object itself for brevity if too large, focusing on parameters):"
    )
    # Create a copy for logging to avoid modifying the original if we decide to remove agent_engine for logging
    log_config = {k: v for k, v in agent_config.items() if k != "agent_engine"}
    log_config["agent_engine_class"] = agent_config["agent_engine"].__class__.__name__
    logging.info(json.dumps(log_config, indent=2, default=str))

    try:
        # Check if an agent with this name already exists
        existing_agents = list(agent_engines.list(filter=f"display_name={agent_name}"))
        if existing_agents:
            # Update the existing agent with new configuration
            logging.info(f"Attempting to updste existing: {agent_name} in project {project}, location {location} ")
            remote_agent = existing_agents[0].update(**agent_config)
            logging.info(f"Agent '{agent_name}' updated successfully.")
        else:
            # Create a new agent if none exists
            logging.info(f"Attempting to create new agent: {agent_name} in project {project}, location {location}")
            remote_agent = agent_engines.create(**agent_config)
            logging.info(f"Agent '{agent_name}' created successfully.")

    except google.api_core.exceptions.InvalidArgument as e:
        logging.error(f"!!! InvalidArgument error during agent deployment for '{agent_name}' in project '{project}', location '{location}': {e}")
        logging.error("--- Agent Configuration Sent (excluding agent_engine object for brevity) ---")
        logging.error(json.dumps(log_config, indent=2, default=str))
        logging.error("--- End of Agent Configuration Sent ---")
        logging.error(
            "ACTION REQUIRED: This 'Build failed' error indicates an issue with the agent's source code, "
            "its requirements.txt file, or other dependencies. "
            "For DETAILED build errors, please navigate to the Google Cloud Console:"
        )
        logging.error(f"1. Go to Cloud Build > History.")
        logging.error(f"2. Ensure you are in project: '{project}'.")
        logging.error(f"3. Filter by region if necessary (often 'global' or '{location}' for regionalized services).")
        logging.error("4. Look for recent FAILED builds. The logs there will contain the specific reason for the build failure (e.g., pip install errors, code compilation issues).")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred during agent deployment for '{agent_name}' in project '{project}', location '{location}': {e}")
        logging.error(f"Agent configuration that might be relevant (excluding agent_engine object): {json.dumps(log_config, indent=2, default=str)}")
        import traceback
        logging.error(traceback.format_exc())
        raise

    config = {
        "remote_agent_engine_id": remote_agent.resource_name,
        "deployment_timestamp": datetime.datetime.now().isoformat(),
    }
    config_file = "deployment_metadata.json"

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    logging.info(f"Agent Engine ID written to {config_file}")

    return remote_agent


if __name__ == "__main__":
    # Setup basic logging for the script execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    )
    import argparse

    parser = argparse.ArgumentParser(description="Deploy agent engine app to Vertex AI")
    parser.add_argument(
        "--project",
        default=GOOGLE_CLOUD_PROJECT,
        help="GCP project ID (defaults to application default credentials)",
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP region (defaults to us-central1)",
    )
    parser.add_argument(
        "--agent-name",
        default="orchestrate-agent",
        help="Name for the agent engine",
    )
    parser.add_argument(
        "--requirements-file",
        default="./requirements.txt",
        help="Path to requirements.txt file",
    )
    parser.add_argument(
        "--extra-packages",
        nargs="+",
        default=["./app","./orchestrate","./a2a_common-0.1.0-py3-none-any.whl"],
        help="Additional packages to include",
    )
    parser.add_argument(
        "--set-env-vars",
        help="Comma-separated list of environment variables in KEY=VALUE format",
    )
    args = parser.parse_args()

    # --- Parse and Set Environment Variables ---
    # Parse environment variables if provided
    env_vars = None
    if args.set_env_vars:
        env_vars = {}
        for pair_raw in args.set_env_vars.split(";"): # Use semicolon as the outer delimiter
            pair = pair_raw.strip() # Remove leading/trailing whitespace
            if not pair: # Skip empty pairs (e.g., from double semicolons)
                continue
            try:
                key, value = pair.split("=", 1)
                env_vars[key.strip()] = value # Store with stripped key
                # os.environ[key.strip()] = value # AgentEngineApp handles env_vars
                logging.info(f"Parsed environment variable for agent: {key.strip()}={value}")
            except ValueError:
                # Warn if a pair doesn't contain '='
                logging.warning(f"Skipping invalid environment variable pair: '{pair}'")
    # --- End Parse and Set Environment Variables ---

    if not args.project:
        _, args.project = google.auth.default()

    logging.info("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🤖 DEPLOYING AGENT TO VERTEX AI AGENT ENGINE 🤖         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    deploy_agent_engine_app(
        project=args.project,
        location=args.location,
        agent_name=args.agent_name,
        requirements_file=args.requirements_file,
        extra_packages=args.extra_packages,
        env_vars=env_vars,
    )
