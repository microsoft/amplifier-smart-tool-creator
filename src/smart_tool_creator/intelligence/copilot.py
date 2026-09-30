"""GitHub Copilot SDK implementation of the intelligence interface."""

import asyncio
import contextlib
from importlib.metadata import version
import shutil
import subprocess
import time
from typing import Any

from copilot import CopilotClient, PermissionHandler, Tool, ToolInvocation, ToolResult

from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult
from smart_tool_creator.intelligence.submission import (
    MAX_INVALID_SUBMISSIONS,
    SUBMIT_TOOL,
    resubmit_prompt,
    submission_problem,
)
from smart_tool_creator.schemas import SmartToolCreatorError


class CopilotIntelligence:
    """Runs agents through a Copilot CLI runtime on this machine, signed in as the GitHub CLI's user."""

    def __init__(self) -> None:
        self.implementation = f"copilot-sdk {version('github-copilot-sdk')}"
        self._token: str | None = None

    def preflight(self) -> None:
        self._github_token()

    def run(self, request: AgentRequest) -> AgentResult:
        working_directory = str(request.workspace.path) if request.workspace is not None else None
        client = CopilotClient(working_directory=working_directory, github_token=self._github_token())
        return asyncio.run(self._run(client, request))

    def _github_token(self) -> str:
        if self._token is not None:
            return self._token
        if shutil.which("gh") is None:
            raise SmartToolCreatorError(
                "Model-backed capabilities need the GitHub CLI. Install gh from https://cli.github.com/ and sign in with "
                "`gh auth login`."
            )
        minted = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if minted.returncode != 0:
            raise SmartToolCreatorError(
                f"The GitHub CLI is not signed in: {minted.stderr.strip()} "
                "Run `gh auth login` with an account that has Copilot access."
            )
        self._token = minted.stdout.strip()
        return self._token

    async def _run(self, client: CopilotClient, request: AgentRequest) -> AgentResult:
        submitted: dict[str, Any] | None = None

        def capture(invocation: ToolInvocation) -> ToolResult:
            nonlocal submitted
            submitted = invocation.arguments
            return ToolResult(text_result_for_llm="Submission received.")

        session_options: dict[str, Any] = {
            "model": request.model,
            "reasoning_effort": request.reasoning_effort,
            "on_permission_request": PermissionHandler.approve_all,
            "skip_custom_instructions": True,
            "available_tools": [],
        }
        if request.workspace is not None:
            session_options["working_directory"] = str(request.workspace.path)
            session_options["available_tools"] = ["view", "grep", "bash"]
            if request.writable:
                # bash is not sandboxed to the workspace; the caller's prompt bounds the agent
                # and the caller validates before anything the agent wrote is kept.
                session_options["available_tools"] = [*session_options["available_tools"], "edit", "write"]
        if request.output_schema is not None:
            session_options["tools"] = [
                Tool(
                    name=SUBMIT_TOOL,
                    description="Submit your final answer. Call it exactly once, when you are done.",
                    parameters=request.output_schema,
                    handler=capture,
                    skip_permission=True,
                    is_terminal=True,
                )
            ]
            session_options["available_tools"] = [*session_options["available_tools"], SUBMIT_TOOL]
        deadline = time.monotonic() + request.timeout_seconds
        # Carried out of the try so the failure paths can name the session the caller could resume.
        session_id: str | None = None
        try:
            await client.start()
            if request.resume is not None:
                session = await client.resume_session(request.resume, **session_options)
            else:
                session = await client.create_session(**session_options)
            session_id = session.session_id
            prompt = request.prompt
            invalid = 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                try:
                    event = await session.send_and_wait(prompt, timeout=remaining)
                except TimeoutError:
                    await session.abort()
                    return AgentResult(
                        error=f"The agent did not finish within {request.timeout_seconds} seconds.",
                        session_id=session_id,
                    )
                text = str(getattr(event.data, "content", "") or "") if event is not None else ""
                if request.output_schema is None:
                    return AgentResult(text=text, session_id=session_id)
                problem = submission_problem(submitted, request.output_schema)
                if problem is None:
                    return AgentResult(output=submitted, text=text, session_id=session_id)
                if invalid >= MAX_INVALID_SUBMISSIONS:
                    return AgentResult(
                        text=text,
                        error=f"No valid submission after {invalid} retries: {problem}",
                        session_id=session_id,
                    )
                invalid += 1
                submitted = None
                prompt = resubmit_prompt(problem)
        except TimeoutError:
            return AgentResult(
                error=f"The agent did not finish within {request.timeout_seconds} seconds.", session_id=session_id
            )
        except Exception as error:  # an SDK or runtime failure is the caller's data, not a crash
            return AgentResult(error=f"{type(error).__name__}: {error}", session_id=session_id)
        finally:
            with contextlib.suppress(Exception):
                await client.stop()
