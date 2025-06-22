import os
import sys

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

from orchestrator.agent import root_agent  # UPDATE THIS LINE

# ------------------------------------
# Step 1: Define CLI flags
# ------------------------------------
FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket.")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")
flags.DEFINE_string("user_id", "test_user", "User ID for session operations.")
flags.DEFINE_string("session_id", None, "Session ID for operations.")
flags.DEFINE_bool("create", False, "Creates a new deployment.")
flags.DEFINE_bool("delete", False, "Deletes an existing deployment.")
flags.DEFINE_bool("list", False, "Lists all deployments.")
flags.DEFINE_bool("create_session", False, "Creates a new session.")
flags.DEFINE_bool("list_sessions", False, "Lists all sessions for a user.")
flags.DEFINE_bool("get_session", False, "Gets a specific session.")
flags.DEFINE_bool("send", False, "Sends a message to the deployed agent.")
flags.DEFINE_string(
    "message",
    "Ask something to your orchestrator agent.",
    "Message to send to the agent.",
)

flags.mark_bool_flags_as_mutual_exclusive(
    [
        "create",
        "delete",
        "list",
        "create_session",
        "list_sessions",
        "get_session",
        "send",
    ]
)

# ------------------------------------
# Step 2: Define operations
# ------------------------------------
def create():
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )
    remote_app = agent_engines.create(
        agent_engine=app,
        requirements=["google-cloud-aiplatform[adk,agent_engines]"],
        extra_packages=["."],  # root of your module with pyproject.toml
    )
    print(f"Created remote app: {remote_app.resource_name}")

def delete(resource_id: str):
    remote_app = agent_engines.get(resource_id)
    remote_app.delete(force=True)
    print(f"Deleted remote app: {resource_id}")

def list_deployments():
    deployments = agent_engines.list()
    print("Deployments:")
    for deployment in deployments:
        print(f"- {deployment.resource_name}")

def create_session(resource_id: str, user_id: str):
    remote_app = agent_engines.get(resource_id)
    remote_session = remote_app.create_session(user_id=user_id)
    print("Created session:")
    print(f"  Session ID: {remote_session['id']}")
    print(f"  User ID: {remote_session['user_id']}")
    print(f"  App name: {remote_session['app_name']}")
    print(f"  Last update time: {remote_session['last_update_time']}")

def list_sessions(resource_id: str, user_id: str):
    remote_app = agent_engines.get(resource_id)
    sessions = remote_app.list_sessions(user_id=user_id)
    print(f"Sessions for user '{user_id}':")
    for session in sessions:
        print(f"- Session ID: {session['id']}")

def get_session(resource_id: str, user_id: str, session_id: str):
    remote_app = agent_engines.get(resource_id)
    session = remote_app.get_session(user_id=user_id, session_id=session_id)
    print("Session details:")
    print(f"  ID: {session['id']}")
    print(f"  User ID: {session['user_id']}")
    print(f"  App name: {session['app_name']}")
    print(f"  Last update time: {session['last_update_time']}")

def send_message(resource_id: str, user_id: str, session_id: str, message: str):
    remote_app = agent_engines.get(resource_id)
    print(f"Sending message to session {session_id}:")
    print(f"Message: {message}")
    print("\nResponse:")
    for event in remote_app.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message,
    ):
        print(event)

# ------------------------------------
# Step 3: Entry Point
# ------------------------------------
def main(argv=None):
    argv = flags.FLAGS(sys.argv) if argv is None else flags.FLAGS(argv)
    load_dotenv()

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location or os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket or os.getenv("GOOGLE_CLOUD_STAGING_BUCKET")
    user_id = FLAGS.user_id

    if not all([project_id, location, bucket]):
        print("Missing required environment variables: GOOGLE_CLOUD_PROJECT / LOCATION / BUCKET")
        return

    vertexai.init(project=project_id, location=location, staging_bucket=bucket)

    if FLAGS.create:
        create()
    elif FLAGS.delete:
        delete(FLAGS.resource_id)
    elif FLAGS.list:
        list_deployments()
    elif FLAGS.create_session:
        create_session(FLAGS.resource_id, user_id)
    elif FLAGS.list_sessions:
        list_sessions(FLAGS.resource_id, user_id)
    elif FLAGS.get_session:
        get_session(FLAGS.resource_id, user_id, FLAGS.session_id)
    elif FLAGS.send:
        send_message(FLAGS.resource_id, user_id, FLAGS.session_id, FLAGS.message)
    else:
        print("Please specify an action to perform.")


if __name__ == "__main__":
    app.run(main)