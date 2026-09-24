# Security

Agent Kaizen is intended to help agents discover and build better automation **without expanding their authority by default**.

Because this repository is public, assume anything committed here is permanently public.

## Capability policy

Use **default deny + least privilege**.

An investigation does not itself authorize an agent to:

- install or connect a new external service;
- request broader OAuth scopes;
- acquire or expose credentials;
- switch from read-only to write access;
- access unrelated repositories, mailboxes, drives, databases, or accounts;
- spend money or increase API budgets;
- publish, send, deploy, merge, delete, purchase, schedule, or modify production state;
- bypass an existing human approval step.

Grant only the narrowest capability needed for an approved experiment or production workflow.

Prefer:

```text
no access
  ↓
synthetic / public data
  ↓
read-only scoped access
  ↓
sandbox write access
  ↓
production write with approval
  ↓
guardrailed autonomy
```

Do not skip stages merely because the agent or model supports them.

## Investigation vs activation

Agents may usually investigate an opportunity before deployment approval by:

- mapping the workflow;
- analysing already-authorized evidence;
- researching public information;
- designing an approach;
- writing code against fixtures/mocks;
- building a sandboxed proof of concept;
- defining tests, safety boundaries, and expected value.

Approval is required before crossing an applicable trust boundary, including:

- privileged or sensitive data access;
- new credentials/connectors/scopes;
- externally visible communication or publishing;
- financial transactions or material spend;
- destructive or hard-to-reverse actions;
- security/permission changes;
- production deployment or activation;
- actions with material legal, safety, employment, customer, or reputational consequences.

## Agent safety requirements

For automation above simple suggestion/drafting:

1. **Declare allowed tools and resources.** Avoid wildcard tool access.
2. **Separate read and write authority** where practical.
3. **Classify external actions by consequence and reversibility.**
4. **Preview consequential actions** before an approval gate.
5. **Make retries idempotent** or add deduplication.
6. **Bound loops, spend, concurrency, and rate.**
7. **Log decisions and side effects** without logging secrets or unnecessary sensitive payloads.
8. **Provide an interrupt/disable path.**
9. **Validate outputs before treating work as complete.**
10. **Test failure and recovery paths**, not only happy paths.

## Secrets

Never commit:

- API keys or access tokens;
- passwords;
- OAuth refresh tokens;
- private keys/certificates;
- cookies/session tokens;
- real `.env` files;
- credentials embedded in examples, fixtures, screenshots, prompts, logs, or test recordings.

Use placeholders and environment-variable names instead.

A lightweight repository check lives at `scripts/check-secrets.sh` and runs in GitHub Actions. It is a backstop, not a substitute for GitHub secret scanning/push protection or a dedicated secret scanner.

If a real secret is committed, treat it as compromised: revoke/rotate it first, then clean up the repository history if appropriate.

## Recommended GitHub repository settings

For this public repository, enable where available:

- secret scanning;
- push protection;
- dependency alerts;
- private vulnerability reporting;
- a ruleset for the default branch requiring pull requests and passing checks for external contributors.

The connected GitHub integration used to bootstrap this repo cannot administer those repository-level security settings, so they must be enabled in GitHub settings.

## Reporting a vulnerability

Please report security issues privately rather than opening a public issue containing exploit details, credentials, or sensitive information. Use GitHub's private vulnerability reporting feature when enabled.
