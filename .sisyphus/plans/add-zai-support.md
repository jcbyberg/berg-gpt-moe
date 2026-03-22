# Add ZAI GLM-5 Support to Hive Mind

## TL;DR

> **Quick Summary**: Add ZAI's GLM-5 as a second AI provider to Hive Mind, maintaining full Google Gemini support. Implement dual-provider architecture where both orchestrator and agents can leverage ZAI's enhanced reasoning capabilities.
>
> **Deliverables**:
> - ZAI client class (`orchestrator/ai/zai.py`) with async wrapper for synchronous SDK
> - Updated configuration to support `ZAI_API_KEY` and `zai_model` settings
> - Updated `agents_config.json` with 5 agents using `glm-5`
> - Provider factory pattern for unified client management
> - Updated `.env.example` with both API key placeholders
> - Comprehensive tests proving both providers work correctly
>
> **Estimated Effort**: Medium (8 files modified/created, ~500 lines of code)
> **Parallel Execution**: NO - sequential changes to maintain consistency
> **Critical Path**: Install deps → Create ZAI client → Update config → Update agents → Test

---

## Context

### Original Request
Add ZAI GLM-5 support to Hive Mind project while keeping Google Gemini working. Half of the 10 agents should use GLM-5 (Web Scout, Code Hunter, The Watcher, The Scholar, Fact Checker). The other half can use Gemini 2.5 or Gemini 3 Preview. Environment must support both `GOOGLE_API_KEY` and `ZAI_API_KEY`.

### Interview Summary
**Key Discussions**:
- **Integration Approach**: Use official ZAI SDK (`zai-sdk` package, `from zai import ZaiClient`)
- **Model Selection**: glm-5 for 5 assigned agents
- **Architecture Decision**: Both orchestrator AND agents use ZAI - "Both Layers" approach chosen for comprehensive GLM-5 integration
- **Async Handling**: Must wrap synchronous ZAI SDK in `asyncio.run_in_executor()`

**Research Findings**:
- ZAI Python SDK: `zai-sdk` package (NOT `zai-sdk-python`)
- Official docs: https://docs.z.ai/guides/llm/glm-5
- ZAI SDK is synchronous (blocking HTTP calls)
- GLM-5 features: Enhanced programming, deep thinking, function calling, streaming

### Metis Review
**Identified Gaps** (addressed):
- **Critical Discovery - ZAI SDK Sync Nature**: ZAI SDK uses blocking calls. **FIX**: Wrap in `asyncio.run_in_executor()` to avoid blocking async event loop
- **Critical Discovery - Model Field Decorative**: Current `model` field unused. **FIX**: Make model field functional - agents use their assigned model, orchestrator uses ZAI for planning/synthesis
- **Critical Discovery - SDK Package Name**: Plan mentioned wrong package. **FIX**: Use correct `zai-sdk` package
- **Medium Risk - No `.env.example` Exists**: Only `.env` with real key. **FIX**: Create proper `.env.example` with placeholders

---

## Work Objectives

### Core Objective
Integrate ZAI GLM-5 as a second AI provider in Hive Mind, enabling 5 agents to use ZAI for their AI-powered reasoning and planning tasks, while maintaining full Google Gemini support for remaining 5 agents.

### Concrete Deliverables
- `orchestrator/ai/zai.py` - New ZAI client class with async wrapper
- `orchestrator/ai/__init__.py` - Export ZaiClient and factory function
- `orchestrator/config.py` - Add `zai_api_key` and `zai_model` settings
- `schemas/agents_config.json` - Update 5 agents to use `glm-5` model
- `.env.example` - Template with both API keys
- `pyproject.toml` - Add `zai-sdk` dependency
- Tests proving both providers work independently

### Definition of Done
- [ ] Both `GOOGLE_API_KEY` and `ZAI_API_KEY` can be set in `.env`
- [ ] All 5 GLM-5 agents successfully use ZaiClient for their operations
- [ ] Orchestrator uses ZaiClient for planning (`plan_mission`) and synthesis (`synthesize_results`)
- [ ] Existing 5 Gemini agents continue working without changes
- [ ] All tests pass (import verification, config loading, both providers functional)
- [ ] No blocking calls in async context (ZAI client properly wrapped)

### Must Have
- Official ZAI SDK (`zai-sdk` package, not `zai-sdk-python`)
- Async wrapper for synchronous ZAI SDK
- Provider factory function (`get_ai_client(provider)`)
- Both providers functional in same codebase
- `model` field becomes functional (agents use their assigned model)

### Must NOT Have (Guardrails)
- **NO** removal of Gemini support - all existing agents must continue working
- **NO** modification to agent tool integrations (Tavily, GitHub, etc. remain unchanged)
- **NO** architectural refactor to support provider switching per-request (use config-based assignment)
- **NO** streaming support in V1 for ZAI (focus on non-streaming first)
- **NO** thinking mode configuration in V1 (hardcode `thinking={"type": "disabled"}`)
- **NO** OpenAI-compatible endpoint approach (use native SDK)

---

## Verification Strategy (MANDATORY)

> **UNIVERSAL RULE: ZERO HUMAN INTERVENTION**
> ALL tasks in this plan MUST be verifiable WITHOUT any human action.
> This is NOT conditional — it applies to EVERY task, regardless of test strategy.
> **FORBIDDEN** — acceptance criteria that require:
> - "User manually tests..." / "사용자가 직접 테스트..."
> - "User visually confirms..." / "사용자가 눈으로 확인..."
> - "User interacts with..." / "사용자가 직접 조작..."
> - "Ask user to verify..." / "사용자에게 확인 요청..."
> - ANY step where a human must perform an action
>
> **ALL verification is executed by agent** using tools (Playwright, interactive_bash, curl, etc.). No exceptions.

### Test Decision
- **Infrastructure exists**: YES (pytest already configured)
- **Automated tests**: YES (TDD - tests first, then implementation)
- **Framework**: pytest

### If TDD Enabled

Each TODO follows RED-GREEN-REFACTOR:

