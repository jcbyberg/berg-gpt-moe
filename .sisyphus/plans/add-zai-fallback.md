# Add ZAI GLM-5 Fallback to GLM-4.7

## TL;DR

> **Quick Summary**: Implement automatic fallback mechanism when GLM-5 encounters rate limits, automatically retrying with GLM-4.7 from the same ZAI provider to ensure service continuity.
> 
> **Deliverables**:
> - Updated ZaiClient with fallback model support
> - Rate limit error detection and automatic retry logic
> - Configuration support for preferred and fallback models
> - Tests for fallback behavior
> - Updated orchestrator to handle fallback responses
> 
> **Estimated Effort**: Short (3 files modified, ~100 lines of code)
> **Parallel Execution**: NO - sequential changes for proper error handling
> **Critical Path**: Update config → Modify ZaiClient → Test fallback → Update orchestrator

---

## Context

### Original Request
GLM-5 is being severely rate-limited. System should try GLM-5 first, but automatically fallback to GLM-4.7 if GLM-5 is not available or hits rate limits.

### Interview Summary
**User Decisions**:
- **Fallback Behavior**: Automatic retry with GLM-4.7 (no user intervention)
- **Retry Policy**: 1 attempt only (try GLM-5 once, if fails fallback immediately)
- **Fallback Model**: GLM-4.7 (same ZAI provider, different model)
- **On Complete Failure**: Return error to user if GLM-4.7 also fails

### Technical Approach
- Detect ZAI rate limit errors (typically HTTP 429 or specific error codes)
- Implement single-retry logic with model fallback
- Use same provider (ZAI) but different model (glm-5 → glm-4.7)
- Preserve error context in logs for debugging
- No user notification needed - silent fallback

### Research Findings
- **ZAI Rate Limits**: GLM-5 has stricter rate limits than GLM-4.7
- **Error Patterns**: Rate limits return HTTP 429 or specific API error codes
- **Fallback Strategy**: Model-level fallback within same provider is faster than provider-level fallback

---

## Work Objectives

### Core Objective
Implement automatic fallback mechanism from GLM-5 to GLM-4.7 when rate limits are encountered, ensuring service continuity with minimal user disruption.

### Concrete Deliverables
- `orchestrator/config.py` - Add `zai_fallback_model` setting
- `orchestrator/ai/zai.py` - Add fallback logic with rate limit detection
- `orchestrator/ai/tests/test_zai.py` - Add tests for fallback behavior
- Updated logs to track fallback occurrences

### Definition of Done
- [ ] Configuration supports both `zai_model` and `zai_fallback_model` settings
- [ ] ZaiClient detects rate limit errors automatically
- [ ] ZaiClient retries with fallback model on rate limit (1 attempt)
- [ ] Tests verify fallback triggers correctly and returns valid responses
- [ ] Logs clearly indicate when fallback occurs
- [ ] Orchestrator continues normal operation with fallback responses

### Must Have
- Automatic fallback without user intervention
- Single retry attempt (GLM-5 → GLM-4.7)
- Fallback uses same ZAI provider
- Error detection for rate limits (HTTP 429 or API-specific codes)
- Preserves error context in logs
- Tests for both success path and fallback path

### Must NOT Have (Guardrails)
- **NO** fallback to Gemini 2.5 Flash (different provider)
- **NO** multiple retry attempts (only 1 retry: GLM-5 → GLM-4.7)
- **NO** user notification on fallback (silent operation)
- **NO** provider-level fallback (stay within ZAI provider)

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

