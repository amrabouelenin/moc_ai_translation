// MOC Translation Dashboard Data
// Last updated: October 24, 2025

const dashboardData = {
  // Summary Statistics
  summary: {
    totalLanguages: 6,
    totalRepos: 3,
    repoNames: "GRIB2, BUFR4, CCT",
    totalFiles: 464,
    languagesStarted: "4/5",
    totalRows: 28891,
    overallCompletion: "25%",
  },

  // Main Process Overview (5 processes)
  mainProcesses: [
    {
      id: 1,
      name: "Extraction",
      icon: "📤",
      description: "Extract content from source files",
      status: "complete",
    },
    {
      id: 2,
      name: "Formatting",
      icon: "📝",
      description: "Standardize data format",
      status: "complete",
    },
    {
      id: 3,
      name: "QC Status",
      icon: "✅",
      description: "Quality control checks",
      status: "complete",
    },
    {
      id: 4,
      name: "ID Generation",
      icon: "🆔",
      description: "⚠️ Started (5%)",
      status: "in-progress",
      progress: 5,
    },
    {
      id: 5,
      name: "AI Translation",
      icon: "🤖",
      description: "Automated translation",
      status: "pending",
    },
  ],

  // Languages Data
  languages: {
    english: {
      name: "English",
      flag: "🇬🇧",
      code: "en",
      type: "source",
      status: "ID Gen Pending",
      statusClass: "status-notstarted",
      totalFiles: 464,
      totalRows: 28891,
      repos: "3 Repos",
      reposDetail: "GRIB2, BUFR4, CCT",
      processes: {
        bufridgenration: { progress: 100, status: "complete" },
        grib2idgenration: { progress: 0, status: "started" },

        cctidgenration: { progress: 0, status: "started" },
      },
      alert: {
        type: "info",
        message:
          "Two repos are still pending id generation GRIB2 and CCT, BUFR is complete Id gnerated",
      },
    },
    spanish: {
      name: "Spanish",
      flag: "🇪🇸",
      code: "es",
      type: "full",
      status: "ID Gen Pending",
      statusClass: "status-inprogress",
      totalFiles: 352,
      totalRows: 22164,
      missingRows: 6727,
      processes: {
        extraction: { progress: 100, status: "complete" },
        formatting: { progress: 100, status: "complete" },
        qcStatus: { progress: 100, status: "complete" },
        idGeneration: { progress: 5, status: "started" },
        aiTranslation: { progress: 15, status: "started" },
      },
      alert: {
        type: "warning",
        message:
          "30% of rows are missing. 108 files missing in GRIB2, All repos are translated in spanish",
      },
    },
    french: {
      name: "French",
      flag: "🇫🇷",
      code: "fr",
      type: "full",
      status: "ID Gen Pending",
      statusClass: "status-inprogress",
      totalFiles: "TBD",
      totalRows: "TBD",
      missingRows: "TBD",
      processes: {
        extraction: { progress: 100, status: "complete" },
        formatting: { progress: 100, status: "complete" },
        qcStatus: { progress: 100, status: "complete" },
        idGeneration: { progress: 0, status: "started" },
        aiTranslation: { progress: 0, status: "started" },
      },
      alert: {
        type: "info",
        message: "Only one repos is translated in french which is BUFR4",
      },
    },
    russian: {
      name: "Russian",
      flag: "🇷🇺",
      code: "ru",
      type: "full",
      status: "Extraction phase",
      statusClass: "status-inprogress",
      totalFiles: "TBD",
      totalRows: "TBD",
      missingRows: "TBD",
      processes: {
        extraction: { progress: 5, status: "started" },
        formatting: { progress: 0, status: "started" },
        qcStatus: { progress: 0, status: "started" },
        idGeneration: { progress: 0, status: "started" },
        aiTranslation: { progress: 0, status: "started" },
      },
      alert: {
        type: "info",
        message: "Just started extraction process of russian language",
      },
    },
    arabic: {
      name: "Arabic",
      flag: "🇸🇦",
      code: "ar",
      type: "direct",
      status: "ID Gen + AI Translation",
      statusClass: "status-notstarted",
      totalFiles: 464,
      totalRows: 28891,
      repos: "3 Repos",
      reposDetail: "GRIB2, BUFR4, CCT",
      processes: {
        idGeneration: { progress: 30, status: "started" },
        aiTranslation: { progress: 15, status: "started" },
      },
      alert: {
        type: "info",
        message: "Two repos are still pending id generation GRIB2 and CCT",
      },
    },
    chinese: {
      name: "Chinese",
      flag: "🇨🇳",
      code: "zh",
      type: "direct",
      status: "Not Started",
      totalFiles: 464,
      totalRows: 28891,
      repos: "3 Repos",
      statusClass: "status-notstarted",
      message: "All processes at 0% - No activity",
    },
  },

  // Process Completion Matrix
  processMatrix: {
    processes: [
      "Extraction",
      "Formatting",
      "QC Status",
      "ID Generation",
      "AI Translation",
    ],
    languages: [
      { name: "English", subtitle: "(Source)" },
      { name: "Spanish", subtitle: "" },
      { name: "French", subtitle: "" },
      { name: "Russian", subtitle: "" },
      { name: "Chinese", subtitle: "(Direct)" },
      { name: "Arabic", subtitle: "(Direct)" },
    ],
    data: [
      // Extraction
      ["Source", "✓ 100%", "0%", "0%", "N/A", "N/A"],
      // Formatting
      ["Source", "✓ 100%", "0%", "0%", "N/A", "N/A"],
      // QC Status
      ["Source", "✓ 100%", "0%", "0%", "N/A", "N/A"],
      // ID Generation
      ["5%", "5%", "0%", "0%", "5%", "5%"],
      // AI Translation
      ["Source", "15%", "0%", "0%", "15%", "15%"],
    ],
    cellClasses: [
      // Extraction
      [
        "cell-na",
        "cell-complete",
        "cell-notstarted",
        "cell-notstarted",
        "cell-na",
        "cell-na",
      ],
      // Formatting
      [
        "cell-na",
        "cell-complete",
        "cell-notstarted",
        "cell-notstarted",
        "cell-na",
        "cell-na",
      ],
      // QC Status
      [
        "cell-na",
        "cell-complete",
        "cell-notstarted",
        "cell-notstarted",
        "cell-na",
        "cell-na",
      ],
      // ID Generation
      [
        "cell-started",
        "cell-started",
        "cell-notstarted",
        "cell-notstarted",
        "cell-started",
        "cell-started",
      ],
      // AI Translation
      [
        "cell-na",
        "cell-started",
        "cell-notstarted",
        "cell-notstarted",
        "cell-started",
        "cell-started",
      ],
    ],
  },

  // Critical Blockers
  blockers: [
    {
      priority: "danger",
      title: "1. ID Generation - 0% Across ALL Languages",
      description:
        "This is the #1 blocker. English (source) needs ID Gen to enable all target languages. Spanish is ready but blocked.",
    },
    {
      priority: "danger",
      title: "2. Spanish Data Quality Issues",
      description:
        "6,727 missing rows (30%) and 108 missing files in GRIB2 may impact translation quality.",
    },
    {
      priority: "warning",
      title: "3. French & Russian - No Activity",
      description: "These languages haven't started the extraction phase yet.",
    },
    {
      priority: "warning",
      title: "4. Chinese & Arabic - Awaiting English IDs",
      description:
        "Direct translation from English cannot start until English ID Generation is complete.",
    },
  ],

  // Process Flow Information
  processFlows: [
    {
      languages: "🇬🇧 English (Source)",
      flow: "ID Generation only",
    },
    {
      languages: "🇪🇸 Spanish / 🇫🇷 French / 🇷🇺 Russian",
      flow: "Extraction → Formatting → QC → ID Generation → AI Translation",
    },
    {
      languages: "🇨🇳 Chinese / 🇸🇦 Arabic",
      flow: "ID Generation → AI Translation (direct from English)",
    },
  ],

  // Metadata
  metadata: {
    lastUpdated: "October 24, 2025",
    generatedFrom: "MOC Translation Status data",
  },
};
