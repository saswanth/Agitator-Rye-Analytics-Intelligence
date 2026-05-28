# Agitator Rye — System Architecture & Workflows

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI["React Frontend<br/>Port 5173"]
    end

    subgraph "API Gateway"
        GW["FastAPI Backend<br/>Port 8000"]
        WS["WebSocket<br/>Handler"]
        REST["REST<br/>Endpoints"]
    end

    subgraph "Agent Orchestration Layer"
        ORCH["LangChain<br/>Orchestrator"]
        A1["🔍 Text-to-SQL<br/>Agent"]
        A2["🔬 Root Cause<br/>Agent"]
        A3["💹 Financial<br/>Agent"]
        A4["⚙️ Pipeline<br/>Agent"]
        A5["💡 Insight<br/>Agent"]
    end

    subgraph "Intelligence Layer"
        LLM["Sarvam AI LLM<br/>api.sarvam.ai/v1"]
        LS["LangSmith<br/>Tracing"]
    end

    subgraph "Data Layer"
        DB[("SQLite DB<br/>SQLAlchemy")]
        CACHE["In-Memory<br/>Cache"]
        PANDAS["Pandas<br/>DataFrames"]
    end

    UI -->|"REST/WS"| GW
    GW --> WS
    GW --> REST
    WS --> ORCH
    REST --> ORCH
    ORCH --> A1
    ORCH --> A2
    ORCH --> A3
    ORCH --> A4
    ORCH --> A5
    A1 --> LLM
    A2 --> LLM
    A3 --> LLM
    A4 --> LLM
    A5 --> LLM
    LLM --> LS
    A1 --> DB
    A2 --> DB
    A3 --> DB
    A4 --> DB
    A5 --> DB
    DB --> CACHE
    DB --> PANDAS
```

---

## 2. Workflow 1: Conversational Business Intelligence (Text-to-SQL)

```mermaid
sequenceDiagram
    participant U as User
    participant UI as React UI
    participant WS as WebSocket
    participant A as Text-SQL Agent
    participant LLM as Sarvam AI
    participant DB as SQLite

    U->>UI: Types natural language question
    UI->>WS: Send {message, agent: "bi"}
    WS->>A: Dispatch to Text-SQL Agent

    loop SQL Generation & Validation (max 3 retries)
        A->>LLM: Prompt: "Convert to SQL given schema..."
        LLM-->>A: Generated SQL query
        A->>DB: Execute SQL
        alt SQL Error
            DB-->>A: Error message
            A->>LLM: "Fix this SQL error: ..."
            LLM-->>A: Corrected SQL
        else Success
            DB-->>A: Result rows
        end
    end

    A->>LLM: "Interpret these results in plain English"
    LLM-->>A: Natural language answer (streamed)
    A->>A: Determine best chart type for data
    A-->>WS: Stream tokens + final chart spec
    WS-->>UI: Progressive tokens → final response
    UI->>U: Renders answer text + interactive chart
```

---

## 3. Workflow 2: Automated Root Cause Analysis

```mermaid
flowchart TD
    START([KPI Anomaly Detected]) --> ALERT[Alert Triggered\nvia Dashboard Monitor]
    ALERT --> DISPATCH[Dispatch RCA Agent]

    DISPATCH --> COLLECT[Collect Baseline Metrics\nlast 30 days]

    COLLECT --> SLICE{Dimension Slicer\nLoop}

    SLICE --> D1[Slice by Region]
    SLICE --> D2[Slice by Product Category]
    SLICE --> D3[Slice by Channel]
    SLICE --> D4[Slice by Customer Segment]
    SLICE --> D5[Slice by Device Type]
    SLICE --> D6[Slice by Time-of-Day]

    D1 & D2 & D3 & D4 & D5 & D6 --> SCORE[Anomaly Scoring\nZ-score + IQR per slice]

    SCORE --> RANK[Rank Slices by\nContribution to Anomaly]

    RANK --> LLM_HYPO[Sarvam AI:\nGenerate Hypotheses\nfor Top 3 Slices]

    LLM_HYPO --> CORR[Correlation Check\nwith Related Metrics]

    CORR --> REPORT[Structured RCA Report\n• Root cause\n• Evidence\n• Confidence %\n• Recommended actions]

    REPORT --> UI_RENDER[Render in RCA Dashboard\nwith Supporting Charts]