**Task Structure**:
1. **RED**: Write failing test first
   - Test file: `orchestrator/ai/tests/test_zai.py`
   - Test command: `pytest orchestrator/ai/tests/test_zai.py -v -k fallback`
   - Expected: FAIL (test exists, fallback logic doesn't)
2. **GREEN**: Implement minimum code to pass
   - Command: `pytest orchestrator/ai/tests/test_zai.py -v -k fallback`
   - Expected: PASS
3. **REFACTOR**: Clean up while keeping green
   - Command: `pytest orchestrator/ai/tests/test_zai.py -v -k fallback`
   - Expected: PASS (still)

---

## Execution Strategy

### Parallel Execution Waves

> Sequential execution required for proper error handling implementation.
> Each task depends on previous completing correctly.

```
Wave 1 (Start Immediately):
└── Task 1: Add fallback_model configuration setting

Wave 2 (After Wave 1):
└── Task 2: Update ZaiClient with fallback logic

Wave 3 (After Wave 2):
└── Task 3: Write tests for fallback behavior

Wave 4 (After Wave 3):
└── Task 4: Update orchestrator to handle fallback

Critical Path: Task 1 → Task 2 → Task 3 → Task 4
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2 | None |
| 2 | 1 | 3 | None |
| 3 | 2 | 4 | None |
| 4 | 3 | None | None (final) |

---

## TODOs

> Implementation + Test = ONE Task. Never separate.
> EVERY task MUST have: Recommended Agent Profile + Parallelization info.

- [ ] 1. Add fallback_model configuration setting

  **What to do**:
  - Add `zai_fallback_model: str = "glm-4.7"` field to Settings class in `config.py`
  - Follow existing pydantic_settings pattern
  - Add validation to ensure fallback_model is a valid model string
  - Update .env.example to include ZAI_FALLBACK_MODEL placeholder

  **Must NOT do**:
  - Remove or modify existing `zai_model` field
  - Change existing Settings class structure
  - Modify Redis, LanceDB, or other settings

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Simple pydantic field addition following existing pattern
  - **Skills**: None needed for settings updates
  - **Skills Evaluated but Omitted**: All agent skills are domain-specific

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/config.py:16-67` - Settings class with zai_model field (lines 52-55)
  - `pydantic_settings` usage patterns in existing Settings class
  - `.env.example` structure for environment variable documentation

  **API/Type References** (contracts to implement against):
  - Settings class with additional string field for model configuration
  - pydantic_settings Field type for string validation

  **Test References** (testing patterns to follow):
  - Existing tests for Settings loading in `tests/` directory

  **Documentation References** (specs and requirements):
  - pydantic_settings documentation for Field usage
  - User requirement: support fallback model configuration

  **External References** (libraries and frameworks):
  - pydantic-settings library documentation

  **WHY Each Reference Matters** (explain relevance):
  - Lines 52-55 show exactly how zai_model field was added, follow same pattern
  - Need to understand pydantic Field syntax and validation options
  - Follow same comment style and type annotations

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled)**:
  - [ ] Config class has zai_fallback_model field with default "glm-4.7"
  - [ ] Settings() function loads ZAI_FALLBACK_MODEL from environment
  - [ ] .env.example includes ZAI_FALLBACK_MODEL placeholder with comment
  - [ ] pytest tests pass: `pytest tests/test_config.py -v`

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed)**:

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Config loads zai_fallback_model field**
  Tool: Bash (Python)
  Preconditions: config.py updated
  Steps:
    1. Run: `python -c "from orchestrator.config import get_settings; s = get_settings(); print(hasattr(s, 'zai_fallback_model'))"`
    2. Assert stdout is "True"
  Expected Result: zai_fallback_model field exists in Settings
  Evidence: Python output

  **Scenario 2: Config defaults to glm-4.7**
  Tool: Bash (Python)
  Preconditions: No ZAI_FALLBACK_MODEL env var set
  Steps:
    1. Run: `python -c "from orchestrator.config import get_settings; s = get_settings(); print(s.zai_fallback_model)"`
    2. Assert stdout contains "glm-4.7"
  Expected Result: Default value is glm-4.7
  Evidence: Python output

  **Scenario 3: Config loads from environment variable**
  Tool: Bash (Python)
  Preconditions: ZAI_FALLBACK_MODEL=glm-4.7 env var set
  Steps:
    1. Run: `ZAI_FALLBACK_MODEL=glm-4.7 python -c "from orchestrator.config import get_settings; s = get_settings(); print(s.zai_fallback_model)"`
    2. Assert stdout contains "glm-4.7"
  Expected Result: Environment variable overrides default
  Evidence: Python output

  **Scenario 4: .env.example includes fallback model**
  Tool: Bash (grep)
  Preconditions: .env.example updated
  Steps:
    1. Run: `grep "ZAI_FALLBACK_MODEL" .env.example`
    2. Assert grep finds the line
    3. Assert grep output contains "glm-4.7"
  Expected Result: Environment variable documented in .env.example
  Evidence: Grep output

  **Evidence to Capture**:
  - [ ] zai_fallback_model field test saved to .sisyphus/evidence/task-1-field.txt
  - [ ] Default value test saved to .sisyphus/evidence/task-1-default.txt
  - [ ] Env var test saved to .sisyphus/evidence/task-1-env.txt
  - [ ] .env.example test saved to .sisyphus/evidence/task-1-example.txt

  **Commit**: YES
  - Message: `feat(config): add zai_fallback_model setting with glm-4.7 default`
  - Files: `orchestrator/config.py`, `.env.example`

