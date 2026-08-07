# Enterprise Delivery Management System

## Estimation, Architecture, and Delivery Roadmap

**Prepared for:** Shafique Departmental Store ERP  
**Existing system:** VB6 + SQL Server 2008 + FastAPI/Jinja2/Bootstrap  
**Estimate class:** ROM (rough order of magnitude), suitable for budgeting and phased approval  
**Accuracy:** -20% / +30% until Phase 0 schema and workflow discovery is complete

---

## 1. Executive decision

The requested master prompt describes a logistics platform, rider application, real-time telemetry system, proof-of-delivery platform, reporting suite, fleet system, and AI product. It is not one normal ERP screen and should not be implemented as a single release.

Recommended delivery:

1. **Operational MVP:** automatic invoice detection, dispatching, rider workflow, GPS/photo/signature/OTP proof, customer tracking, dashboard, and core reports.
2. **Enterprise release:** live tracking, offline sync, route optimization, geofences, fleet/COD/attendance operations, high availability, and comprehensive testing.
3. **Advanced release:** AI predictions, fraud detection, traffic/weather intelligence, and advanced safety automation.

| Release | Effort | Calendar duration | Recommended team |
|---|---:|---:|---:|
| Operational MVP | 2,900–3,800 hours | 5–7 months | 5–6 people |
| Enterprise production system, excluding AI | 5,490–7,490 hours total | 9–12 months | 7–8 people |
| Complete master-prompt scope, including advanced AI | 6,390–8,890 hours total | 12–16 months | 8–10 people |

These are total person-hours, not elapsed working hours. Adding developers does not reduce the duration linearly because ERP discovery, database design, mobile foundations, integrations, UAT, and store deployment have sequential dependencies.

---

## 2. What the existing system already provides

The implementation must extend the current repository rather than generate a separate replacement ERP.

### Reuse directly

- FastAPI application and `/api/v1` OpenAPI structure
- JWT access/refresh authentication and session revocation
- SQL Server-backed users, roles, granular permissions, and audit logs
- Existing `API → service → repository → SQL Server` layering
- Separate authentication and legacy business database connections
- Bootstrap 5/Jinja2 administration shell and responsive page conventions
- Shared browser API client, date/time formatting, money formatting, and permission-aware navigation
- SMTP email and WhatsApp Cloud API foundations
- Customer mobile/address sources, including `CUST_SMS`
- ReportLab PDF generation patterns
- Cloudflare HTTPS tunnel and Windows service deployment scripts
- Existing scheduler pattern for low-volume periodic work

### Reuse after extension

- Audit logging: extend with delivery event types and immutable operational history
- User accounts: add rider profile/device records linked to existing auth user IDs
- WhatsApp: add approved delivery template messages and delivery-event orchestration
- Admin dashboard: reuse layout and chart conventions, not the sales queries
- Mobile web conventions: useful for prototypes, but not a substitute for the required Flutter rider app
- Deployment scripts: suitable for pilot operation, but not sufficient for enterprise high availability

### Net-new capabilities

- Delivery domain schema and state machine
- Invoice-to-delivery integration
- Rider and dispatcher APIs
- Flutter Android application
- WebSocket/SSE real-time event layer
- High-frequency GPS ingestion and retention
- Maps, geocoding, routing, ETA, geofences, and route replay
- Offline mobile queue and conflict-safe synchronization
- Photo/signature/object storage and proof-of-delivery documents
- OTP service and abuse controls
- Push notifications and true SMS provider integration
- Customer tracking portal
- Route optimization and traffic integration
- Fleet, shifts, attendance, COD settlement, fuel, leave, safety alerts
- Automated API, integration, mobile, end-to-end, security, and load testing
- Production observability, queue workers, retries, dead-letter handling, and disaster recovery

The existing repository provides approximately **30–40% of the web platform foundation**, but only about **10–15% of the complete requested logistics product**.

---

## 3. Confirmed legacy constraints

