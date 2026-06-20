---
name: example-api-testing
description: Write and run API integration tests with pytest, covering authentication, rate limiting, error handling, and response validation
domain: development
subdomain: testing
tags:
- api
- testing
- pytest
- integration
- rest
version: '1.0'
author: your-name
license: Apache-2.0
---

# Example API Testing Skill

## Overview

This is an example skill showing the standard SKILL.md format. Each skill has YAML frontmatter with metadata, followed by markdown content describing the methodology.

The Skill Lifecycle tools read the frontmatter to auto-categorize skills and generate trigger keywords.

## When to Use

- When building or maintaining API integration tests
- When validating REST API responses against a contract
- When setting up automated testing in CI/CD pipelines

## Prerequisites

- Python 3.9+ with pytest and requests libraries
- API endpoint accessible from the test environment
- Authentication credentials for protected endpoints

## Steps

1. **Define test fixtures** — Set up authentication, base URL, and shared test data using pytest fixtures.

2. **Write contract tests** — Validate response status codes, headers, and JSON schema against the API specification.

3. **Test error paths** — Verify proper error responses for invalid input, missing auth, rate limiting, and server errors.

4. **Add integration tests** — Test multi-step workflows (create → read → update → delete) with real API calls.

5. **Run in CI** — Configure pytest in your CI pipeline with proper environment variables and test isolation.

## Lessons Learned

### [2025-01-10] Flaky tests due to rate limiting
**Problem:** API tests fail intermittently when run in parallel due to rate limit (429) responses
**Solution:** Add exponential backoff retry decorator and run rate-limit-sensitive tests sequentially with pytest-ordering

### [2025-02-03] Auth token expiry mid-suite
**Problem:** Long test suites fail halfway through when the OAuth token expires (1-hour lifetime)
**Solution:** Use a session-scoped fixture that refreshes the token if remaining lifetime < 5 minutes

## Deprecated Approaches

### [2025-03-15] DEPRECATED: Using unittest.mock for API responses
**Was:** Mocking HTTP responses with unittest.mock.patch
**Use instead:** Use pytest-httpserver or responses library — they catch serialization issues that mocks hide