**Task Structure:**
1. **RED**: Write failing test first
   - Test file: `orchestrator/ai/tests/test_zai.py`
   - Test command: `pytest orchestrator/ai/tests/test_zai.py -v`
   - Expected: FAIL (test exists, implementation doesn't)
2. **GREEN**: Implement minimum code to pass
   - Command: `pytest orchestrator/ai/tests/test_zai.py -v`
   - Expected: PASS
3. **REFACTOR**: Clean up while keeping green
   - Command: `pytest orchestrator/ai/tests/test_zai.py -v`
   - Expected: PASS (still)

**Test Setup Task** (already exists, skip):
- Tests infrastructure already configured with pytest

### Agent-Executed QA Scenarios (MANDATORY — ALL tasks)

> Whether TDD is enabled or not, EVERY task MUST include Agent-Executed QA Scenarios.
> - **With TDD**: QA scenarios complement unit tests at integration/E2E level
> - **Without TDD**: QA scenarios are PRIMARY verification method
>
> These describe how executing agent DIRECTLY verifies deliverable
> by running it — opening browsers, executing commands, sending API requests.
> The agent performs what a human tester would do, but automated via tools.

**Verification Tool by Deliverable Type:**

| Type | Tool | How Agent Verifies |
|------|------|-------------------|
| **Backend/CLI** | Bash (Python commands, curl) | Run Python scripts, execute imports, verify outputs |
| **Library/Module** | Bash (Python REPL) | Import, call functions, compare output |
| **Config/Infra** | Bash (shell commands) | Apply config, run state checks, validate |

**Each Scenario MUST Follow This Format:**

```
Scenario: [Descriptive name — what user action/flow is being verified]
  Tool: [Bash / Python REPL]
  Preconditions: [What must be true before this scenario runs]
  Steps:
    1. [Exact action with specific command/function call]
    2. [Next action with expected intermediate state]
    3. [Assertion with exact expected value]
  Expected Result: [Concrete, observable outcome]
  Failure Indicators: [What would indicate failure]
  Evidence: [Output capture path / screenshot]
```

**Scenario Detail Requirements:**
- **Commands**: Specific shell commands with exact paths (`python -c "..."`)
- **Assertions**: Exact values (`exit code 0`, `output contains "ZAI client importable"`, not `verify it works`)
- **Negative Scenarios**: At least ONE failure/error scenario per feature
- **Evidence Paths**: Specific file paths (`.sisyphus/evidence/task-N-scenario-name.txt`)

**Anti-patterns (NEVER write scenarios like this):**
- ❌ "Verify ZAI client initializes correctly"
- ❌ "Check that agents can use GLM-5"
- ❌ "Test that both providers work"

**Write scenarios like this instead:**
- ✅ `python -c "from orchestrator.ai.zai import ZaiClient; print('Import OK')"` → Assert `stdout contains "Import OK"`
- ✅ `python -c "from orchestrator.config import get_settings; s = get_settings(); print(type(s.zai_api_key))"` → Assert `stdout contains "<class 'str'>"`
- ✅ `python -c "import json; data = json.load(open('schemas/agents_config.json')); print([k for k,v in data['agents'].items() if v['model']=='glm-5'])"` → Assert `stdout contains 5 keys`

**Evidence to Capture:**
- Output captures for all verification scenarios
- Config file validation outputs
- Test results (`pytest` output)

---

## Execution Strategy

### Parallel Execution Waves

> Sequential execution required to maintain consistency and avoid breaking changes.

```
Wave 1 (Start Immediately):
├── Task 1: Install zai-sdk dependency
└── Task 2: Create .env.example template

Wave 2 (After Wave 1):
├── Task 3: Create ZAI client class with async wrapper
├── Task 4: Update config.py with ZAI settings
└── Task 5: Create provider factory function

Wave 3 (After Wave 2):
├── Task 6: Update agents_config.json for GLM-5 agents
├── Task 7: Update orchestrator main.py to use provider factory
└── Task 8: Write tests for ZAI client

Critical Path: Task 1 → Task 3 → Task 6 → Task 7 → Task 8
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2, 3 | None |
| 2 | None | 5 | None |
| 3 | 1 | 4, 6 | 2 |
| 4 | 3 | 5 | 3 |
| 5 | 4 | 7 | 4 |
| 6 | 5 | 8 | 3, 5, 7, 8 |
| 7 | 6 | 8 | None (final) |
| 8 | 7 | None | None (final) |

### Agent Dispatch Summary

| Wave | Tasks | Recommended Agents |
|------|-------|-------------------|
| 1 | 1, 2 | task(category="quick", load_skills=[], run_in_background=false) |
| 2 | 3, 4, 5 | task(category="unspecified-high", load_skills=[], run_in_background=false) |
| 3 | 6, 7, 8 | task(category="unspecified-high", load_skills=[], run_in_background=false) |

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info.

- [x] 1. Install zai-sdk dependency

  **What to do**:
  - Add `zai-sdk` to dependencies in `pyproject.toml`
  - Verify correct package name (NOT `zai-sdk-python`)
  - Remove any duplicate pytest sections if found

  **Must NOT do**:
  - Install `zai-sdk-python` (wrong package name)
  - Modify other dependencies (pytest, fastapi, etc.)

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Simple dependency update, well-defined action
  - **Skills**: None needed for pip operations
  - **Skills Evaluated but Omitted**: All agent skills are domain-specific (web, AI, etc.)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2, Task 3
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/ai/gemini.py:11-154` - ZaiClient class structure to match (lazy init, configure method, generate_response, plan_mission, synthesize_results)
  - `orchestrator/config.py` - Settings class with environment variable loading
  - `pyproject.toml` - Project dependencies format

  **API/Type References** (contracts to implement against):
  - `zai-sdk` package documentation - ZaiClient interface methods

  **Test References** (testing patterns to follow):
  - Existing pytest structure in `tests/` directory

  **Documentation References** (specs and requirements):
  - User's interview decisions - use both providers, GLM-5 for 5 agents

  **External References** (libraries and frameworks):
  - Official ZAI docs: https://docs.z.ai/guides/llm/glm-5
  - Official ZAI SDK repo: https://github.com/zai-org/z-ai-sdk-python

  **WHY Each Reference Matters** (explain relevance):
  - `gemini.py` structure provides template for async wrapper pattern needed for ZAI
  - `config.py` shows how to add new settings fields with pydantic
  - Follow `zai-sdk` docs for correct method signatures

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] Test file created: N/A (dependency update doesn't require new test)
  - [ ] pip install zai-sdk succeeds without errors
  - [ ] Command: `pip install zai-sdk` → exit code 0

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Dependency install succeeds**
  Tool: Bash (pip)
  Preconditions: Internet connection available
  Steps:
    1. Run: `pip install zai-sdk`
    2. Wait for completion
    3. Check exit code
  Expected Result: Package installed successfully
  Evidence: Terminal output showing successful install

  **Scenario 2: Verify correct package name**
  Tool: Bash (pip)
  Preconditions: pip command available
  Steps:
    1. Run: `pip show zai-sdk`
    2. Assert output shows package info
  Expected Result: Package exists and shows metadata
  Evidence: Output from `pip show zai-sdk`

  **Scenario 3: Duplicate pytest sections removed**
  Tool: Bash (grep)
  Preconditions: pyproject.toml exists
  Steps:
    1. Run: `grep -c "pytest" pyproject.toml`
    2. Count occurrences
    3. Assert count == 1
  Expected Result: Only one pytest section
  Evidence: grep output count

  **Evidence to Capture:**
  - [ ] pip install output saved to .sisyphus/evidence/task-1-install.txt
  - [ ] pip show output saved to .sisyphus/evidence/task-1-show.txt
  - [ ] grep count output saved to .sisyphus/evidence/task-1-duplicate.txt

  **Commit**: NO

---

- [x] 2. Create .env.example template

  **What to do**:
  - Create `.env.example` file with placeholders for both API keys
  - Include comments explaining each setting
  - Include all current environment variables

  **Must NOT do**:
  - Modify existing `.env` file (contains real API keys)
  - Remove any existing settings

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Simple file creation, well-defined content
  - **Skills**: None needed for file creation
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Task 5, Task 6, Task 7
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/config.py:10-44` - Settings structure, environment variable patterns
  - `.env` file format - key=value pairs

  **API/Type References** (contracts to implement against):
  - Settings class in pydantic_settings

  **Test References** (testing patterns to follow):
  - N/A (file creation task)

  **Documentation References** (specs and requirements):
  - User's requirement: support both API keys in environment
  - Existing `.env` file structure

  **External References** (libraries and frameworks):
  - Python environment variable patterns

  **WHY Each Reference Matters** (explain relevance):
  - Config.py shows how environment variables are loaded via pydantic
  - Use same comment style as existing settings for consistency

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] .env.example file created
  - [ ] File contains ZAI_API_KEY placeholder
  - [ ] File contains GOOGLE_API_KEY placeholder
  - [ ] File contains all existing settings from config.py

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: .env.example file exists with correct content**
  Tool: Bash (test -f)
  Preconditions: .env.example created
  Steps:
    1. Run: `test -f .env.example`
    2. Assert file is regular file
    3. Assert file contains "ZAI_API_KEY="
    4. Assert file contains "GOOGLE_API_KEY="
    5. Assert file contains all required settings
  Expected Result: File exists with all placeholders
  Evidence: test -f output

  **Scenario 2: .env.example does not contain real API keys**
  Tool: Bash (grep)
  Preconditions: .env.example created
  Steps:
    1. Run: `grep -v "AIzaSy" .env.example`
    2. Assert grep fails (exit code 1, no output)
    3. Assert grep -v "placeholder" .env.example shows placeholder comments
  Expected Result: No real keys in .env.example
  Evidence: Grep output showing no matches

  **Evidence to Capture:**
  - [ ] test -f output saved to .sisyphus/evidence/task-2-exists.txt
  - [ ] grep output saved to .sisyphus/evidence/task-2-no-keys.txt

  **Commit**: NO

---

- [x] 3. Create ZAI client class with async wrapper

  **What to do**:
  - Create `orchestrator/ai/zai.py` following `gemini.py` structure
  - Implement ZaiClient class with async methods wrapping synchronous SDK
  - Use `asyncio.run_in_executor()` for SDK calls
  - Match GeminiClient interface: configure(), generate_response(), plan_mission(), synthesize_results()
  - Add safety settings, retry logic, error handling
  - Use glm-5 model with hardcode `thinking={"type": "disabled"}` initially

  **Must NOT do**:
  - Implement streaming support in V1
  - Remove error handling or retry logic from GeminiClient pattern
  - Change method signatures to not match GeminiClient
  - Use OpenAI SDK or OpenAI-compatible endpoint

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: Complex async wrapper implementation, requires careful attention to SDK sync nature and error handling patterns
  - **Skills**: None needed for this implementation
  - **Skills Evaluated but Omitted**: No web/AI tool integration needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 4, Task 5, Task 6
  - **Blocked By**: Task 1 (dependency install)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/ai/gemini.py:1-155` - Complete GeminiClient class structure for exact pattern matching
  - `orchestrator/ai/gemini.py:19-31` - Lazy initialization pattern
  - `orchestrator/ai/gemini.py:27-48` - configure() method with safety settings
  - `orchestrator/ai/gemini.py:50-91` - generate_response() async method with GenerationConfig
  - `orchestrator/ai/gemini.py:93-130` - plan_mission() and synthesize_results() methods
  - `orchestrator/ai/gemini.py:155-183` - Error handling with try/except

  **API/Type References** (contracts to implement against):
  - ZaiClient class from zai-sdk - study docs for correct method signatures
  - Match GeminiClient interface exactly for compatibility

  **Test References** (testing patterns to follow):
  - Test structure in `tests/` directory - will follow pytest pattern

  **Documentation References** (specs and requirements):
  - User's requirement: use official zai-sdk with glm-5
  - Async handling requirement: wrap sync SDK in executor

  **External References** (libraries and frameworks):
  - ZAI docs: https://docs.z.ai/guides/llm/glm-5
  - ZAI SDK repo: https://github.com/zai-org/z-ai-sdk-python

  **WHY Each Reference Matters** (explain relevance):
  - gemini.py structure is proven pattern that works with rest of codebase
  - Lazy init ensures client only initializes when needed
  - Safety settings, error handling patterns must match for consistency
  - Must study zai-sdk docs for correct async-compatible method calls

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] Test file created: orchestrator/ai/tests/test_zai.py
  - [ ] Test covers: ZaiClient lazy init
  - [ ] Test covers: configure() sets API key
  - [ ] Test covers: generate_response() wraps SDK call in executor
  - [ ] Test covers: SDK call returns correct response
  - [ ] Test covers: plan_mission() returns agent IDs
  - [ ] Test covers: synthesize_results() returns synthesized answer
  - [ ] Test covers: Error handling for missing API key
  - [ ] pytest orchestrator/ai/tests/test_zai.py -v → PASS (all tests)

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: ZaiClient imports without errors**
  Tool: Bash (Python)
  Preconditions: zai.py file exists
  Steps:
    1. Run: `python -c "from orchestrator.ai.zai import ZaiClient; print('Import successful')"`
    2. Assert stdout contains "Import successful"
  Expected Result: Class imports cleanly
  Evidence: Python output

  **Scenario 2: ZaiClient lazy initialization (not configured on import)**
  Tool: Bash (Python)
  Preconditions: No ZAI_API_KEY set
  Steps:
    1. Run: `python -c "from orchestrator.ai.zai import ZaiClient; c = ZaiClient(); print(f'Configured: {c._configured}')"`
    2. Assert "Configured: False" in output
  Expected Result: Client created but not configured
  Evidence: Python output

  **Scenario 3: ZaiClient.configure() with valid key**
  Tool: Bash (Python)
  Preconditions: ZAI_API_KEY environment variable set to "test_key"
  Steps:
    1. Run: `ZAI_API_KEY=test_key python -c "from orchestrator.ai.zai import ZaiClient; c = ZaiClient(); c.configure(); print(f'Configured: {c._configured}')"`
    2. Assert "Configured: True" in output
  Expected Result: Client configures successfully
  Evidence: Python output

  **Scenario 4: generate_response() wraps SDK call in executor**
  Tool: Bash (Python)
  Preconditions: ZAI_API_KEY set
  Steps:
    1. Run: `python -c "
import asyncio
from orchestrator.ai.zai import ZaiClient
async def test():
    c = ZaiClient()
    c.configure()
    result = await c.generate_response('test')
    print(result)
asyncio.run(test())
" `
    2. Assert output contains non-empty result
    Expected Result: Async wrapper works, SDK call executes
  Evidence: Python output

  **Scenario 5: plan_mission() returns agent list**
  Tool: Bash (Python)
  Preconditions: ZAI_API_KEY set
  Steps:
    1. Run: `python -c "
import asyncio
from orchestrator.ai.zai import ZaiClient
async def test():
    c = ZaiClient()
    c.configure()
    agents = await c.plan_mission('search web', [])
    print(agents)
asyncio.run(test())
" `
    2. Assert agents is a list
    3. Assert agents have 'id' field
  Expected Result: Agent planning works
  Evidence: Python output

  **Scenario 6: synthesize_results() returns answer**
  Tool: Bash (Python)
  Preconditions: ZAI_API_KEY set
  Steps:
    1. Run: `python -c "
import asyncio
from orchestrator.ai.zai import ZaiClient
async def test():
    c = ZaiClient()
    c.configure()
    result = await c.synthesize_results('test', [])
    print(result)
asyncio.run(test())
" `
    2. Assert result is a string
    3. Assert result contains "test"
  Expected Result: Synthesis works
  Evidence: Python output

  **Scenario 7: Error handling for missing API key**
  Tool: Bash (Python)
  Preconditions: No ZAI_API_KEY set
  Steps:
    1. Run: `python -c "
import asyncio
from orchestrator.ai.zai import ZaiClient
async def test():
    c = ZaiClient()
    result = await c.generate_response('test')
    print(result)
asyncio.run(test())
" 2>&1 | grep -i "error"`
    2. Assert grep finds error message
  Expected Result: Graceful error logged, not crash
  Evidence: Python stderr output

  **Evidence to Capture:**
  - [ ] Import test output saved to .sisyphus/evidence/task-3-import.txt
  - [ ] Lazy init output saved to .sisyphus/evidence/task-3-lazy.txt
  - [ ] Configure test output saved to .sisyphus/evidence/task-3-configure.txt
  - [ ] generate_response output saved to .sisyphus/evidence/task-3-generate.txt
  - [ ] plan_mission output saved to .sisyphus/evidence/task-3-plan.txt
  - [ ] synthesize_results output saved to .sisyphus/evidence/task-3-synthesize.txt
  - [ ] Error handling output saved to .sisyphus/evidence/task-3-error.txt

  **Commit**: YES
  - Message: `feat(zai): add ZaiClient with async wrapper for zai-sdk`
  - Files: `orchestrator/ai/zai.py`

