import React from 'react';
import { renderToString } from 'react-dom/server';
import { AIDecisionCenterScreen } from './src/screens/AIDecisionCenterScreen';

try {
  const html = renderToString(<AIDecisionCenterScreen />);
  console.log("SUCCESS");
} catch (e) {
  console.error("ERROR", e);
}