---

- [ ] 2. Update ZaiClient with fallback logic

  **What to do**:
  - Add `_fallback_model` attribute to ZaiGLMClient class
  - Modify configure() method to load fallback_model from settings
  - Detect rate limit errors (HTTP 429, specific API error codes)
  - Implement single-retry logic: if rate limit detected, retry with fallback model
  - Add logging to indicate when fallback occurs
  - Preserve error context for debugging

  **Must NOT do**:
  - Add multiple retry attempts (only 1 retry allowed)
  - Fallback to different provider (stay within ZAI)
  - Require user intervention or notification
  - Change existing method signatures or break compatibility

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `unspecified-high`
    - Reason: Complex error handling and retry logic implementation requires careful attention to API error patterns and async/await patterns
  - **Skills**: None needed for this implementation
  - **Skills Evaluated but Omitted**: No web/AI tool integration needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 3
  - **Blocked By**: Task 1 (config must have fallback_model first)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/ai/zai.py:19-31` - Lazy initialization pattern in __init__
  - `orchestrator/ai/zai.py:27-48` - Configure method pattern with safety settings
  - `orchestrator/ai/zai.py:50-91` - generate_response method with async wrapper and error handling
  - `orchestrator/ai/zai.py:93-130` - plan_mission and synthesize_results methods to modify

  **API/Type References** (contracts to implement against):
  - ZaiClient interface methods: configure(), generate_response(), plan_mission(), synthesize_results()
  - Rate limit error patterns from zai-sdk
  - Model parameter in ZAI SDK calls

  **Test References** (testing patterns to follow):
  - Existing pytest test structure in `orchestrator/ai/tests/test_zai.py`
  - Async test patterns with @pytest.mark.asyncio
  - Mock patterns for zai_sdk

  **Documentation References** (specs and requirements):
  - User requirement: automatic fallback with GLM-4.7, 1 retry attempt only
  - Existing ZaiClient implementation patterns
  - Rate limit error documentation from ZAI

  **External References** (libraries and frameworks):
  - ZAI SDK documentation on error codes and rate limits
  - Python async error handling patterns with try/except

  **WHY Each Reference Matters** (explain relevance):
  - __init__ shows how to add new class attributes with default values
  - configure() shows how settings are loaded and assigned to class attributes
  - generate_response shows existing async wrapper pattern to extend with retry logic
  - Need to understand zai_sdk error types to detect rate limits
  - Must preserve existing method signatures for backward compatibility

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled)**:
  - [ ] ZaiClient has _fallback_model attribute
  - [ ] configure() loads zai_fallback_model from settings
  - [ ] generate_response() detects rate limit and retries with fallback model
  - [ ] Only 1 retry attempt allowed
  - [ ] Fallback uses same provider (ZAI) but different model
  - [ ] pytest tests pass: `pytest orchestrator/ai/tests/test_zai.py -v -k fallback`
  - [ ] Logs indicate when fallback occurs

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed)**:

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: ZaiClient loads fallback model from config**
  Tool: Bash (Python)
  Preconditions: config.py has zai_fallback_model field
  Steps:
    1. Run: `python -c "
import asyncio
from orchestrator.ai.zai import ZaiClient
async def test():
    c = ZaiClient()
    await c.configure()
    print(f'Fallback model: {c._fallback_model}')
