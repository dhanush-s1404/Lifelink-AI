# Production Hardening

Checklist applied before shipping to production (final milestone).

- [ ] Secrets moved to a secret manager; `.env` never committed.
- [ ] Vault master keys managed by KMS, not env vars.
- [ ] HTTPS terminated at the edge; HSTS enabled.
- [ ] CORS restricted to the real frontend origin.
- [ ] Rate limiting enabled at API + edge.
- [ ] File upload limits and malware-scanning hook in place.
- [ ] Backups: automated PostgreSQL + object storage backups, tested restore.
- [ ] Read-only replicas / failover strategy documented.
- [ ] Structured logs shipped to a central sink; Prometheus/Grafana dashboards live.
- [x] Database migrations run as a separate step, not during app boot.
- [ ] Minimal image sizes, distroless where practical; non-root containers.
- [ ] Dependency vulnerability scanning in CI.
