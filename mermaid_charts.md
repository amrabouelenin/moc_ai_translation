# MOC Translation Project - Mermaid Visualizations

## 📋 Translation Process Flows

- **🇬🇧 English (Source):** ID Generation only
- **🇪🇸 Spanish / 🇫🇷 French / 🇷🇺 Russian:** Extraction → Formatting → QC → ID Generation → AI Translation
- **🇨🇳 Chinese / 🇸🇦 Arabic:** ID Generation → AI Translation (direct from English)

## Process Flow Diagram

```mermaid
graph TB
    subgraph English[English SOURCE - ID Gen Only]
        E1[ID Generation<br/>🔴 0%]
        E1 --> E_END[Source Complete]
        
        style E1 fill:#dc3545,stroke:#333,color:#fff,stroke-width:3px
        style E_END fill:#0066cc,stroke:#333,color:#fff
    end
    
    subgraph Spanish[Spanish - 60% Complete]
        S1[Extraction<br/>✅ 100%]
        S2[Formatting<br/>✅ 100%]
        S3[QC Status<br/>✅ 100%]
        S4[ID Generation<br/>🔴 0%]
        S5[AI Translation<br/>🔴 0%]
        S1 --> S2 --> S3 --> S4 --> S5
        
        style S1 fill:#28a745,stroke:#333,color:#fff
        style S2 fill:#28a745,stroke:#333,color:#fff
        style S3 fill:#28a745,stroke:#333,color:#fff
        style S4 fill:#dc3545,stroke:#333,color:#fff
        style S5 fill:#dc3545,stroke:#333,color:#fff
    end
    
    subgraph French[French - Not Started]
        F1[Extraction<br/>🔴 0%]
        F2[Formatting<br/>🔴 0%]
        F3[QC Status<br/>🔴 0%]
        F4[ID Generation<br/>🔴 0%]
        F5[AI Translation<br/>🔴 0%]
        F1 --> F2 --> F3 --> F4 --> F5
        
        style F1 fill:#dc3545,stroke:#333,color:#fff
        style F2 fill:#dc3545,stroke:#333,color:#fff
        style F3 fill:#dc3545,stroke:#333,color:#fff
        style F4 fill:#dc3545,stroke:#333,color:#fff
        style F5 fill:#dc3545,stroke:#333,color:#fff
    end
    
    subgraph Russian[Russian - Not Started]
        R1[Extraction<br/>🔴 0%]
        R2[Formatting<br/>🔴 0%]
        R3[QC Status<br/>🔴 0%]
        R4[ID Generation<br/>🔴 0%]
        R5[AI Translation<br/>🔴 0%]
        R1 --> R2 --> R3 --> R4 --> R5
        
        style R1 fill:#dc3545,stroke:#333,color:#fff
        style R2 fill:#dc3545,stroke:#333,color:#fff
        style R3 fill:#dc3545,stroke:#333,color:#fff
        style R4 fill:#dc3545,stroke:#333,color:#fff
        style R5 fill:#dc3545,stroke:#333,color:#fff
    end
    
    subgraph Chinese[Chinese DIRECT - From English]
        C1[ID Generation<br/>🔴 0%]
        C2[AI Translation<br/>🔴 0%]
        C1 --> C2
        
        style C1 fill:#dc3545,stroke:#333,color:#fff
        style C2 fill:#dc3545,stroke:#333,color:#fff
    end
    
    subgraph Arabic[Arabic DIRECT - From English]
        A1[ID Generation<br/>🔴 0%]
        A2[AI Translation<br/>🔴 0%]
        A1 --> A2
        
        style A1 fill:#dc3545,stroke:#333,color:#fff
        style A2 fill:#dc3545,stroke:#333,color:#fff
    end
    
    English -.English IDs enable.-> Chinese
    English -.English IDs enable.-> Arabic
```

## Gantt Chart - Project Timeline

```mermaid
gantt
    title MOC Translation Project Timeline
    dateFormat YYYY-MM-DD
    
    section English (Source)
    ID Generation       :crit, en1, 2025-04-01, 30d
    
    section Spanish
    Extraction           :done, sp1, 2025-01-01, 2025-02-01
    Formatting          :done, sp2, 2025-02-01, 2025-03-01
    QC Status           :done, sp3, 2025-03-01, 2025-04-01
    ID Generation       :crit, sp4, 2025-04-01, 30d
    AI Translation      :crit, sp5, after sp4, 45d
    
    section French
    Extraction          :fr1, 2025-04-15, 30d
    Formatting          :fr2, after fr1, 25d
    QC Status           :fr3, after fr2, 20d
    ID Generation       :crit, fr4, after fr3, 30d
    AI Translation      :crit, fr5, after fr4, 45d
    
    section Russian
    Extraction          :ru1, 2025-04-15, 30d
    Formatting          :ru2, after ru1, 25d
    QC Status           :ru3, after ru2, 20d
    ID Generation       :crit, ru4, after ru3, 30d
    AI Translation      :crit, ru5, after ru4, 45d
    
    section Chinese (Direct)
    ID Generation       :crit, ch1, after en1, 30d
    AI Translation      :crit, ch2, after ch1, 45d
    
    section Arabic (Direct)
    ID Generation       :crit, ar1, after en1, 30d
    AI Translation      :crit, ar2, after ar1, 45d
```