asyncio.run(test())
"`
    2. Assert stdout contains "glm-4.7"
  Expected Result: Client loads fallback model from settings
  Evidence: Python output

  **Scenario 2: Rate limit triggers fallback**
  Tool: Bash (Python with mock)
  Preconditions: ZaiClient updated with fallback logic
  Steps:
    1. Run: `python -c "
import asyncio
from unittest.mock import patch
from orchestrator.ai.zai import ZaiClient

async def test():
    # Mock generate_response to raise rate limit error first time
    with patch('zai_sdk.zai.ZaiClient.chat', side_effect=[Exception('Rate limit error (HTTP 429)')]):
        c = ZaiClient()
        await c.configure()
        # This should trigger fallback and retry
        try:
            result = await c.generate_response('test query')
            print(f'Success: {result}')
        except Exception as e:
            print(f'Fallback error: {e}')

asyncio.run(test())
" 2>&1 | grep -E "success:|Fallback error:"`
    2. Assert grep finds either "success:" or "Fallback error:"
  Expected Result: Client retries with fallback model on rate limit
  Evidence: Python stderr output

  **Scenario 3: Normal operation without rate limit**
  Tool: Bash (Python with mock)
  Preconditions: ZaiClient updated, no rate limit
  Steps:
    1. Run: `python -c "
import asyncio
from unittest.mock import patch
from orchestrator.ai.zai import ZaiClient

async def test():
    # Mock generate_response to succeed first time
    with patch('zai_sdk.zai.ZaiClient.chat', return_value={'choices': [{'message': {'content': 'response'}}]):
        c = ZaiClient()
        await c.configure()
        result = await c.generate_response('test query')
        print(f'Content: {result}')

asyncio.run(test())
" 2>&1 | grep "Content: response"`
    2. Assert grep finds "Content: response"
  Expected Result: Client returns response without fallback
  Evidence: Python output

  **Scenario 4: Only 1 retry attempt**
  Tool: Bash (Python with mock)
  Preconditions: ZaiClient updated with retry logic
  Steps:
    1. Run: `python -c "
import asyncio
from unittest.mock import patch, call
from orchestrator.ai.zai import ZaiClient

async def test():
    c = ZaiClient()
    await c.configure()
    
    # Track how many times generate_response is called
    call_count = [0]
    
    original_chat = None
    
    def track_calls(*args, **kwargs):
        call_count[0] += 1
        return original_chat(*args, **kwargs)
    
    # Mock to fail twice (GLM-5 rate limit, then GLM-4.7 rate limit)
    with patch('zai_sdk.zai.ZaiClient.chat', side_effect=[Exception('Rate limit 1'), Exception('Rate limit 2')]):
        c = ZaiClient()
        await c.configure()
        try:
            result = await c.generate_response('test')
        except Exception as e:
            print(f'Final error: {e}')
        
    print(f'Total calls: {call_count[0]}')

asyncio.run(test())
" 2>&1 | grep -E "Total calls:|Final error:"`
    2. Assert grep shows "Total calls: 2" (GLM-5 + 1 retry with GLM-4.7)
    3. Assert grep finds "Final error:" (second rate limit after fallback also failed)
  Expected Result: Only 1 retry attempt, then returns error
  Evidence: Python output

  **Scenario 5: Logs indicate when fallback occurs**
  Tool: Bash (Python with mock)
  Preconditions: ZaiClient updated with logging
  Steps:
    1. Run: `python -c "
import asyncio
from unittest.mock import patch
from orchestrator.ai.zai import ZaiClient
import logging

# Capture log output
log_handler = logging.StreamHandler()
logging.getLogger().addHandler(log_handler)

async def test():
    with patch('zai_sdk.zai.ZaiClient.chat', side_effect=[Exception('Rate limit (HTTP 429)')]):
        c = ZaiClient()
        await c.configure()
        result = await c.generate_response('test')
        print(f'Result: {result}')

asyncio.run(test())
" 2>&1 | grep -i "fallback\|retry\|glm-4.7" | head -5`
    2. Assert grep finds at least one mention of fallback or glm-4.7
  Expected Result: Logs clearly indicate fallback occurred
  Evidence: Python output

  **Evidence to Capture**:
  - [ ] Fallback model load test saved to .sisyphus/evidence/task-2-load.txt
  - [ ] Rate limit fallback test saved to .sisyphus/evidence/task-2-fallback.txt
  - [ ] Normal operation test saved to .sisyphus/evidence/task-2-normal.txt
  - [ ] Single retry test saved to .sisyphus/evidence/task-2-retry.txt
  - [ ] Log output test saved to .sisyphus/evidence/task-2-log.txt

  **Commit**: YES
  - Message: `feat(zai): add automatic fallback to GLM-4.7 on rate limit (single retry)`
  - Files: `orchestrator/ai/zai.py`