---

- [x] 4. Update config.py with ZAI settings

  **What to do**:
  - Add `zai_api_key: str = ""` to Settings class
  - Add `zai_model: str = "glm-5"` to Settings class
  - Follow pydantic Settings pattern for environment variable loading
  - Add validation to ensure either GOOGLE_API_KEY or ZAI_API_KEY is present

  **Must NOT do**:
  - Remove any existing Google or AI-related settings
  - Change environment variable loading pattern
  - Modify Redis or LanceDB settings

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Simple settings update following pydantic pattern
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (with Tasks 3, 5)
  - **Blocks**: Task 6, Task 7
  - **Blocked By**: Task 3 (ZaiClient must exist)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/config.py:5-47` - Settings class structure
  - `orchestrator/config.py:10-44` - Environment variable loading pattern
  - `orchestrator/config.py:24-30` - Redis settings pattern for reference

  **API/Type References** (contracts to implement against):
  - Settings class with new string fields

  **Test References** (testing patterns to follow):
  - Test config loading pattern in tests/

  **Documentation References** (specs and requirements):
  - User's requirement: both API keys supported
  - Existing Settings structure

  **External References** (libraries and frameworks):
  - Pydantic Settings documentation

  **WHY Each Reference Matters** (explain relevance):
  - config.py lines 10-44 show exact pattern for adding settings
  - Use same type annotation and default values pattern
  - Add validation logic to ensure at least one AI provider is configured

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] Config loads with zai_api_key field
  - [ ] Config loads with zai_model field
  - [ ] Config validates at least one API key present
  - [ ] Config defaults zai_model to "glm-5"
  - [ ] Command: `python -c "from orchestrator.config import get_settings; s = get_settings(); print(hasattr(s, 'zai_api_key') and hasattr(s, 'zai_model'))"` → output shows both fields

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Config loads with zai_api_key field**
  Tool: Bash (Python)
  Preconditions: config.py updated
  Steps:
    1. Run: `python -c "from orchestrator.config import get_settings; s = get_settings(); print(hasattr(s, 'zai_api_key'))"`
    2. Assert stdout is "True"
  Expected Result: zai_api_key field exists
  Evidence: Python output

  **Scenario 2: Config loads with zai_model field**
  Tool: Bash (Python)
  Preconditions: config.py updated
  Steps:
    1. Run: `python -c "from orchestrator.config import get_settings; s = get_settings(); print(hasattr(s, 'zai_model'))"`
    2. Assert stdout is "True"
  Expected Result: zai_model field exists
  Evidence: Python output

  **Scenario 3: Config validates at least one API key present**
  Tool: Bash (Python)
  Preconditions: config.py updated with validation
  Steps:
    1. Run: `python -c "
