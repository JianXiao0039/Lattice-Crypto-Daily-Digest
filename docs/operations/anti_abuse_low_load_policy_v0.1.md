# Anti-Abuse and Low-Load Policy v0.1

## Principle

Reliability must improve through conservative, respectful source use, not through bypassing source restrictions.

## Allowed

- low request rate;
- fewer query groups per run;
- official APIs;
- caching and conditional requests when supported;
- backoff with jitter;
- honoring HTTP 429 and `Retry-After`;
- source probing separate from full ingestion;
- source-starved reporting;
- manual retry later.

## Forbidden

- proxy rotation to evade rate limits;
- fake User-Agent rotation;
- CAPTCHA solving or bypass;
- disabling SSL verification as a default fix;
- hidden browser automation to bypass protections;
- ignoring robots or source terms;
- aggressive repeated retries;
- hiding traffic identity.

## Operator Requirement

Every operator must report degraded source health honestly. A source failure is not evidence that no relevant papers exist.