---

- [ ] 3. Write tests for fallback behavior

  **What to do**:
  - Add comprehensive tests for fallback logic to `test_zai.py`
  - Test normal operation (no fallback)
  - Test rate limit triggers fallback
  - Test single retry policy (no infinite loops)
  - Test fallback model usage
  - Test error handling when fallback also fails

  **Must NOT do**:
  - Test other AI providers (only ZAI fallback)
  - Test multiple retry attempts beyond 1
  - Test fallback to different providers
  - Test user notification (should be silent)

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Test implementation following existing pytest patterns
  - **Skills**: None needed for test writing
  - **Skills Evaluated but Omitted**: No web/AI tools needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 4
  - **Blocked By**: Task 2 (ZaiClient must have fallback logic first)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/ai/tests/test_zai.py:14-30` - Existing test structure (lazy initialization, configure)
  - `orchestrator/ai/tests/test_zai.py:50-91` - Existing test for generate_response
  - Mock patterns for zai_sdk in existing tests
  - pytest fixtures and parametrization patterns

  **API/Type References** (contracts to implement against):
  - ZaiClient interface: configure(), generate_response(), plan_mission(), synthesize_results()
  - Rate limit error types and detection
  - Model parameter in SDK calls

  **Test References** (testing patterns to follow):
  - pytest.mark.asyncio decorator for async tests
  - unittest.mock for mocking zai_sdk
  - Existing test file structure and naming conventions

  **Documentation References** (specs and requirements):
  - User requirement: automatic fallback with GLM-4.7, 1 retry only
  - pytest documentation for async tests and mocking
  - Test structure in existing test_zai.py

  **External References** (libraries and frameworks):
  - pytest documentation for async tests
  - unittest.mock documentation

  **WHY Each Reference Matters** (explain relevance):
  - test_zai.py shows exact patterns for async tests and mocking to follow
  - Need to understand pytest.mark.asyncio for async test methods
  - Mock patterns show how to simulate rate limit errors
  - Must follow existing test naming conventions (test_*)

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled)**:
  - [ ] Test file created with fallback tests
  - [ ] test_fallback_on_rate_limit exists
  - [ ] test_single_retry_policy exists
  - [ ] test_normal_operation_no_fallback exists
  - [ ] test_fallback_model_usage exists
  - [ ] test_fallback_also_fails exists
  - [ ] pytest passes all fallback tests: `pytest orchestrator/ai/tests/test_zai.py -v -k fallback`

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed)**:

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Pytest discovers fallback tests**
  Tool: Bash (pytest)
  Preconditions: test_zai.py updated with fallback tests
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py --collect-only 2>&1 | grep "test_.*fallback"`
    2. Assert grep finds test functions (test_fallback_on_rate_limit, etc.)
  Expected Result: Pytest discovers fallback test functions
  Evidence: Pytest output

  **Scenario 2: All fallback tests pass**
  Tool: Bash (pytest)
  Preconditions: ZaiClient updated with fallback logic
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py -v -k fallback`
    2. Check exit code
    3. Check for "PASSED" in output
  4. Check for "FAILED" in output (should be 0)
  Expected Result: All fallback tests pass
  Evidence: Pytest output showing passed tests

  **Scenario 3: Test verifies only 1 retry**
  Tool: Bash (pytest)
  Preconditions: test_zai.py has retry test
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py::test_single_retry_policy -v`
    2. Check test output for assertion of 2 calls
    3. Check no infinite loop protection
  Expected Result: Test confirms single retry policy
  Evidence: Pytest output

  **Scenario 4: Test logs fallback occurrence**
  Tool: Bash (pytest)
  Preconditions: test_zai.py has logging test
  Steps:
    1. Run: `pytest orchestrator/ai/tests/test_zai.py::test_logs_fallback_occurrence -v -s`
    2. Check output for log messages about fallback
    Expected Result: Test verifies logging of fallback
  Evidence: Pytest captured output

  **Evidence to Capture**:
  - [ ] Pytest collect output saved to .sisyphus/evidence/task-3-collect.txt
  - [ ] All tests pass output saved to .sisyphus/evidence/task-3-pass.txt
  - [ ] Single retry test output saved to .sisyphus/evidence/task-3-retry.txt
  - [ ] Log test output saved to .sisyphus/evidence/task-3-log.txt

  **Commit**: NO (part of Task 2 commit)