from orchestrator.config import get_settings
s = get_settings()
has_google = bool(s.google_api_key)
has_zai = bool(s.zai_api_key)
print(f'Has google: {has_google}, has zai: {has_zai}')
print(f'Has either: {has_google or has_zai}')
" `
    2. Assert "Has either: True" in output
  Expected Result: Validation requires at least one provider
  Evidence: Python output

  **Scenario 4: Config defaults zai_model to glm-5**
  Tool: Bash (Python)
  Preconditions: No ZAI_MODEL env var set
  Steps:
    1. Run: `python -c "from orchestrator.config import get_settings; s = get_settings(); print(s.zai_model)"`
    2. Assert stdout contains "glm-5"
  Expected Result: Default value set correctly
  Evidence: Python output

  **Scenario 5: Config loads both API keys from environment**
  Tool: Bash (Python)
  Preconditions: Both GOOGLE_API_KEY and ZAI_API_KEY env vars set
  Steps:
    1. Run: `python -c "
from orchestrator.config import get_settings
s = get_settings()
print(f'Google: {s.google_api_key[:20]}...')
print(f'ZAI: {s.zai_api_key[:20]}...')
" `
    2. Assert both outputs show keys
  3. Assert keys don't show full values
  Expected Result: Both keys loaded and masked
  Evidence: Python output

  **Evidence to Capture:**
  - [ ] zai_api_key field test saved to .sisyphus/evidence/task-4-zai-key.txt
  - [ ] zai_model field test saved to .sisyphus/evidence/task-4-model.txt
  - [ ] Validation test saved to .sisyphus/evidence/task-4-validate.txt
  - [ ] Default value test saved to .sisyphus/evidence/task-4-default.txt
  - [ ] Both keys test saved to .sisyphus/evidence/task-4-both.txt

  **Commit**: YES
  - Message: `feat(config): add ZAI_API_KEY and zai_model to Settings`
  - Files: `orchestrator/config.py`

