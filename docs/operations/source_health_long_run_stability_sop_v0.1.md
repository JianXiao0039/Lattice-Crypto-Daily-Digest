# Source Health Long-Run Stability SOP v0.1

Status: `source_health_long_run_policy_ready`.

Run the source-health probe manually and conservatively:

```powershell
python scripts\probe_source_health.py --low-load
```

Long-run stability means that failures are classified honestly and the radar degrades visibly. It does not mean every source must be green.

Allowed:

- low request rate;
- low-load mode;
- conservative timeouts;
- official APIs;
- honoring `Retry-After`;
- cache use when already supported;
- source-starved reporting;
- manual retry later.

Forbidden:

- proxy rotation to bypass rate limits;
- fake User-Agent rotation;
- CAPTCHA bypass;
- disabling SSL verification as a production default;
- hidden browser automation;
- ignoring robots or source terms;
- aggressive repeated retries;
- background retry loops.

When a source materially fails, generated Daily/Weekly/Monthly output must not claim that no relevant papers exist solely because the source failed.