```

---

## 4. Workflow 3: Advanced Financial & Investment Analysis

```mermaid
flowchart LR
    subgraph "Data Sources"
        S1[financial_data table\nP&L 60 months]
        S2[daily_metrics table\nRevenue time series]
        S3[sales_transactions\nProduct-level revenue]
        S4[Simulated Market Feed\nBenchmark indices]
    end

    subgraph "Financial Agent Pipeline"
        AGG[Data Aggregator\nPandas merge + resample]
        CLEAN[Data Validator\nNull fill, currency norm]
        RATIOS[Financial Ratios\nGross/Net margins\nROIC, Current Ratio]
        FORECAST[Time-Series Forecast\nARIMA decomposition\n3 scenarios]
        BENCH[Benchmarking\nvs. Industry median]
    end

    subgraph "LLM Analysis"
        NARRATE[Sarvam AI Narration\nExecutive summary]
        RISKS[Risk Identification\nFlag outliers]
    end

    subgraph "Output"
        RPT[Financial Report\nMulti-section JSON]
        VIZ[Chart Specs\nLine/Bar/Waterfall]
    end

    S1 & S2 & S3 & S4 --> AGG
    AGG --> CLEAN --> RATIOS --> FORECAST --> BENCH
    BENCH --> NARRATE --> RISKS
    RISKS --> RPT
    RATIOS & FORECAST --> VIZ
    RPT & VIZ --> UI([Financial Dashboard])
```

---

## 5. Workflow 4: Dynamic Data Cleaning & Pipeline Management

```mermaid
stateDiagram-v2
    [*] --> Ingest: Raw data arrives

    Ingest --> SchemaCheck: Validate column types

    SchemaCheck --> DriftDetected: Schema change found
    SchemaCheck --> QualityCheck: Schema OK

    DriftDetected --> AlertLog: Log schema drift event
    AlertLog --> QualityCheck

    QualityCheck --> MissingValues: Detect nulls
    QualityCheck --> Duplicates: Detect duplicates
    QualityCheck --> Outliers: Detect outliers

    MissingValues --> Impute: Select strategy\n(mean/median/forward-fill/drop)
    Duplicates --> Dedupe: Remove exact + fuzzy
    Outliers --> Clip: Cap at 3σ or domain limits

    Impute --> Validate
    Dedupe --> Validate
    Clip --> Validate

    Validate --> QualityScore: Compute data quality score\n(0-100)

    QualityScore --> Pass: Score ≥ 85
    QualityScore --> Quarantine: Score < 85

    Pass --> AuditLog: Log clean run\nrows in/out/issues
    Quarantine --> HumanReview: Flag for review
    HumanReview --> AuditLog

    AuditLog --> [*]: Pipeline complete
```

---

## 6. Workflow 5: Automated Insight Generation & Charting

```mermaid
sequenceDiagram
    participant U as User
    participant UI as React UI
    participant IA as Insight Agent
    participant LLM as Sarvam AI
    participant DB as SQLite / Pandas

    U->>UI: "Generate insights for this week"
    UI->>IA: POST /api/analytics/insights {persona: "exec"}

    IA->>DB: Fetch all metric deltas\n(week-over-week, MoM)

    IA->>IA: Statistical significance test\n(t-test, Mann-Kendall trend)

    IA->>IA: Filter: only p < 0.05 findings

    loop For each significant finding
        IA->>LLM: "Write a {persona} narrative for: {finding}"
        LLM-->>IA: One-paragraph narrative
        IA->>IA: Select chart type\n(line if trend, bar if comparison,\nscatter if correlation)
        IA->>IA: Build Recharts-compatible spec
    end

    IA->>LLM: "Write executive summary\nfor these {N} insights"
    LLM-->>IA: Executive summary paragraph

    IA-->>UI: Structured insight report\n{summary, sections[], charts[]}
    UI->>U: Renders multi-section insight\nreport with live charts