---

- [x] 5. Create provider factory function

  **What to do**:
  - Create `get_ai_client(provider: str)` function in `__init__.py`
  - Function returns ZaiClient or GeminiClient based on provider argument
  - Add provider type constants or enum
  - Handle invalid provider gracefully with error
  - Export both client instances (gemini_client, zai_client) for backward compatibility

  **Must NOT do**:
  - Remove existing gemini_client singleton
  - Change GeminiClient or ZaiClient interfaces
  - Modify how existing code uses clients

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify this choice.
  - **Category**: `quick`
    - Reason: Simple factory function, follows dependency injection pattern
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Task 6
  - **Blocked By**: Task 3 (ZaiClient), Task 4 (config)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/ai/__init__.py:157-183` - Current singleton export pattern
  - `orchestrator/main.py` - How gemini_client is imported and used

  **API/Type References** (contracts to implement against):
  - Factory function signature: `def get_ai_client(provider: str) -> Union[GeminiClient, ZaiClient]`

  **Test References** (testing patterns to follow):
  - N/A (factory function)

  **Documentation References** (specs and requirements):
  - User's requirement: support both providers via factory

  **External References** (libraries and frameworks):
  - Factory pattern best practices in Python

  **WHY Each Reference Matters** (explain relevance):
  - __init__.py shows existing export pattern to follow
  - Need to see how clients are used in main.py
  - Factory enables clean provider switching without modifying all call sites

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] Factory function created in __init__.py
  - [ ] Function accepts "zai" or "gemini" provider argument
  - [ ] Function returns ZaiClient for "zai" provider
  - [ ] Function returns GeminiClient for "gemini" provider
  - [ ] Function raises ValueError for invalid provider
  - [ ] Both gemini_client and zai_client exported for compatibility
  - [ ] Command: `python -c "from orchestrator.ai import get_ai_client; print(type(get_ai_client('zai')))"` → output shows `ZaiClient` class

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Factory function imports successfully**
  Tool: Bash (Python)
  Preconditions: __init__.py updated
  Steps:
    1. Run: `python -c "from orchestrator.ai import get_ai_client; print('Import OK')"`
    2. Assert stdout contains "Import OK"
  Expected Result: Factory function exists
  Evidence: Python output

  **Scenario 2: Factory returns ZaiClient for "zai" provider**
  Tool: Bash (Python)
  Preconditions: ZaiClient class exists
  Steps:
    1. Run: `python -c "from orchestrator.ai import get_ai_client; c = get_ai_client('zai'); print(type(c).__name__)"`
    2. Assert output contains "ZaiClient"
  Expected Result: Correct client type returned
  Evidence: Python output

  **Scenario 3: Factory returns GeminiClient for "gemini" provider**
  Tool: Bash (Python)
  Preconditions: GeminiClient class exists
  Steps:
    1. Run: `python -c "from orchestrator.ai import get_ai_client; c = get_ai_client('gemini'); print(type(c).__name__)"`
    2. Assert output contains "GeminiClient"
  Expected Result: Correct client type returned
  Evidence: Python output

  **Scenario 4: Factory raises ValueError for invalid provider**
  Tool: Bash (Python)
  Preconditions: Factory function exists
  Steps:
    1. Run: `python -c "from orchestrator.ai import get_ai_client; get_ai_client('invalid') 2>&1 | head -5"`
    2. Assert output contains "ValueError"
    3. Assert output contains "provider"
  Expected Result: Graceful error for invalid provider
  Evidence: Python error output

  **Scenario 5: Backward compatibility - gemini_client exported**
  Tool: Bash (Python)
  Preconditions: __init__.py updated
  Steps:
    1. Run: `python -c "from orchestrator.ai import gemini_client; print('gemini_client available')"`
    2. Assert stdout contains "gemini_client available"
  Expected Result: Old import still works
  Evidence: Python output

  **Scenario 6: Backward compatibility - zai_client exported**
  Tool: Bash (Python)
  Preconditions: __init__.py updated
  Steps:
    1. Run: `python -c "from orchestrator.ai import zai_client; print('zai_client available')"`
    2. Assert stdout contains "zai_client available"
  Expected Result: New import available
  Evidence: Python output

  **Evidence to Capture:**
  - [ ] Factory import test saved to .sisyphus/evidence/task-5-import.txt
  - [ ] ZaiClient return test saved to .sisyphus/evidence/task-5-zai.txt
  - [ ] GeminiClient return test saved to .sisyphus/evidence/task-5-gemini.txt
  - [ ] Invalid provider test saved to .sisyphus/evidence/task-5-invalid.txt
  - [ ] gemini_client export test saved to .sisyphus/evidence/task-5-old-gemini.txt
  - [ ] zai_client export test saved to .sisyphus/evidence/task-5-new-zai.txt

  **Commit**: YES
  - Message: `feat(ai): add get_ai_client provider factory function`
  - Files: `orchestrator/ai/__init__.py`

---

- [x] 6. Update agents_config.json for GLM-5 agents

  **What to do**:
  - Change model field to `glm-5` for 5 agents: res_01_web, res_02_code, res_04_video, res_05_academic, res_06_wiki
  - Keep all other agent fields unchanged (id, name, role, tools, hot_memory_prefix, etc.)
  - Keep remaining 5 agents with `gemini-2.5-flash` unchanged
  - Verify JSON is valid after changes

  **Must NOT do**:
  - Change any field other than `model` for those 5 agents
  - Modify agent IDs
  - Change tool integrations
  - Modify agent config schema/structure

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Simple JSON field update, clear mapping
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (with Tasks 6, 7)
  - **Blocks**: Task 7, Task 8
  - **Blocked By**: Task 5 (factory function)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `schemas/agents_config.json` - JSON structure for agents
  - `orchestrator/agents/base.py` - How model field is used

  **API/Type References** (contracts to implement against):
  - AgentConfig schema with model field

  **Test References** (testing patterns to follow):
  - N/A (JSON file update)

  **Documentation References** (specs and requirements):
  - User's requirement: 5 agents use glm-5, 5 agents use gemini-2.5-flash
  - Interview assignment: Web Scout, Code Hunter, The Watcher, The Scholar, Fact Checker use GLM-5

  **External References** (libraries and frameworks):
  - JSON schema validation

  **WHY Each Reference Matters** (explain relevance):
  - agents_config.json shows exact format to follow
  - Must maintain parity between agent IDs and models
  - Reference agent IDs from interview to confirm correct ones

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] res_01_web model changed to glm-5
  - [ ] res_02_code model changed to glm-5
  - [ ] res_04_video model changed to glm-5
  - [ ] res_05_academic model changed to glm-5
  - [ ] res_06_wiki model changed to glm-5
  - [ ] res_03_debug model remains gemini-2.5-flash
  - [ ] res_07_privacy model remains gemini-2.5-flash
  - [ ] res_08_fetch model remains gemini-2.5-flash
  - [ ] res_09_social model remains gemini-2.5-flash
  - [ ] res_10_files model remains gemini-2.5-flash
  - [ ] JSON file is valid
  - [ ] Command: `python -c "import json; data = json.load(open('schemas/agents_config.json')); glm5 = [k for k,v in data['agents'].items() if v['model']=='glm-5']; print(f'GLM-5 agents: {len(glm5)}: {glm5}'); gemini = [k for k,v in data['agents'].items() if 'gemini' in v['model'] and v['model']!='glm-5']; print(f'Gemini agents: {len(gemini)}: {gemini}')"` → output shows correct counts

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Exactly 5 agents have glm-5 model**
  Tool: Bash (Python json module)
  Preconditions: agents_config.json updated
  Steps:
    1. Run: `python -c "