---

- [ ] 4. Update orchestrator to handle fallback

  **What to do**:
  - Review orchestrator/main.py to ensure it handles ZaiClient responses correctly
  - Verify that fallback responses are processed normally
  - Ensure logs from ZaiClient are visible in orchestrator logs
  - No code changes required if ZaiClient handles fallback transparently

  **Must NOT do**:
  - Add fallback logic to orchestrator (should be in ZaiClient)
  - Modify agent dispatch or mission planning
  - Add user notifications (fallback is silent)
  - Change response handling logic

  **Recommended Agent Profile**:
  > Select category + skills based on task domain. Justify each choice.
  - **Category**: `quick`
    - Reason: Verification that fallback works correctly in full system context
  - **Skills**: None needed for verification task
  - **Skills Evaluated but Omitted**: No specialized skills needed

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: None (final verification)
  - **Blocked By**: Task 3 (tests must pass first)

  **References** (CRITICAL - Be Exhaustive):

  > The executor has NO context from your interview. References are their ONLY guide.
  > Each reference must answer: "What should I look at and WHY?"

  **Pattern References** (existing code to follow):
  - `orchestrator/main.py:130` - How zai_client.plan_mission() is used
  - `orchestrator/main.py:175` - How zai_client.synthesize_results() is used
  - Response handling patterns in orchestrator
  - Logging patterns in main.py

  **API/Type References** (contracts to implement against):
  - ZaiClient return types from generate_response(), plan_mission(), synthesize_results()
  - Orchestrator response processing logic

  **Test References** (testing patterns to follow):
  - Existing orchestrator tests in `tests/test_orchestrator.py`
  - Integration test patterns

  **Documentation References** (specs and requirements):
  - User requirement: orchestrator should handle fallback responses normally
  - Existing orchestrator architecture and data flow

  **External References** (libraries and frameworks):
  - FastAPI response handling patterns
  - Logging best practices

  **WHY Each Reference Matters** (explain relevance):
  - main.py shows how ZaiClient is currently used for planning and synthesis
  - Need to verify that fallback responses are processed without errors
  - Need to ensure logs from ZaiClient flow through to system logs
  - Must understand response data structures to verify handling

  **Acceptance Criteria**:

  > **AGENT-EXECUTABLE VERIFICATION ONLY** — No human action permitted.
  > Every criterion MUST be verifiable by running a command or using a tool.
  > REPLACE all placeholders with actual values from task context.

  **If TDD (tests enabled)**:
  - [ ] Orchestrator imports ZaiClient and get_ai_client successfully
  - [ ] Orchestrator calls zai_client methods (plan_mission, synthesize_results)
  - [ ] Fallback responses are processed without errors
  - [ ] ZaiClient logs are visible in orchestrator output
  - [ ] System health endpoint shows AI functionality

  **Agent-Executed QA Scenarios (MANDATORY — per-scenario, ultra-detailed)**:

  > Write MULTIPLE named scenarios per task: happy path AND failure cases.
  > Each scenario = exact tool + steps with real commands/outputs + evidence path.

  **Scenario 1: Orchestrator handles normal ZaiClient responses**
  Tool: Bash (Python)
  Preconditions: ZaiClient updated, orchestrator unchanged
  Steps:
    1. Run: `python -c "
import asyncio
from orchestrator.main import app
from orchestrator.ai import get_ai_client

async def test():
    # Verify zai_client is available
    zai_client = get_ai_client('zai')
    print(f'ZAI client type: {type(zai_client).__name__}')
    
asyncio.run(test())
" 2>&1 | grep "ZAI client type:"
    2. Assert grep finds "ZaiClient"
  Expected Result: Orchestrator can import and use ZaiClient
  Evidence: Python output

  **Scenario 2: Orchestrator startup logs both providers**
  Tool: Bash (curl)
  Preconditions: Both API keys configured
  Steps:
    1. Run: `python orchestrator/main.py 2>&1 | grep -i "provider\|zai\|configured" | head -10`
    2. Wait for startup (5 seconds)
    3. Check grep output
  Expected Result: Logs show ZAI provider configured
  Evidence: Stderr output from startup

  **Scenario 3: System health shows AI functionality**
  Tool: Bash (curl)
  Preconditions: Services running
  Steps:
    1. Run: `curl -s http://localhost:8000/health 2>&1 | grep -i "ai_enabled"`
    2. Check response
  Expected Result: Health endpoint shows ai_enabled: true
  Evidence: JSON response

  **Scenario 4: Query endpoint works with fallback**
  Tool: Bash (curl with mock)
  Preconditions: ZaiClient has fallback, services running
  Steps:
    1. Run: `curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "test", "max_agents": 1}'`
    2. Check response
    Expected Result: Query completes (may use fallback internally)
  Evidence: JSON response

  **Evidence to Capture**:
  - [ ] Import test output saved to .sisyphus/evidence/task-4-import.txt
  - [ ] Startup logs output saved to .sisyphus/evidence/task-4-startup.txt
  - [ ] Health check output saved to .sisyphus/evidence/task-4-health.txt
  - [ ] Query endpoint output saved to .sisyphus/evidence/task-4-query.txt

  **Commit**: NO (verification-only task)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(config): add zai_fallback_model setting with glm-4.7 default` | `orchestrator/config.py`, `.env.example` | pytest tests pass |
| 2 | `feat(zai): add automatic fallback to GLM-4.7 on rate limit (single retry)` | `orchestrator/ai/zai.py` | pytest -k fallback passes |
| 3 | `test(zai): add comprehensive tests for fallback behavior` | `orchestrator/ai/tests/test_zai.py` | pytest -k fallback passes |
| 4 | (no code changes) | (verification only) | Tests pass |

---

## Success Criteria

### Verification Commands

```bash
# 1. Verify config has fallback model
python -c "from orchestrator.config import get_settings; s = get_settings(); print(hasattr(s, 'zai_fallback_model') and s.zai_fallback_model == 'glm-4.7')"

