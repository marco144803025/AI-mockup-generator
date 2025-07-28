import React, { useState, useEffect } from 'react';

function DebugPanel({ sessionId, isVisible, onClose }) {
  const [debugInfo, setDebugInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('session');

  const fetchDebugInfo = async () => {
    console.log('DebugPanel: fetchDebugInfo called with sessionId:', sessionId);
    if (!sessionId) {
      console.log('DebugPanel: No sessionId available');
      return;
    }
    
    setLoading(true);
    try {
      console.log('DebugPanel: Fetching from:', `http://localhost:8000/api/debug/session/${sessionId}`);
      const response = await fetch(`http://localhost:8000/api/debug/session/${sessionId}`);
      console.log('DebugPanel: Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('DebugPanel: Received data:', data);
        setDebugInfo(data);
      } else {
        const errorText = await response.text();
        console.error('DebugPanel: Response not ok:', response.status, errorText);
      }
    } catch (error) {
      console.error('DebugPanel: Error fetching debug info:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isVisible && sessionId) {
      fetchDebugInfo();
    }
  }, [isVisible, sessionId]);

  if (!isVisible) return null;

  return (
    <div className="debug-panel">
      <div className="debug-header">
        <h3>Agent Debug Panel</h3>
        <button onClick={onClose} className="close-button">×</button>
      </div>
      
      <div className="debug-tabs">
        <button 
          className={activeTab === 'session' ? 'active' : ''} 
          onClick={() => setActiveTab('session')}
        >
          Session State
        </button>
        <button 
          className={activeTab === 'conversation' ? 'active' : ''} 
          onClick={() => setActiveTab('conversation')}
        >
          Conversation History
        </button>
        <button 
          className={activeTab === 'validation' ? 'active' : ''} 
          onClick={() => setActiveTab('validation')}
        >
          Validation
        </button>
        <button 
          className={activeTab === 'tools' ? 'active' : ''} 
          onClick={() => setActiveTab('tools')}
        >
          Tools
        </button>
      </div>

      <div className="debug-content">
        {loading ? (
          <div className="loading">Loading debug information...</div>
        ) : debugInfo ? (
          <>
            {debugInfo.error && (
              <div className="debug-section">
                <h4>Error</h4>
                <pre style={{color: 'red'}}>{JSON.stringify(debugInfo, null, 2)}</pre>
              </div>
            )}
            
            {activeTab === 'session' && (
              <div className="debug-section">
                <h4>Session State</h4>
                <pre>{JSON.stringify(debugInfo.session_state, null, 2)}</pre>
              </div>
            )}
            
            {activeTab === 'conversation' && (
              <div className="debug-section">
                <h4>Conversation History</h4>
                <pre>{JSON.stringify(debugInfo.conversation_history, null, 2)}</pre>
              </div>
            )}
            
            {activeTab === 'validation' && (
              <div className="debug-section">
                <h4>Validation Summary</h4>
                <pre>{JSON.stringify(debugInfo.validation_summary, null, 2)}</pre>
              </div>
            )}
            
            {activeTab === 'tools' && (
              <div className="debug-section">
                <h4>Tool Statistics</h4>
                <pre>{JSON.stringify(debugInfo.tool_statistics, null, 2)}</pre>
              </div>
            )}
          </>
        ) : (
          <div className="no-data">
            <p>No debug information available</p>
            <p>Session ID: {sessionId || 'None'}</p>
            <p>Try sending a message first to create a session</p>
          </div>
        )}
      </div>

      <div className="debug-footer">
        <button onClick={fetchDebugInfo} disabled={loading}>
          Refresh Debug Info
        </button>
        <span className="session-id">Session: {sessionId || 'None'}</span>
      </div>
    </div>
  );
}

export default DebugPanel; 