import json
with open('schemas/agents_config.json') as f:
    data = json.load(f)
glm5_agents = {k: v for k, v in data['agents'].items() if v['model'] == 'glm-5'}
print(f'GLM-5 count: {len(glm5_agents)}')
print(f'IDs: {list(glm5_agents.keys())}')
" `
    2. Assert output shows "GLM-5 count: 5"
    3. Assert output shows all 5 agent IDs
  Expected Result: Exactly 5 agents use glm-5
  Evidence: Python output

  **Scenario 2: GLM-5 agents match interview assignment**
  Tool: Bash (Python json module)
  Preconditions: agents_config.json updated
  Steps:
    1. Run: `python -c "
import json
with open('schemas/agents_config.json') as f:
    data = json.load(f)
glm5_ids = {'res_01_web', 'res_02_code', 'res_04_video', 'res_05_academic', 'res_06_wiki'}
actual = {k: v['model'] for k, v in data['agents'].items() if k in glm5_ids}
expected = glm5_ids
match = set(actual.keys()) == set(expected)
print(f'Expected: {expected}')
print(f'Actual: {list(actual.keys())}')
print(f'Match: {match}')
" `
    2. Assert "Match: True" in output
  Expected Result: Correct agents assigned
  Evidence: Python output

  **Scenario 3: Remaining agents use gemini-2.5-flash**
  Tool: Bash (Python json module)
  Preconditions: agents_config.json updated
  Steps:
    1. Run: `python -c "
import json
with open('schemas/agents_config.json') as f:
    data = json.load(f)
gemini = {k: v['model'] for k, v in data['agents'].items() if 'gemini' in v['model'] and v['model'] != 'glm-5'}
print(f'Gemini agents: {len(gemini)}')
print(f'IDs: {list(gemini.keys())}')
" `
    2. Assert output shows "Gemini agents: 5"
    3. Assert output doesn't include GLM-5 agents
  Expected Result: 5 remaining agents unchanged
  Evidence: Python output

  **Scenario 4: JSON file is valid**
  Tool: Bash (Python json module)
  Preconditions: agents_config.json updated
  Steps:
    1. Run: `python -m json.tool schemas/agents_config.json 2>&1 | head -5`
    2. Assert no error in output
  Expected Result: JSON is valid
  Evidence: json.tool output

  **Evidence to Capture:**
  - [ ] 5 agents test saved to .sisyphus/evidence/task-6-count.txt
  - [ ] Assignment test saved to .sisyphus/evidence/task-6-assignment.txt
  - [ ] Remaining agents test saved to .sisyphus/evidence/task-6-gemini.txt
  - [ ] JSON validation saved to .sisyphus/evidence/task-6-valid.txt

  **Commit**: YES
  - Message: `feat(config): assign glm-5 to 5 agents (Web Scout, Code Hunter, Watcher, Scholar, Fact Checker)`
  - Files: `schemas/agents_config.json`

