---
name: agentops-best-practices
description: >
  Enterprise AgentOps guidelines and best practices for building production-grade
  AI agents and multi-agent systems. Covers Tool & Interface Design, Context & Memory
  Management, Orchestration & Logic, Observability & Tracing, and Infrastructure & CI/CD
  based on the 19-criteria AgentOps Code Review Matrix.
---

# AgentOps Production Best Practices & Code Review Guide

A universal guide and engineering framework for designing, implementing, evaluating, and operating production-ready autonomous AI agents and multi-agent systems.

---

## 📋 The 19-Criteria AgentOps Quality Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       AGENT ARCHITECTURE PILLARS                            │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│ 1. Tool & Interface  │ 2. Context & Memory  │ 3. Orchestration & Logic      │
│  • Docstrings        │  • Constitutions     │  • Coordinator / Multi-Agent  │
│  • Descriptive Names │  • Compaction        │  • Strategic Model Routing    │
│  • Pydantic Schemas  │  • Persistent State  │  • Guardrails & Self-Eval     │
│  • Guided Errors     │  • Async Memory Ops  │  • Human-in-the-Loop Gates    │
├──────────────────────┴──────────────────────┼───────────────────────────────┤
│ 4. Observability & Tracing                  │ 5. Infrastructure & CI/CD     │
│  • Structured JSON Logging                  │  • Automated Golden Eval      │
│  • Intent vs. Outcome Tracking              │  • Infrastructure as Code     │
│  • Distributed Tracing (OTel)               │  • Secure Secret Management   │
│  • Automated PII Redaction                  │                               │
└─────────────────────────────────────────────┴───────────────────────────────┘
```

---

## 1. Tool & Interface Design

### 1.1 Comprehensive Tool Docstrings
Every tool exposed to an LLM must have an unambiguous, human-readable Google- or Sphinx-style docstring:
- **Purpose**: A clear 1-2 sentence description of what the tool accomplishes.
- **Args**: Type, purpose, acceptable values, and default behavior for every argument.
- **Returns**: Structure and semantics of the returned payload.
- **Failure Modes**: How edge cases and invalid parameters are handled.

```python
def fetch_adaptive_drill_item(
    user_id: str,
    preferred_item_type: str = "question",
    target_domain_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve the next highest-priority adaptive flashcard or scenario question.

    Uses spaced repetition and domain mastery rankings to select items from
    the candidate's weakest technical areas.

    Args:
        user_id (str): Unique candidate identifier.
        preferred_item_type (str): Type filter ('question', 'flashcard', or 'any').
        target_domain_id (Optional[str]): Optional domain filter (e.g. 'domain_3').

    Returns:
        Dict[str, Any]: Item payload containing question/prompt, Leitner box,
        current domain mastery score, and option choices.
    """
```

### 1.2 Descriptive & Specific Naming
- Use explicit `verb_noun` semantic names (e.g., `authenticate_or_register_candidate`, `evaluate_scenario_answer_and_update_mastery`).
- Avoid vague names like `update`, `do_task`, `process`, or `run_query`.

### 1.3 Strict JSON Schemas & Typing
- Wrap all tool arguments in strict **Pydantic models** (`BaseModel`).
- Use `Field(description=..., ge=..., le=..., pattern=...)` to constrain the LLM's parameter choices and prevent malformed tool calls.

```python
class AnswerSubmissionInput(BaseModel):
    user_id: str = Field(min_length=3, max_length=64, description="Candidate ID.")
    item_id: str = Field(description="Unique ID of the question being answered.")
    submitted_answer: str = Field(pattern=r"^[A-Da-d]$", description="Option key 'A', 'B', 'C', or 'D'.")
    candidate_reasoning: Optional[str] = Field(default=None, description="Optional reasoning.")
```

### 1.4 Guided Error Handling with Recovery Suggestions
- **Never crash or raise unhandled exceptions back into the model context.**
- Return structured error dictionaries containing `error_code`, `message`, and an actionable `recovery_suggestion` so the LLM can self-correct on its next turn.

```python
class ToolErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    recovery_suggestion: str

# Example return on missing resource:
return ToolErrorResponse(
    error_code="ITEM_NOT_FOUND",
    message=f"Item ID '{item_id}' does not exist in the active question bank.",
    recovery_suggestion="Call 'fetch_adaptive_drill_item' first to obtain a valid active question ID.",
).model_dump()
```

---

## 2. Context & Memory Architecture

### 2.1 Robust System Constitutions
Define a formal "Constitution" in system prompts establishing:
1. **Persona & Tone**: Professional role, expertise level, communication style.
2. **Authority & Grounding**: Canonical reference sources, documentation boundaries, anti-hallucination rules.
3. **Operational Directives**: How tool calls are routed and how errors are handled.
4. **Safety Boundaries**: Explicit constraints on what the agent must *never* do.

### 2.2 History Compaction & Sliding Windows
- Manage context bloat to prevent latency degradation and token overflow.
- Implement a sliding window for recent turns combined with extractive/abstractive summarization for older conversational turns.

```python
def compact_history(messages: List[Message], max_turns: int = 10) -> tuple[List[Message], str]:
    if len(messages) <= max_turns:
        return messages, ""
    older_turns = messages[:-max_turns]
    recent_window = messages[-max_turns:]
    summary = generate_summary(older_turns)
    return recent_window, summary
```

### 2.3 Persistent Multi-User Session State
- Multi-user isolation: Each user must have an isolated data namespace (e.g. `data/user_profiles/{user_id}.json` or database partition).
- Cross-session memory: User preferences, historical mastery scores, error patterns, and spaced repetition states must persist across application restarts.

### 2.4 Asynchronous Background Memory Operations
- Memory consolidation, profile writes, embedding calculations, and analytics must execute in background tasks (`asyncio.create_task` or worker queue) to avoid blocking the interactive chat thread.

---

## 3. Orchestration & Logic

### 3.1 Proven Multi-Agent Design Patterns
Avoid monolithic agents for complex domains. Use structured ADK patterns:
- **Coordinator Pattern**: A root orchestrator evaluates user intent and routes to specialist sub-agents (e.g., `DiagnosticAgent`, `AdaptiveDrillAgent`, `SocraticTutorAgent`, `ProgressAnalyticsAgent`).
- **Sequential / Pipeline Pattern**: Output of Agent A feeds into Agent B for multi-step refinement.

### 3.2 Strategic Model Routing
Route tasks to the optimal model based on latency and complexity:
- **Lightweight / Fast Model (`gemini-2.5-flash`)**: Quizzes, answer grading, classification, UI actions, status reports.
- **Deep-Reasoning Model (`gemini-2.5-pro`)**: Socratic deep-dive discussions, architectural trade-off evaluations, complex multi-document synthesis.

### 3.3 Guardrails & Self-Evaluation Plugins
- **Input Guardrail**: Detect and reject prompt injections and adversarial overrides.
- **Soundness Verifier**: Verify that recommended services and architectures exist and follow official best practices.
- **Self-Evaluation Hook**: Programmatically evaluate explanation completeness and pedagogical quality before returning responses to users.

### 3.4 Human-in-the-Loop (HITL) Confirmation Gates
- Destructive or high-stakes actions (clearing history, deleting databases, purchasing resources, resetting progress) must generate a challenge token and require explicit human confirmation.

```python
# Step 1: Generate challenge token
token = hitl_manager.create_confirmation_request(user_id, "reset_progress", details)
# Prompt user: "To confirm, enter token: 'A4F9B2'"

# Step 2: Validate token before execution
is_valid = hitl_manager.validate_and_consume_token(user_id, user_entered_token)
if is_valid:
    execute_destructive_action()
```

---

## 4. Observability & Tracing

### 4.1 Structured JSON Logging
- Use structured logging libraries (`structlog` or `json-logging`).
- Emit logs with ISO timestamps, `session_id`, `user_id`, `trace_id`, `model`, `latency_ms`, and `token_usage`.

### 4.2 Intent vs. Outcome Event Logging
Always record matching log pairs:
1. **`log_agent_intent`**: Emitted *before* tool execution, capturing intended action, target component, and parameters.
2. **`log_agent_outcome`**: Emitted *after* execution, capturing actual outcome status, latency in milliseconds, and error messages.

### 4.3 Distributed Tracing with OpenTelemetry
- Instrument agent calls, tool executions, and LLM inferences with OpenTelemetry spans (`trace_span`).
- Trace IDs link the entire request path from incoming user query to tool dispatch to final generated response.

### 4.4 Automated PII & Credential Scrubbing
- Implement a regex/DLP scrubbing processor that automatically redacts email addresses, names, API keys, and bearer tokens before payloads are written to logs or long-term memory.

```python
def redact_pii(text: str) -> str:
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", text)
    text = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_API_KEY]", text)
    return text
```

---

## 5. Infrastructure & CI/CD

### 5.1 Automated Evaluation Suites & Golden Datasets
- Maintain a golden evaluation dataset (`eval_dataset.json`) with ground-truth criteria.
- Run static evaluation tests (`agents-cli eval run` / `pytest`) measuring retrieval precision, architectural accuracy, distractor distinction, and safety compliance.

### 5.2 Infrastructure as Code (IaC)
- Manage all cloud infrastructure (Secret Manager, Cloud Run, Cloud Storage, Service Accounts, IAM bindings) declaratively using **Terraform**.

### 5.3 Secure Secret Management
- **Zero hardcoded credentials** in code or repository.
- Secrets injected securely at runtime via Google Cloud Secret Manager or environment variable loaders with runtime validation.

---

## 🚀 Quick Audit Checklist for New Agents

Before deploying an agent to production, verify:
- [ ] Every tool has a Google-format docstring (`Args`, `Returns`).
- [ ] Every tool has a strict Pydantic input schema with field constraints.
- [ ] Tool errors return structured recovery suggestions instead of raising exceptions.
- [ ] System prompt contains a formal Constitution with persona, grounding authority, and safety boundaries.
- [ ] Context compaction / sliding windows are active to prevent token bloat.
- [ ] User state is isolated by `user_id` and persists across sessions.
- [ ] Heavy memory/analytics tasks run asynchronously in background workers.
- [ ] Multi-agent architecture uses Coordinator or Pipeline patterns.
- [ ] Fast tasks route to Flash models; deep reasoning routes to Pro models.
- [ ] Safety guardrails filter prompt injections and verify factual accuracy.
- [ ] High-stakes actions require Human-in-the-Loop challenge confirmation.
- [ ] Logs are structured JSON with explicit Intent vs. Outcome pairs.
- [ ] OpenTelemetry distributed tracing spans are configured.
- [ ] PII and API credentials are automatically scrubbed from logs.
- [ ] Golden evaluation dataset with automated regression tests is present in CI/CD.
- [ ] Infrastructure is provisioned via Terraform with runtime Secret Manager injection.