- VB6 owns invoice creation; the Python application currently does not write `FIN_INV_M` or `FIN_INV_D`.
- Existing sales reads use `V_FIN_SALE_DISC_NEW2` and join invoice master/detail through `SERIAL_NO`.
- `DOC_DATE_T` is the transaction timestamp; `DOC_DATE` has different accounting-date semantics.
- The repository does not confirm the full `FIN_INV_M` schema, the invoice customer key, or exactly when an invoice becomes final.
- Customer contact data is fragmented across invoice data, `CUST_SMS`, `GL0005`, and other legacy records.
- SQL Server 2008 compatibility rules apply; modern T-SQL features cannot be assumed.
- ERP and ARP deployments have demonstrated business-schema drift.
- Existing database backup/restore synchronization is not row-level replication and cannot carry live tracking.
- The current Windows single-process deployment and in-process scheduler are unsuitable for hundreds of riders sending GPS every five seconds.

These constraints are why Phase 0 is mandatory.

---

## 4. Recommended target architecture

```text
VB6 ERP
  └─ saves invoice in existing nsds2626 database
       └─ read-only invoice detector with watermark and idempotency
            └─ Delivery database (new, isolated operational schema/database)
                 ├─ FastAPI delivery APIs
                 ├─ Dispatcher/admin web dashboard
                 ├─ Flutter rider application
                 ├─ Public customer tracking page
                 ├─ Real-time event gateway
                 ├─ Background job workers and retry queues
                 ├─ Object storage for photos/signatures/PDFs
                 └─ Map, SMS, WhatsApp, email, push, traffic, and weather providers
```

### Database placement

Create a dedicated delivery database, for example `NSDS2626_DELIVERY`.

Do not place high-volume GPS, proof files, routes, or delivery workflow data in:

- `NSDS2626_AUTH`, which should remain an identity/security database; or
- existing VB6 invoice tables, which should remain legacy-owned.

Store only source references such as business database/site code, `SERIAL_NO`, `INV_ID`, and a source fingerprint. Avoid cross-database foreign keys to legacy ERP objects.

### Invoice detection

Recommended sequence:

1. Discover the actual invoice columns, keys, triggers, indexes, and save/post behavior.
2. Build an ERP invoice projection/view containing only required delivery fields.
3. Poll incrementally by a reliable watermark and stable source key.
4. Use a unique constraint on `(SourceSite, SourceSerialNo)` to guarantee idempotency.
5. Create an order only when trimmed `customer_mobileno` is non-empty and the invoice meets the confirmed finalization rule.
6. Reconcile changed/cancelled invoices safely and log every decision.

A trigger directly on `FIN_INV_M` is not the default recommendation because it couples VB6 invoice transactions to the delivery platform. Use one only if discovery proves that no reliable watermark/finalization signal exists and DBA testing confirms negligible risk.

### Real-time and jobs

- WebSocket or SSE for dispatcher dashboards and order events
- Separate authenticated GPS ingestion endpoint optimized for batched mobile points
- Redis-compatible cache/broker and durable worker queue for notifications, geocoding, route work, media processing, and retries
- Database remains the system of record; real-time messages are delivery optimizations, not authoritative state
- GPS writes should be partitioned/archived by retention policy

### Maps and routing

- Default cost-controlled option: OpenStreetMap tiles through a compliant hosted provider plus a routing engine/provider
- Optional Google Maps mode for traffic, geocoding quality, navigation, Street View, and satellite imagery
- Keep map/routing providers behind adapter interfaces to avoid provider lock-in

---

## 5. Effort by implementation phase

