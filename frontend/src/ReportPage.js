import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const BACKEND_BASE_URL = 'http://localhost:8000';

function ReportPage() {
  const [reportOptions, setReportOptions] = useState({
    uiDescription: true,
    uiTags: true,
    uiPreview: true,
    uiCode: false,
    changesMade: true,
    creationDate: true,
    agentRationale: false
  });
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportGenerated, setReportGenerated] = useState(false);
  const [reportFile, setReportFile] = useState(null);
  const [reportMetadata, setReportMetadata] = useState(null); // Used in handleDownload function
  const [error, setError] = useState(null);
  
  const location = useLocation();
  const navigate = useNavigate();
  
  // Get session data from location state
  const sessionData = location.state?.sessionData || {};
  const sessionId = sessionData.sessionId || 'demo_session';
  const uiCodes = sessionData.uiCodes || {};
  const projectInfo = sessionData.projectInfo || {};

  const handleOptionChange = (option) => {
    setReportOptions(prev => ({
      ...prev,
      [option]: !prev[option]
    }));
  };

  const withTimeout = async (promise, ms = 60000) => {
    const timeout = new Promise((_, reject) => {
      const id = setTimeout(() => {
        clearTimeout(id);
        reject(new Error('Request timed out'));
      }, ms);
    });
    return Promise.race([promise, timeout]);
  };

  const generateReport = async () => {
    setIsGenerating(true);
    setError(null);
    console.log('🧾 Generating custom report with options:', reportOptions, 'session:', sessionId);
    
    try {
      const response = await withTimeout(fetch(`http://localhost:8000/api/ui-editor/generate-custom-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          report_options: reportOptions,
          // Send only minimal payload to avoid large body timeouts
          project_info: projectInfo
        }),
      }));

      console.log('🧾 Generate report response status:', response.status);

      if (!response.ok) {
        const text = await response.text();
        console.error('🧾 Generate report error body:', text);
        throw new Error(`HTTP ${response.status}: ${text || 'Unknown error'}`);
      }

      const data = await response.json();
      console.log('🧾 Generate report data:', data);
      
      if (data.success) {
        setReportGenerated(true);
        setReportFile(data.report_file);
        setReportMetadata(data.report_metadata);
      } else {
        throw new Error(data.error || 'Failed to generate report');
      }
    } catch (error) {
      console.error('🧾 Error generating report:', error);
      setError(`Error generating report: ${error.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async () => {
    if (!reportFile) return;
    console.log('⬇️ Downloading report:', reportFile);
    
    try {
      const response = await withTimeout(fetch(`http://localhost:8000/api/reports/download/${reportFile}`, {
        method: 'GET',
      }));
      
      if (!response.ok) {
        const text = await response.text();
        console.error('⬇️ Download report error body:', text);
        throw new Error(`HTTP ${response.status}: ${text || 'Unknown error'}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = reportFile;
      document.body.appendChild(a);
      a.click();
      
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('⬇️ Error downloading report:', error);
      alert(`Error downloading report: ${error.message}`);
    }
  };

  const handleBackToEditor = () => {
    navigate('/editor', { 
      state: { 
        sessionData: sessionData,
        fromReportPage: true 
      } 
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Generate Custom Report
              </h1>
              <p className="text-gray-600">
                Select the content you want to include in your UI mockup report
              </p>
            </div>
            <button
              onClick={handleBackToEditor}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition"
            >
              ← Back to Editor
            </button>
          </div>
        </div>

        {/* Report Options */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Report Content Options
          </h2>
          
          <div className="space-y-4">
            {/* UI Description */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="uiDescription"
                checked={reportOptions.uiDescription}
                onChange={() => handleOptionChange('uiDescription')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="uiDescription" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">Description of UI</div>
                <div className="text-sm text-gray-500">Include a detailed description of the UI mockup and its purpose</div>
              </label>
            </div>

            {/* UI Tags */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="uiTags"
                checked={reportOptions.uiTags}
                onChange={() => handleOptionChange('uiTags')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="uiTags" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">Tags of UI</div>
                <div className="text-sm text-gray-500">Include relevant tags and categories for the UI design</div>
              </label>
            </div>

            {/* UI Preview */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="uiPreview"
                checked={reportOptions.uiPreview}
                onChange={() => handleOptionChange('uiPreview')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="uiPreview" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">UI Preview</div>
                <div className="text-sm text-gray-500">Include a screenshot of the current UI mockup</div>
              </label>
            </div>

            {/* UI Code */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="uiCode"
                checked={reportOptions.uiCode}
                onChange={() => handleOptionChange('uiCode')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="uiCode" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">UI Code</div>
                <div className="text-sm text-gray-500">Include the HTML and CSS code for the UI mockup</div>
              </label>
            </div>

            {/* Changes Made */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="changesMade"
                checked={reportOptions.changesMade}
                onChange={() => handleOptionChange('changesMade')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="changesMade" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">Changes Made</div>
                <div className="text-sm text-gray-500">Include a list of modifications made and the reasoning behind them</div>
              </label>
            </div>

            {/* Agent Rationale */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="agentRationale"
                checked={reportOptions.agentRationale}
                onChange={() => handleOptionChange('agentRationale')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="agentRationale" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">Agent Decision Rationale</div>
                <div className="text-sm text-gray-500">Include detailed reasoning behind AI agent decisions for template selection, UI modifications, and workflow choices</div>
              </label>
            </div>

            {/* Creation Date */}
            <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <input
                type="checkbox"
                id="creationDate"
                checked={reportOptions.creationDate}
                onChange={() => handleOptionChange('creationDate')}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="creationDate" className="flex-1 cursor-pointer">
                <div className="font-medium text-gray-900">Creation Date</div>
                <div className="text-sm text-gray-500">Include the project creation and completion dates</div>
              </label>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {Object.values(reportOptions).filter(Boolean).length} of 7 options selected
            </div>
            
            <div className="flex space-x-3">
              {!reportGenerated ? (
                <button
                  onClick={generateReport}
                  disabled={isGenerating || Object.values(reportOptions).every(opt => !opt)}
                  className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center"
                >
                  {isGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Generating...
                    </>
                  ) : (
                    'Generate Report'
                  )}
                </button>
              ) : (
                <button
                  onClick={handleDownload}
                  className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Download Report
                </button>
              )}
            </div>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}
          
          {reportGenerated && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-700 text-sm">
                Report generated successfully! Click "Download Report" to get your PDF.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportPage;