---

- [x] 7. Update orchestrator main.py to use provider factory

  **What to do**:
  - Import `get_ai_client` from `orchestrator.ai`
  - Replace direct `gemini_client` imports with factory call
  - Use `get_ai_client("zai")` for planning and synthesis
  - Keep `get_ai_client("gemini")` for compatibility
  - Update startup logs to show both providers available
  - Update health check to verify both providers

  **Must NOT do**:
  - Remove Gemini provider support
  - Change existing API endpoints or methods
  - Remove or refactor agent base class
  - Modify memory systems

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: Main application entry point modification, requires understanding of FastAPI startup flow and client initialization
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**: No specialized web/AI skills needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (with Tasks 6, 8)
  - **Blocks**: Task 8
  - **Blocked By**: Task 5 (factory), Task 6 (agents config)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/main.py` - How gemini_client is currently imported and used
  - `orchestrator/main.py` - Startup sequence and health check patterns
  - `orchestrator/ai/__init__.py` - Factory function export location

  **API/Type References** (contracts to implement against):
  - FastAPI app lifecycle and initialization
  - get_ai_client factory function interface

  **Test References** (testing patterns to follow):
  - Test patterns in tests/test_orchestrator.py

  **Documentation References** (specs and requirements):
  - User's requirement: orchestrator uses ZAI for planning/synthesis
  - Existing application flow

  **External References** (libraries and frameworks):
  - FastAPI startup patterns

  **WHY Each Reference Matters** (explain relevance):
  - main.py shows exact locations where client is used for planning and synthesis
  - Must update all direct gemini_client calls to use factory
  - Health check should verify both providers can initialize

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] main.py imports get_ai_client from orchestrator.ai
  - [ ] Planning uses get_ai_client("zai")
  - [ ] Synthesis uses get_ai_client("zai")
  - [ ] Startup logs show both providers available
  - [ ] Health check verifies both providers
  - [ ] Command: `python -c "
from orchestrator.main import app
from orchestrator.ai import get_ai_client
print('Factory importable')
zai_client = get_ai_client('zai')
gemini_client = get_ai_client('gemini')
print(f'ZAI client type: {type(zai_client).__name__}')
print(f'Gemini client type: {type(gemini_client).__name__}')
"` → output shows both client types

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: main.py imports factory function**
  Tool: Bash (Python)
  Preconditions: main.py updated
  Steps:
    1. Run: `python -c "from orchestrator.main import app; print('main.py loaded')"`
    2. Assert stderr doesn't contain "ModuleNotFoundError"
  Expected Result: Module imports cleanly
  Evidence: Python stderr output

  **Scenario 2: Planning uses ZAI client**
  Tool: Bash (Python)
  Preconditions: ZAI_API_KEY set, main.py updated
  Steps:
    1. Run: `python -c "
import sys
sys.path.insert(0, '.')
from orchestrator.ai import get_ai_client
from orchestrator.main import app

# Check if planning uses ZAI
print('Checking if planning route uses ZAI...')
# Note: This verifies the client is available for planning tasks
print('ZAI client available:', type(get_ai_client('zai')).__name__)
" `
    2. Assert output shows "ZAI client available"
  Expected Result: Factory provides ZaiClient for planning
  Evidence: Python output

  **Scenario 3: Synthesis uses ZAI client**
  Tool: Bash (Python)
  Preconditions: ZAI_API_KEY set, main.py updated
  Steps:
    1. Run: `python -c "
import sys
sys.path.insert(0, '.')
from orchestrator.ai import get_ai_client
from orchestrator.main import app

print('Checking if synthesis uses ZAI...')
print('ZAI client available:', type(get_ai_client('zai')).__name__)
" `
    2. Assert output shows "ZAI client available"
  Expected Result: Factory provides ZaiClient for synthesis
  Evidence: Python output

  **Scenario 4: Both providers available in startup logs**
  Tool: Bash (Python)
  Preconditions: Both API keys set
  Steps:
    1. Run: `python orchestrator/main.py 2>&1 | grep -i "provider\|available\|zai\|gemini" | head -20`
    2. Assert grep shows both providers mentioned
  Expected Result: Startup logs show both providers ready
  Evidence: Grep output from startup

  **Evidence to Capture:**
  - [ ] Import test output saved to .sisyphus/evidence/task-7-import.txt
  - [ ] Planning ZAI test saved to .sisyphus/evidence/task-7-planning.txt
  - [ ] Synthesis ZAI test saved to .sisyphus/evidence/task-7-synthesis.txt
  - [ ] Startup logs output saved to .sisyphus/evidence/task-7-startup.txt

  **Commit**: YES
  - Message: `feat(orchestrator): use provider factory, enable ZAI for planning/synthesis`
  - Files: `orchestrator/main.py`