```

---

## 7. Component Architecture (Frontend)

```mermaid
graph TB
    subgraph "React Application"
        APP[App.tsx\nRouter + Providers]

        subgraph "Layout"
            LAY[Layout.tsx]
            SB[Sidebar.tsx]
            HD[Header.tsx]
        end

        subgraph "Pages"
            PG1[Home.tsx\nExecutive Dashboard]
            PG2[BI.tsx\nText-to-SQL Chat]
            PG3[RootCause.tsx\nAnomaly Investigation]
            PG4[Financial.tsx\nFinancial Analysis]
            PG5[Pipeline.tsx\nData Pipeline Monitor]
            PG6[Insights.tsx\nAuto Insights]
        end

        subgraph "Components"
            C1[KPICard]
            C2[SalesChart\nRecharts AreaChart]
            C3[RevenueChart\nRecharts BarChart]
            C4[AnomalyAlert]
            C5[ChatInterface\n+ WebSocket hook]
            C6[ChatMessage\nmarkdown renderer]
        end

        subgraph "State & Data"
            ST[Zustand Store]
            QY[TanStack Query\ncache + refetch]
            API[api.ts\nAxios client]
            WSH[useWebSocket.ts]
        end
    end

    APP --> LAY
    LAY --> SB
    LAY --> HD
    LAY --> PG1 & PG2 & PG3 & PG4 & PG5 & PG6
    PG1 --> C1 & C2 & C3
    PG2 --> C5 & C6
    PG3 --> C4 & C2
    PG4 --> C3 & C2
    PG5 --> C4
    PG6 --> C2 & C3
    C5 --> WSH
    PG1 & PG3 & PG4 & PG5 & PG6 --> QY
    QY --> API
    WSH --> API
    ST --> PG1 & PG2 & PG3
```

---

## 8. Database Entity Relationship

```mermaid
erDiagram
    CUSTOMERS {
        string customer_id PK
        string name
        string email
        string region
        string segment
        string acquisition_channel
        float clv
        date signup_date
    }

    PRODUCTS {
        string product_id PK
        string name
        string category
        string subcategory
        float price
        float cost
        float margin_pct
    }

    SALES_TRANSACTIONS {
        string transaction_id PK
        date date
        string customer_id FK
        string product_id FK
        float amount
        int quantity
        string region
        string channel
        float discount_pct
    }

    DAILY_METRICS {
        date date PK
        float revenue
        int orders
        int sessions
        float conversion_rate
        float nps
        int new_customers
        float avg_order_value
    }

    FINANCIAL_DATA {
        string month PK
        float revenue
        float cogs
        float gross_profit
        float gross_margin
        float opex
        float ebitda
        float net_income
        float net_margin
    }

    WEB_ANALYTICS {
        date date PK
        int sessions
        int pageviews
        float bounce_rate
        float avg_session_duration
        int goal_completions
        float conversion_rate
    }

    ANOMALY_EVENTS {
        string event_id PK
        string metric
        date detected_at
        float actual_value
        float expected_value
        float z_score
        string severity
        string status
    }

    PIPELINE_LOGS {
        string run_id PK
        string stage
        timestamp started_at
        string status
        int rows_processed
        int issues_found
        string notes
    }

    CUSTOMERS ||--o{ SALES_TRANSACTIONS : places
    PRODUCTS ||--o{ SALES_TRANSACTIONS : included_in
```

---

## 9. Security Architecture

```mermaid
flowchart TD
    REQ[Incoming Request] --> CORS[CORS Middleware\nwhitelist: localhost:5173]
    CORS --> RATE[Rate Limiter\n100 req/min per IP]
    RATE --> VAL[Pydantic Validation\nInput sanitization]
    VAL --> AUTH[API Key Header Check\nOptional in dev mode]
    AUTH --> ROUTE[Route Handler]
    ROUTE --> SQL_SAFE[SQL Safety Layer\nParameterized queries\nLangChain SQL toolkit]
    SQL_SAFE --> DB[(Database)]
```

---

## 10. Deployment Architecture (Production)

```mermaid
graph LR
    subgraph "Frontend CDN"
        FE[React Build\nnginx / Vercel]
    end

    subgraph "Backend Service"
        BE[FastAPI + Uvicorn\nGunicorn workers]
    end

    subgraph "Database"
        DB[(PostgreSQL\nProduction DB)]
    end

    subgraph "AI Services"
        SARVAM[Sarvam AI\napi.sarvam.ai]
        LS[LangSmith\nTracing Dashboard]
    end

    USER((User)) --> FE
    FE -->|HTTPS/WSS| BE
    BE --> DB
    BE --> SARVAM
    BE --> LS
```

---

*Agitator Rye Architecture v1.0 — Generated May 2026*