## Language Progress Pie Chart

```mermaid
pie title Overall Language Progress Distribution
    "Spanish (In Progress)" : 1
    "English (Source - Pending)" : 1
    "French (Not Started)" : 1
    "Russian (Not Started)" : 1
    "Chinese (Direct Translation)" : 1
    "Arabic (Direct Translation)" : 1
```

## Process Status Overview

```mermaid
graph LR
    A[Total Processes: 30] --> B[Completed: 3]
    A --> C[Not Started: 21]
    A --> D[Source: 6]
    
    B --> B1[Spanish Extraction]
    B --> B2[Spanish Formatting]
    B --> B3[Spanish QC]
    
    C --> C1[ID Generation: 0% ALL 6 langs]
    C --> C2[AI Translation: 0% ALL 5 langs]
    C --> C3[French/Russian: All Processes]
    
    D --> D1[English Source Language]
    
    style B fill:#28a745,color:#fff
    style C fill:#dc3545,color:#fff
    style D fill:#0066cc,color:#fff
```

## Critical Path Analysis

```mermaid
graph TD
    START[Project Start] --> EN1[English ID Gen<br/>🔴 CRITICAL]
    EN1 --> EN_END[English Source Ready]
    
    START --> SP1{Spanish Ready?}
    SP1 -->|YES| SP_ID[Spanish ID Gen<br/>🔴 BLOCKER]
    SP_ID --> SP_AI[Spanish AI Trans]
    SP_AI --> SP_END[Spanish Complete]
    
    START --> FR1[French Extraction<br/>🔴 Not Started]
    FR1 --> FR2[French Formatting]
    FR2 --> FR3[French QC]
    FR3 --> FR_ID[French ID Gen]
    FR_ID --> FR_AI[French AI Trans]
    FR_AI --> FR_END[French Complete]
    
    START --> RU1[Russian Extraction<br/>🔴 Not Started]
    RU1 --> RU2[Russian Formatting]
    RU2 --> RU3[Russian QC]
    RU3 --> RU_ID[Russian ID Gen]
    RU_ID --> RU_AI[Russian AI Trans]
    RU_AI --> RU_END[Russian Complete]
    
    EN_END -.Enables.-> CH1[Chinese ID Gen]
    CH1 --> CH2[Chinese AI Trans]
    CH2 --> CH_END[Chinese Complete]
    
    EN_END -.Enables.-> AR1[Arabic ID Gen]
    AR1 --> AR2[Arabic AI Trans]
    AR2 --> AR_END[Arabic Complete]
    
    SP_END --> FINAL[All Languages Complete]
    FR_END --> FINAL
    RU_END --> FINAL
    CH_END --> FINAL
    AR_END --> FINAL
    
    style EN1 fill:#dc3545,stroke:#333,color:#fff,stroke-width:4px
    style SP_ID fill:#dc3545,stroke:#333,color:#fff,stroke-width:3px
    style EN_END fill:#0066cc,stroke:#333,color:#fff
    style FINAL fill:#28a745,stroke:#333,color:#fff
```

## Repository Breakdown

```mermaid
graph TB
    subgraph Spanish_Repos[Spanish Language Repos]
        SG[GRIB2<br/>260 files<br/>4,808 rows]
        SB[BUFR4<br/>78 files<br/>14,877 rows]
        SC[CCT<br/>14 files<br/>2,479 rows]
    end
    
    subgraph English_Repos[English Language Repos]
        EG[GRIB2<br/>370 files<br/>8,439 rows]
        EB[BUFR4<br/>80 files<br/>17,499 rows]
        EC[CCT<br/>? files<br/>2,953 rows]
    end
    
    style SG fill:#ffc107,stroke:#333
    style SB fill:#ffc107,stroke:#333
    style SC fill:#ffc107,stroke:#333
    style EG fill:#17a2b8,stroke:#333,color:#fff
    style EB fill:#17a2b8,stroke:#333,color:#fff
    style EC fill:#17a2b8,stroke:#333,color:#fff
```

---

**Legend:**
- ✅ Green = Completed (100%)
- 🔴 Red = Not Started (0%)
- ⚫ Gray = Not Applicable (N/A)
- 🟡 Yellow = In Progress

**How to View:**
Copy any of these Mermaid code blocks into:
- GitHub/GitLab markdown files (will render automatically)
- Mermaid Live Editor: https://mermaid.live/
- VS Code with Mermaid Preview extension
- Notion, Confluence, or other tools supporting Mermaid