---

- [x] 8. Write comprehensive tests for ZAI client

  **What to do**:
  - Create with comprehensive tests
  - Test all ZaiClient methods: configure, generate_response, plan_mission, synthesize_results
  - Test error handling: missing API key, invalid API key, SDK errors
  - Test async wrapper behavior: executor wrapping, non-blocking
  - Follow pytest patterns from existing tests/
  - Add fixtures for test data

  **Must NOT do**:
  - Test any other client types
  - Test agent behaviors (those are out of scope)
  - Test tool integrations (Tavily, GitHub, etc.)

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Follows existing test patterns, uses pytest
  - **Skills**: None needed
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: None (can start after Task 7)
  - **Blocked By**: Task 3 (ZaiClient must exist)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `tests/test_hot_memory.py` - pytest test patterns
  - `tests/test_agents.py` - Test structure patterns
  - `orchestrator/ai/gemini.py` - Client class to test
  - `orchestrator/ai/zai.py` - New client class structure

  **API/Type References** (contracts to implement against):
  - ZaiClient interface methods to test

  **Test References** (testing patterns to follow):
  - Existing test files for pytest patterns
  - pytest fixtures and parametrization

  **Documentation References** (specs and requirements):
  - ZaiClient methods and behavior to verify

  **External References** (libraries and frameworks):
  - pytest documentation for test structure

  **WHY Each Reference Matters** (explain relevance):
  - test_hot_memory.py shows pytest patterns used in project
  - Follow same naming and structure conventions
  - ZaiClient has same interface as GeminiClient, test both similarly

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled):**
  - [ ] test_zai.py file created
  - [ ] Test class exists: TestZaiClient
  - [ ] Test lazy initialization: test_not_configured_on_import
  - [ ] Test configure: test_configure_with_valid_key, test_configure_with_no_key_warning
  - [ ] Test generate_response: test_generate_response_success, test_generate_response_executor_wrapper
  - [ ] Test plan_mission: test_plan_mission_returns_agents
  - [ ] Test synthesize_results: test_synthesize_results_returns_answer
  - [ ] Test error handling: test_error_handling_for_invalid_key
  - [ ] pytest orchestrator/ai/tests/test_zai.py -v → PASS (all tests)

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed):**

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Test file created and pytest discovers it**
  Tool: Bash (pytest)
  Preconditions: test_zai.py created
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py --collect-only 2>&1 | grep "test_zai"`
    2. Assert grep finds test file
  Expected Result: Pytest discovers test module
  Evidence: Pytest output

  **Scenario 2: All tests pass**
  Tool: Bash (pytest)
  Preconditions: ZAI_API_KEY set
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py -v`
    2. Check exit code
    3. Check for "PASSED" or "FAILED" in output
  Expected Result: All tests pass
  Evidence: Pytest output showing passed tests

  **Scenario 3: Tests can be run without ZAI_API_KEY (mock mode)**
  Tool: Bash (pytest)
  Preconditions: No ZAI_API_KEY set
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py -v -k "not test_configure_with_valid_key"`
    2. Check exit code
    Expected Result: Tests that don't require API key pass
  Evidence: Pytest output

  **Evidence to Capture:**
  - [ ] Pytest collect output saved to .sisyphus/evidence/task-8-collect.txt
  - [ ] All tests pass output saved to .sisyphus/evidence/task-8-pass.txt
  - [ ] No key mode output saved to .sisyphus/evidence/task-8-no-key.txt

  **Commit**: YES
  - Message: `test(ai): add comprehensive tests for ZaiClient`
  - Files: `orchestrator/ai/tests/test_zai.py`

---



---

## Success Criteria

### Verification Commands

```bash
# 1. Verify ZAI SDK installable
pip install zai-sdk --dry-run 2>&1 | grep -i "Collecting zai-sdk"

# 2. Verify .env.example exists with both keys
grep -E "ZAI_API_KEY|GOOGLE_API_KEY" .env.example

# 3. Verify ZaiClient imports
python -c "from orchestrator.ai.zai import ZaiClient; print('OK')"

# 4. Verify config loads ZAI settings
python -c "from orchestrator.config import get_settings; s = get_settings(); print(hasattr(s, 'zai_api_key') and hasattr(s, 'zai_model'))"

# 5. Verify provider factory
python -c "from orchestrator.ai import get_ai_client; print(type(get_ai_client('zai')).__name__)"

# 6. Verify 5 agents use glm-5
python -c "import json; data = json.load(open('schemas/agents_config.json')); print(sum(1 for v in data['agents'].values() if v['model']=='glm-5'))"

# 7. Verify orchestrator uses factory
python -c "from orchestrator.main import app; from orchestrator.ai import get_ai_client; print('Factory OK' if 'zai' in str(app))"

# 8. Run all tests
pytest orchestrator/ai/tests/test_zai.py -v
```

### Final Checklist
- [ ] `zai-sdk` dependency installed (correct package name)
- [ ] `.env.example` created with both API key placeholders
- [ ] ZaiClient class created matching GeminiClient pattern
- [ ] Config.py updated with `zai_api_key` and `zai_model` settings
- [ ] Provider factory function created and exported
- [ ] 5 agents updated to use `glm-5` model
- [ ] Orchestrator main.py updated to use provider factory
- [ ] Comprehensive tests written and passing
- [ ] Both GOOGLE_API_KEY and ZAI_API_KEY can be set independently
- [ ] Existing 5 Gemini agents still work without changes
- [ ] No blocking calls in async context
- [ ] Import backward compatibility maintained