# 2. Verify fallback tests pass
pytest orchestrator/ai/tests/test_zai.py -v -k fallback

# 3. Verify orchestrator handles ZaiClient
curl http://localhost:8000/health

# 4. Run a query (should work with or without fallback)
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query": "test"}'
```

### Final Checklist

- [ ] Config supports zai_fallback_model with default glm-4.7
- [ ] .env.example documents ZAI_FALLBACK_MODEL
- [ ] ZaiClient detects rate limits (HTTP 429 or API-specific codes)
- [ ] ZaiClient retries with fallback model on rate limit (1 attempt only)
- [ ] Fallback uses same provider (ZAI), not different provider
- [ ] Logs indicate when fallback occurs
- [ ] No user notification required (silent fallback)
- [ ] Tests verify normal operation, fallback triggered, single retry, and complete failure
- [ ] Orchestrator processes ZaiClient responses correctly
- [ ] System health shows AI functionality

---

## After Plan Completion: Cleanup & Handoff

**When your plan is complete and saved:**

### 1. Delete Draft File (MANDATORY)

The draft served its purpose. Clean up:
```bash
rm .sisyphus/drafts/add-zai-fallback.md
```

### 2. Guide User to Start Execution

```
Plan saved to: .sisyphus/plans/add-zai-fallback.md

To begin execution, run:
  /start-work

This will:
1. Register fallback plan as your active boulder
2. Track progress across sessions
3. Enable automatic continuation if interrupted
```
