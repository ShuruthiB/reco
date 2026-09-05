const fs = require('fs');
const path = require('path');

const replaceInFile = (filePath, replacements) => {
  let content = fs.readFileSync(filePath, 'utf8');
  for (const { search, replace } of replacements) {
    if (typeof search === 'string') {
      content = content.split(search).join(replace);
    } else {
      content = content.replace(search, replace);
    }
  }
  fs.writeFileSync(filePath, content, 'utf8');
};

const screensDir = path.join(__dirname, 'src', 'screens');
const uiDir = path.join(__dirname, 'src', 'components', 'ui');
const layoutDir = path.join(__dirname, 'src', 'components', 'layout');
const srcDir = path.join(__dirname, 'src');

// App.tsx
replaceInFile(path.join(srcDir, 'App.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);

// Layout
replaceInFile(path.join(layoutDir, 'Layout.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);
replaceInFile(path.join(layoutDir, 'Sidebar.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);
replaceInFile(path.join(layoutDir, 'Topbar.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);

// Screens
replaceInFile(path.join(screensDir, 'AIDecisionCenterScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "import { Card, CardHeader, CardTitle, CardContent }", replace: "import { Card, CardContent }" },
  { search: "<XCircle className=\"w-4 h-4 text-red-500\" title={c.rejectReason} />", replace: "<div title={c.rejectReason}><XCircle className=\"w-4 h-4 text-red-500\" /></div>" }
]);

replaceInFile(path.join(screensDir, 'AuditTrailScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "import { MOCK_AUDIT, AuditEvent }", replace: "import { MOCK_AUDIT, type AuditEvent }" }
]);

replaceInFile(path.join(screensDir, 'ExperimentsScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);

replaceInFile(path.join(screensDir, 'OverviewDashboard.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "DollarSign, ShieldAlert, Sparkles, TrendingUp, RefreshCcw, Activity", replace: "DollarSign, ShieldAlert, Sparkles, RefreshCcw" }
]);

replaceInFile(path.join(screensDir, 'PoliciesScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "import { Card, CardHeader, CardTitle, CardContent }", replace: "import { Card, CardTitle, CardContent }" }
]);

replaceInFile(path.join(screensDir, 'RecoveryBudgetScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);

replaceInFile(path.join(screensDir, 'SettingsScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" }
]);

replaceInFile(path.join(screensDir, 'SystemHealthScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "import { Card, CardHeader, CardTitle, CardContent }", replace: "import { Card }" }
]);

replaceInFile(path.join(screensDir, 'TransactionDetailsScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "ArrowLeft, Clock, ShieldAlert, CreditCard, Activity", replace: "ArrowLeft, ShieldAlert, CreditCard, Activity" },
  { search: "import { useParams, Link } from 'react-router-dom';", replace: "import { useParams, Link, useNavigate } from 'react-router-dom';" },
  { search: "const { id } = useParams();", replace: "const { id } = useParams();\n  const navigate = useNavigate();" },
  { search: "<Button variant=\"ghost\" size=\"sm\" asChild>\n          <Link to=\"/transactions\">\n            <ArrowLeft className=\"w-4 h-4 mr-2\" />\n            Back\n          </Link>\n        </Button>", replace: "<Button variant=\"ghost\" size=\"sm\" onClick={() => navigate('/transactions')}>\n          <ArrowLeft className=\"w-4 h-4 mr-2\" />\n          Back\n        </Button>" }
]);

replaceInFile(path.join(screensDir, 'TransactionsScreen.tsx'), [
  { search: "import React from 'react';\n", replace: "" },
  { search: "import { MOCK_TRANSACTIONS, Transaction }", replace: "import { MOCK_TRANSACTIONS, type Transaction }" }
]);

replaceInFile(path.join(screensDir, 'InterventionSimulatorScreen.tsx'), [
  { search: "import React, { useState } from 'react';", replace: "import { useState, type FormEvent } from 'react';" },
  { search: "React.FormEvent", replace: "FormEvent" }
]);

// UI Components
replaceInFile(path.join(uiDir, 'Button.tsx'), [
  { search: "import React from 'react';", replace: "import { forwardRef, type ButtonHTMLAttributes } from 'react';" },
  { search: "React.ButtonHTMLAttributes", replace: "ButtonHTMLAttributes" },
  { search: "React.forwardRef", replace: "forwardRef" }
]);

replaceInFile(path.join(uiDir, 'Card.tsx'), [
  { search: "import React from 'react';", replace: "import { type HTMLAttributes } from 'react';" },
  { search: /React\.HTMLAttributes/g, replace: "HTMLAttributes" }
]);

replaceInFile(path.join(uiDir, 'Badge.tsx'), [
  { search: "import React from 'react';", replace: "import { type HTMLAttributes } from 'react';" },
  { search: "React.HTMLAttributes", replace: "HTMLAttributes" }
]);

replaceInFile(path.join(uiDir, 'MetricCard.tsx'), [
  { search: "import React from 'react';", replace: "import { type ReactNode } from 'react';" },
  { search: /React\.ReactNode/g, replace: "ReactNode" }
]);

replaceInFile(path.join(uiDir, 'DataTable.tsx'), [
  { search: "import React from 'react';", replace: "import { type ReactNode } from 'react';" },
  { search: /React\.ReactNode/g, replace: "ReactNode" }
]);

console.log("Done");