| Phase | Scope | Effort |
|---|---|---:|
| 0. Discovery and validated design | Live schema inventory, VB6 invoice-save walkthrough, customer-key mapping, rider/dispatcher interviews, UX flows, non-functional targets, provider decisions, acceptance backlog | 160–240 h |
| 1. Delivery platform foundation | Delivery DB and migrations, RBAC seeds, settings, order/rider/device/location models, state machine, audit events, idempotent invoice detector, admin CRUD foundation, CI baseline | 480–650 h |
| 2. Core dispatch web system | Dashboard KPIs, order grid/search/filters, manual/automatic assignment, rider workload/area logic, status workflow, failed/return/cancel flows, settings, core reports, exports | 900–1,200 h |
| 3. Rider app and proof of delivery | Flutter login, assignments, accept/reject, route/customer actions, delivered workflow, GPS metadata, OTP, QR/barcode, photo/signature, failed-delivery proof, secure uploads, initial offline queue | 900–1,200 h |
| 4. Live tracking and maps | GPS ingestion, WebSocket/SSE, rider presence, live map, route line, distance/ETA, replay/timeline/stops/speed, retention, battery/network/device alerts, load optimization | 700–1,000 h |
| 5. Routing, geofences, and communications | Multi-stop optimization, priorities, geofences, near-arrival alerts, email/WhatsApp/SMS/push orchestration, customer tracking, rating/feedback, retries and delivery receipts | 650–900 h |
| 6. Enterprise operations and analytics | Attendance, check-in/out, shifts, leave, vehicle/fuel, COD/cash settlement, rider performance, heat maps, scheduled reports, PDF proof, management analytics | 800–1,100 h |
| 7. Production hardening and rollout | Automated tests, E2E mobile tests, performance tests, security review, rate limits, observability, backups/DR, high availability, UAT, pilot, training, staged rollout | 900–1,200 h |
| 8. Advanced intelligence | Delay/time prediction, fraud anomaly detection, AI-assisted routing, weather/traffic risk, device-loss patterns, calibrated models, monitoring and retraining workflow | 900–1,400 h |
| **Total complete scope** | Phases 0–8 | **6,390–8,890 h** |

Phase effort already includes engineering, review, normal defect correction, technical documentation, and proportionate project/architecture effort. It does not include major hardware procurement or third-party usage fees.

---

## 6. Release contents

### Release A — Operational MVP

Target: 5–7 months, 2,900–3,800 hours.

Included:

- automatic delivery creation from eligible invoices
- duplicate prevention and reconciliation report
- delivery dashboard and complete searchable grid
- manual assignment plus nearest/least-busy/area rule foundation
- dispatcher, manager, rider, admin, and read-only permissions
- rider Flutter app for assignments and status changes
- GPS, timestamp, device, photo, signature, OTP, QR/barcode, and remarks capture
- mandatory failed-delivery reason and photo
- current order map, customer marker, navigation hand-off, distance, and basic ETA
- customer invoice/mobile tracking with privacy controls
- email/WhatsApp notifications and push foundation
- core delivery, rider, failed/cancelled, area, customer, and time reports
- audit trail, rate limiting, secure uploads, backups, test suite, pilot deployment

Deferred:

- sophisticated multi-stop traffic optimization
- complete offline-first operation
- full fleet/COD/fuel/leave/shift modules
- historical heat maps and advanced telemetry analytics
- AI predictions and fraud detection

### Release B — Enterprise production

Target: 9–12 months total, 5,490–7,490 hours total.

Adds:

- robust real-time rider map at target scale
- route replay, stop/speed analysis, alerts, and configurable retention
- offline-first app synchronization and conflict handling
- geofences and near-arrival automation
- production SMS, WhatsApp templates, push, retries, and channel receipts
- multi-stop route optimization and configurable provider adapters
- attendance, shifts, leave, vehicles, fuel, COD, cash settlement, and SOS
- comprehensive scheduled analytics, PDF/Excel exports, and management reports
- high availability, queue workers, observability, disaster recovery exercises
- performance/security testing and controlled rollout

### Release C — Advanced/AI

Target: 12–16 months total, 6,390–8,890 hours total.

Adds the AI, weather, traffic, fraud, predictive ETA/delay, and advanced safety capabilities. These features require sufficient clean production history; they cannot be credibly trained during the first implementation sprint.

---

## 7. Recommended delivery team

| Role | MVP allocation | Enterprise allocation |
|---|---:|---:|
| Product owner/business analyst | 0.5–1.0 | 1.0 |
| Solution architect/technical lead | 0.5–1.0 | 1.0 |
| FastAPI/backend engineers | 2 | 2–3 |
| Web frontend engineer | 1 | 1–2 |
| Flutter engineer | 1–2 | 2 |
| QA automation engineer | 1 | 1–2 |
| DevOps/SRE | 0.25–0.5 | 0.5–1 |
| UI/UX designer | 0.25–0.5 | 0.5 |
| GIS/data/ML specialist | as needed | 0.5–1 during relevant phases |

