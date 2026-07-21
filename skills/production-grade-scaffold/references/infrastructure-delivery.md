# Infrastructure & Delivery Reference

## Containers
- Multi-stage builds: compile/build in one stage, discard it, ship a minimal or distroless runtime image.
- Run as non-root; order Dockerfile `COPY` steps dependency-manifest-first (e.g. `package.json` before source) for layer-cache efficiency; maintain a `.dockerignore`.
- Pin image references to a digest, never a mutable tag like `latest`.
- Hard resource limits (memory + pid via cgroups) so one runaway container can't cascade into a host-level OOM.
- Persistent state (databases, queues) goes in named volumes, never bind-mounted into the writable container layer - copy-on-write overhead there kills performance. Runtime secrets via tmpfs.

## CI pipeline (language-agnostic stage template)
```
lint -> unit test -> SAST -> integration test (ephemeral containers/Testcontainers)
     -> contract test -> build + sign artifact (SBOM, Cosign, SLSA provenance) -> push to registry
```
Treat the built artifact as immutable once signed - promote that same artifact through environments rather than rebuilding per environment, so what's tested is exactly what ships.

## Deployment strategy
- **Rolling** - default, lowest cost, acceptable rollback speed for most services.
- **Blue-Green** - instant rollback, ~2x infrastructure cost during the swap window; use for services where even a rolling-restart's brief mixed-version window is unacceptable.
- **Canary** - best blast-radius control; requires automated, metric-driven analysis (error rate, latency) to gate the rollout. Best fit for high-traffic or high-risk-of-regression services.
- Feature flags decouple deploy from release. Classify flags as short-lived release flags (must be deleted once fully rolled out - flag debt is real debt) versus long-lived operational/kill-switch flags. Evaluate flags with a local/in-process SDK server-side to avoid a network call per request.

## GitOps
- Pull-based reconciliation (ArgoCD/Flux-style controllers) is preferable to push-based "CI applies directly to the cluster" - no cluster credentials need to leave the cluster, and drift is continuously detected and self-healed rather than only caught at the next deploy.
- Repository layout: directory-per-environment (a shared base plus environment-specific overlays), not branch-per-environment - branches drift and merge-conflict in ways overlay directories don't.

## Observability (three pillars)
- **Logs** - structured JSON, including `trace_id`/`span_id` correlation fields so a single request can be followed across services.
- **Metrics** - low-cardinality labels only; never put a user ID or UUID in a metric label (cardinality explosion breaks most metrics backends).
- **Traces** - distributed tracing via OpenTelemetry with W3C `traceparent` propagation across service boundaries.

## Reliability engineering
- Define SLIs (good events / total events) per user-facing capability, and SLOs intentionally tighter than any external SLA commitment, so there's margin before a customer-visible breach.
- Error budgets gate release velocity: burn the budget fast, slow down risky releases; have budget to spare, ship faster.
- Alert on **symptom-based SLO burn-rate** (multi-window, multi-burn-rate alerting) rather than raw infrastructure thresholds like CPU/RAM - infra-threshold alerting is a leading cause of alert fatigue because it fires on things that don't actually affect users.

## Infrastructure as Code
- Keep declarative provisioning (Terraform/Pulumi) and configuration management (Ansible/Kubernetes manifests) as separate toolchains - blending them makes both harder to reason about.
- Remote state, encrypted at rest, with locking to prevent concurrent-apply corruption.
- Version infrastructure modules via git tags, not floating branches.
- Static analysis (Checkov/TFLint or equivalent) gates CI; run integration tests against sandboxed infra (Terratest or equivalent), never against shared/live infrastructure.
- No manual console/CLI changes to live infrastructure - the GitOps controller is the sole write path; run scheduled drift detection with auto-reconciliation.

## Minimum bar before calling infrastructure "production grade"
1. CI enforces the full stage pipeline above and blocks merge on any stage failure.
2. Every deployed artifact is signed and traceable back to the commit and pipeline run that produced it.
3. Logs, metrics, and traces are all wired up before first production launch, not added after the first incident.
4. Alerts are defined against SLO burn-rate for at least the top user-facing capabilities.
5. No infrastructure change reaches production by a manual console click.