At least one team member must have practical access to the VB6 invoice workflow and production-like SQL Server schema. Without that access, invoice integration remains an assumption rather than a deliverable.

---

## 8. Budget model

Use:

```text
Engineering budget = estimated person-hours × agreed blended hourly rate
Contingency reserve = 15% after Phase 0, or 25% before Phase 0
Third-party and infrastructure costs are separate
```

### Example budgets in USD

| Scope | At $25/hour | At $40/hour | At $60/hour |
|---|---:|---:|---:|
| Operational MVP, 2,900–3,800 h | $72,500–$95,000 | $116,000–$152,000 | $174,000–$228,000 |
| Enterprise, 5,490–7,490 h | $137,250–$187,250 | $219,600–$299,600 | $329,400–$449,400 |
| Complete with AI, 6,390–8,890 h | $159,750–$222,250 | $255,600–$355,600 | $383,400–$533,400 |

These examples exclude contingency, taxes, travel, devices, messaging/map consumption, app-store accounts, and cloud/on-premise hardware. For PKR budgeting, multiply the person-hours by the agreed PKR blended hourly rate instead of relying on a changing exchange rate.

### Separate recurring budget lines

- map tiles, geocoding, routing, traffic, Street View, and satellite usage
- SMS messages and WhatsApp conversation/template charges
- email provider and push-notification support services
- object storage, backup storage, and media egress
- application servers, queue/cache, monitoring, log retention, and database capacity
- Android/iOS store accounts, code signing, and managed-device services
- SSL/domain/WAF services not covered by the existing Cloudflare plan
- support/on-call capacity and periodic security testing

Actual provider costs require expected daily deliveries, rider count, GPS retention, photo size, message volume, and map usage.

---

## 9. Proposed delivery data model

Minimum bounded contexts and tables:

### Core

- `DeliveryOrders`
- `DeliveryOrderItems` when item-level proof is required
- `DeliveryStatusHistory`
- `DeliveryAssignments`
- `DeliveryRiders`
- `DeliveryDevices`
- `DeliverySettings`
- `DeliveryAuditEvents`

### Location and routing

- `DeliveryLocations`
- `RiderLocationPoints`
- `DeliveryRoutes`
- `DeliveryRouteStops`
- `DeliveryRoutePoints` only when provider geometry must be retained
- `DeliveryGeofences`
- `DeliveryGeofenceEvents`

### Proof and communication

- `DeliveryProof`
- `DeliveryProofFiles` containing object-storage metadata, not large database blobs
- `DeliveryOtps` with hashes, expiry, attempts, and no plaintext retention
- `DeliveryNotifications`
- `DeliveryNotificationAttempts`
- `CustomerTrackingTokens`
- `DeliveryFeedback`

### Operations

- `RiderAttendance`
- `RiderShifts`
- `RiderLeave`
- `DeliveryVehicles`
- `VehicleAssignments`
- `FuelExpenses`
- `CashCollections`
- `CodSettlements`
- `RiderAlerts`

All workflow tables need UTC timestamps, actor/source, soft-delete policy where appropriate, row-version/concurrency control, targeted indexes, and explicit retention rules.

---

## 10. API and screen inventory

### API groups

- `/api/v1/delivery/orders`
- `/api/v1/delivery/assignments`
- `/api/v1/delivery/riders`
- `/api/v1/delivery/devices`
- `/api/v1/delivery/tracking`
- `/api/v1/delivery/routes`
- `/api/v1/delivery/proof`
- `/api/v1/delivery/notifications`
- `/api/v1/delivery/reports`
- `/api/v1/delivery/settings`
- `/api/v1/delivery/realtime`
- `/api/v1/public/delivery-tracking`
- `/api/v1/mobile/delivery/*`

### Web screens

- command-center dashboard
- orders grid and order detail/timeline
- manual/automatic assignment board
- live rider map
- rider/vehicle/device management
- route planning and replay
- proof-of-delivery viewer
- failed/cancelled/returned work queues
- notifications and retry monitor
- settings and provider configuration
- reports and scheduled exports
- customer tracking page

### Rider app screens

- login/device registration
- shift check-in/out
- assignment inbox
- route and stop list
- delivery detail/customer contact
- accept/reject/start/arrive
- delivered confirmation workflow
- failed/returned workflow
- photo/signature/QR/barcode/OTP capture
- offline queue/synchronization status
- SOS, alerts, history, and profile

---

## 11. Non-functional acceptance targets

Final values must be approved in Phase 0. Estimation assumes:

- 100–300 concurrent riders initially
- thousands, not millions, of deliveries per day
- nominal GPS interval of five seconds while actively moving; adaptive throttling when idle/backgrounded
- dashboard status propagation within five seconds under normal conditions
- idempotent delivery creation and mobile synchronization
- no lost confirmed proof/status event after API acknowledgement
- 99.5% initial service availability, with a path to 99.9%
- encrypted internet traffic and protected secrets
- least-privilege RBAC and auditable administrative actions
- configurable GPS, media, notification, and audit retention
- tested restore procedure and documented recovery objectives

Higher rider counts, multi-region deployment, 99.99% availability, or permanent five-second telemetry retention will increase infrastructure and engineering effort.

---

## 12. Major risks and controls

| Risk | Impact | Required control |
|---|---|---|
| Unknown `FIN_INV_M.customer_mobileno` and customer-key behavior | High | Phase 0 live schema inventory and VB6 save walkthrough |
| Duplicate/partial deliveries during invoice edits | High | Confirm finalization rule, idempotency key, reconciliation worker |
| Trigger slows or breaks VB6 invoicing | High | Prefer decoupled detector; load-test any trigger |
| Poor/unstructured customer addresses | High | Address normalization, map correction UI, stored coordinates |
| SQL Server 2008 limitations | Medium–High | Compatible SQL, separate delivery schema/database, tested indexes |
| Five-second GPS write volume | High | Batch ingestion, adaptive sampling, partition/archive policy |
| Current single Windows process fails | High | Separate workers, health checks, service supervision, HA plan |
| Offline rider actions conflict | High | Client operation IDs, server state machine, conflict policy |
| Photos/signatures expose customer data | High | Object ACLs, signed URLs, validation, retention and access audit |
| OTP abuse or bypass | High | Hashes, expiry, attempt limits, rate limits, override audit |
| Notification provider outages | Medium | Queue, retry/backoff, dead-letter and operator replay |
| ARP/ERP schema differences | Medium–High | Site adapters and per-site integration validation |
| Scope expansion from bonus/AI list | High | Release gates and change control |

---

## 13. Phase 0 fixed deliverables

Phase 0 should be approved first as a 160–240 hour engagement. It produces:

1. Verified `FIN_INV_M`, `FIN_INV_D`, related view, trigger, index, and key inventory.
2. Documented VB6 invoice create/edit/cancel/post transaction sequence.
3. Confirmed meaning and quality profile of `customer_mobileno`.
4. Customer name/address/payment/amount source mapping.
5. Measured invoice and anticipated GPS volumes.
6. Approved delivery state machine and exception rules.
7. UX wireflows for dispatcher, rider, manager, and customer.
8. Provider decisions for maps, routing, SMS, WhatsApp, push, and storage.
9. Production topology and security model.
10. Prioritized backlog with acceptance criteria.
11. Updated estimate with target accuracy of approximately ±15%.

Do not begin broad code generation before these points are validated.

---

## 14. Definition of “complete”

A phase is complete only when:

- every included screen is connected to implemented APIs;
- every state transition enforces the approved server-side state machine;
- invoice synchronization is idempotent and reconcilable;
- permissions are seeded and tested;
- mobile offline/retry behavior meets that phase’s scope;
- proof files and OTPs follow security and retention rules;
- automated tests pass at agreed coverage and critical-path levels;
- performance tests meet approved rider/order volumes;
- deployment, rollback, backup, restore, monitoring, and support documentation exist;
- UAT acceptance is signed by operations;
- no unresolved critical or high-severity security defects remain.

This definition is more reliable than promising that “every button works” without testable acceptance criteria.

---

## 15. Recommended authorization

Approve **Phase 0 only**, then re-baseline cost and schedule before committing to the MVP. The safest modernization path keeps VB6 invoice entry unchanged, reads eligible invoices without blocking the ERP transaction, and stores all delivery operations in an isolated delivery database.
