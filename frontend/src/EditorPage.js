import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

function EditorPage() {
  const [viewMode, setViewMode] = useState('preview'); // 'preview' or 'code'
  const [uiCodes, setUiCodes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Chat state management
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Phase transition state
  const [isFromPhase1, setIsFromPhase1] = useState(false);
  const [sessionId, setSessionId] = useState("demo_session");
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [category, setCategory] = useState(null);
  
  // Code tab state
  const [activeCodeTab, setActiveCodeTab] = useState('html');
  
  // Store original UI template state for reset functionality
  const [originalUICodes, setOriginalUICodes] = useState(null);
  
  const location = useLocation();

  // Handle transition from Phase 1
  useEffect(() => {
    if (location.state && location.state.fromPhase1) {
      console.log('Transitioning from Phase 1 to Phase 2');
      setIsFromPhase1(true);
      setSessionId(location.state.sessionId || location.state.session_id || "demo_session");
      setSelectedTemplate(location.state.selectedTemplate);
      setCategory(location.state.category);
      
      // Load Phase 1 conversation history
      const phase1History = localStorage.getItem('phase1ChatHistory');
      if (phase1History) {
        try {
          const history = JSON.parse(phase1History);
          console.log('Loaded Phase 1 history from localStorage:', history);
          console.log('History length:', history.length);
          // Convert ChatScreen format to EditorPage format
          const convertedHistory = history.map(msg => {
            let timestamp;
            if (msg.timestamp) {
              // Handle ChatScreen's toLocaleTimeString() format
              if (typeof msg.timestamp === 'string' && msg.timestamp.includes(':')) {
                // It's a time string like "12:00:00 AM", convert to today's date
                const today = new Date();
                const timeParts = msg.timestamp.match(/(\d+):(\d+):(\d+)\s*(AM|PM)/);
                if (timeParts) {
                  let hours = parseInt(timeParts[1]);
                  const minutes = parseInt(timeParts[2]);
                  const seconds = parseInt(timeParts[3]);
                  const ampm = timeParts[4];
                  
                  if (ampm === 'PM' && hours !== 12) hours += 12;
                  if (ampm === 'AM' && hours === 12) hours = 0;
                  
                  today.setHours(hours, minutes, seconds, 0);
                  timestamp = today.toISOString();
                } else {
                  timestamp = new Date().toISOString();
                }
              } else {
                timestamp = new Date(msg.timestamp).toISOString();
              }
            } else {
              timestamp = new Date().toISOString();
            }
            
            return {
              id: msg.id || Date.now() + Math.random(),
              type: msg.sender === 'user' ? 'user' : 'ai',
              content: msg.text || msg.content || '',
              timestamp: timestamp
            };
          });
          setChatMessages(convertedHistory);
          console.log('Loaded Phase 1 conversation history:', convertedHistory.length, 'messages');
        } catch (e) {
          console.error('Error loading Phase 1 history:', e);
        }
      }
      
      // Add transition message
      const transitionMessage = {
        id: Date.now(),
        type: 'ai',
        content: `🎉 Perfect! I've loaded your selected template. You're now in the UI Editor where you can make modifications to your ${category || 'template'}. What would you like to change?`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, transitionMessage]);
    } else {
      // Load chat history from localStorage on component mount (existing logic)
      const savedMessages = localStorage.getItem('editorChatHistory');
      if (savedMessages) {
        try {
          setChatMessages(JSON.parse(savedMessages));
        } catch (e) {
          console.error('Error loading chat history:', e);
          // Initialize with default welcome message
          setChatMessages([
            {
              id: Date.now(),
              type: 'ai',
              content: "I'm ready to help you edit your UI! What would you like to change?",
              timestamp: new Date().toISOString()
            }
          ]);
        }
      } else {
        // Initialize with default welcome message
        setChatMessages([
          {
            id: Date.now(),
            type: 'ai',
            content: "I'm ready to help you edit your UI! What would you like to change?",
            timestamp: new Date().toISOString()
          }
        ]);
      }
    }
  }, [location.state]);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (isFromPhase1) {
      // Save to Phase 2 specific storage
      localStorage.setItem('phase2ChatHistory', JSON.stringify(chatMessages));
    } else {
      // Save to regular editor storage
      localStorage.setItem('editorChatHistory', JSON.stringify(chatMessages));
    }
  }, [chatMessages, isFromPhase1]);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Fetch UI codes from backend on component mount
  useEffect(() => {
    fetchUICodes();
  }, [isFromPhase1, sessionId]);

  // Force refresh on component mount to clear any cached data
  useEffect(() => {
    // Clear any cached data by forcing a fresh fetch
    const timestamp = Date.now();
    console.log('Forcing fresh UI codes fetch at:', timestamp);
    fetchUICodes();
  }, []);

  const fetchUICodes = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let response;
      
      if (isFromPhase1 && sessionId) {
        // Load template from session (Phase 1 transition)
        console.log('Loading template from Phase 1 session:', sessionId);
        response = await fetch(`http://localhost:8000/api/ui-codes/session/${sessionId}`, {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
        
        // If session endpoint fails, try to load the template directly
        if (!response.ok) {
          console.log('Session endpoint failed, trying to load template directly');
          const templateId = selectedTemplate?.template_id;
          if (templateId) {
            response = await fetch(`http://localhost:8000/api/ui-codes/${templateId}`, {
              headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
              }
            });
          } else {
            response = await fetch('http://localhost:8000/api/ui-codes/default', {
              headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
              }
            });
          }
        }
      } else {
        // Load default template (direct access to editor)
        console.log('Loading default template');
        response = await fetch('http://localhost:8000/api/ui-codes/default', {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        });
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('UI codes response:', data);
      
      if (data.success) {
        setUiCodes(data.ui_codes);
        
        // Store original UI codes for reset functionality (only on first load or when not already stored)
        if (!originalUICodes || Object.keys(originalUICodes).length === 0) {
          setOriginalUICodes(data.ui_codes);
          console.log('Original UI codes stored for reset functionality');
        }
        
        console.log('UI codes loaded successfully:', data.ui_codes ? 'with data' : 'empty');
        if (data.ui_codes) {
          console.log('UI codes structure:', Object.keys(data.ui_codes));
          console.log('Template name:', data.ui_codes.template_info?.name || data.ui_codes.current_codes?.template_info?.name);
          console.log('HTML content length:', data.ui_codes.current_codes?.html_export?.length || data.ui_codes.html_export?.length || 0);
          console.log('Complete HTML available:', !!data.ui_codes.current_codes?.complete_html || !!data.ui_codes.complete_html);
        }
      } else {
        throw new Error(data.error || 'Failed to fetch UI codes');
      }
    } catch (err) {
      console.error('Error fetching UI codes:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isSending) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message to chat
    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsSending(true);

    try {
      // Call the AI-powered UI editor chat endpoint
      const chatRequest = {
        message: inputMessage.trim(),
        session_id: sessionId, // Use the session ID from transition state
        current_ui_codes: uiCodes
      };

      const response = await fetch('http://localhost:8000/api/ui-editor/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatRequest)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Add AI response to chat
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.response,
          timestamp: new Date().toISOString()
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Apply modifications if they exist
        if (data.ui_modifications && data.metadata?.intent === "modification_request") {
          await applyModifications(data.ui_modifications);
        }
      } else {
        throw new Error(data.response || 'Failed to get AI response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const applyModifications = async (modifications) => {
    try {
      // Prepare modification request
      const modificationData = {
        template_id: selectedTemplate?.template_id || selectedTemplate?._id || "default",
        modification_type: modifications.type || "css_change",
        changes: modifications.changes || {},
        session_id: sessionId // Use the session ID from transition state
      };

      // Call the modification endpoint
      const response = await fetch('http://localhost:8000/api/ui-codes/modify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(modificationData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Update the UI codes with the modified version
        setUiCodes(data.updated_codes);
      } else {
        throw new Error(data.message || 'Failed to apply modifications');
      }
    } catch (error) {
      console.error('Error applying modifications:', error);
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `❌ Error applying changes: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };



  const handleResetButton = async () => {
    try {
      if (!originalUICodes) {
        throw new Error('No original UI template state available for reset');
      }

      // Restore the original UI template state
      setUiCodes(originalUICodes);
      
      // Add success message to chat
      const successMessage = {
        id: Date.now(),
        type: 'ai',
        content: "✅ I've restored the UI template to its original state! All modifications have been reset.",
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, successMessage]);
      
      console.log('UI template restored to original state');
    } catch (error) {
      console.error('Error resetting UI template:', error);
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `❌ Error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChatHistory = () => {
    const defaultMessage = {
      id: Date.now(),
      type: 'ai',
      content: isFromPhase1 
        ? `🎉 Perfect! I've loaded your selected template. You're now in the UI Editor where you can make modifications to your ${category || 'template'}. What would you like to change?`
        : "I'm ready to help you edit your UI! What would you like to change?",
      timestamp: new Date().toISOString()
    };
    
    setChatMessages([defaultMessage]);
    
    // Clear appropriate localStorage
    if (isFromPhase1) {
      localStorage.removeItem('phase2ChatHistory');
    } else {
      localStorage.removeItem('editorChatHistory');
    }
  };

  const renderPreview = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading UI preview...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-red-600 mb-4">Error loading preview: {error}</p>
            <button 
              onClick={fetchUICodes}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    if (!uiCodes) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-600">No UI codes available</p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow-lg h-full overflow-hidden flex flex-col">
        <div className="flex-1 overflow-auto">
          <iframe 
            id="preview-frame"
            className="w-full border-0 rounded-lg"
            title="UI Preview"
            srcDoc={`${uiCodes.current_codes?.complete_html || uiCodes.complete_html || ''}<!-- Cache bust: ${Date.now()} -->`}
            style={{
              minHeight: '600px',
              height: '100%',
              maxHeight: '100vh',
              overflow: 'auto'
            }}
          />
        </div>
      </div>
    );
  };

  const renderCode = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading code...</p>
          </div>
        </div>
      );
    }

    if (error || !uiCodes) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-600">No code available</p>
        </div>
      );
    }

    const codeTabs = [
      { id: 'html', name: 'index.html', content: uiCodes.current_codes?.html_export || uiCodes.html_export || uiCodes.html || '' },
      { id: 'globals', name: 'globals.css', content: uiCodes.current_codes?.globals_css || uiCodes.globals_css || '' },
      { id: 'style', name: 'style.css', content: uiCodes.current_codes?.style_css || uiCodes.style_css || uiCodes.css || '' }
    ];

    return (
      <div className="bg-white rounded-lg shadow-lg h-full overflow-hidden flex flex-col">
        {/* Code Tabs */}
        <div className="bg-gray-800 border-b border-gray-700 flex-shrink-0">
          <div className="flex">
            {codeTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveCodeTab(tab.id)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  activeCodeTab === tab.id
                    ? 'bg-gray-700 text-white border-b-2 border-purple-500'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        {/* Code Content */}
        <div className="flex-1 overflow-auto">
          <div className="bg-gray-900 p-4 min-h-full">
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
              {codeTabs.find(tab => tab.id === activeCodeTab)?.content || 'No content available'}
            </pre>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Chat Interface Section */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold">AI Editor Chat</h2>
            <p className="text-sm text-gray-600">Ask me to modify your UI</p>
          </div>
          <button 
            onClick={clearChatHistory}
            className="text-sm text-gray-500 hover:text-gray-700 px-2 py-1 rounded"
            title="Clear chat history"
          >
            Clear
          </button>
        </div>
        
        {/* Chat Messages Area */}
        <div className="flex-1 p-4 overflow-y-auto">
          {chatMessages.map((message) => (
            <div 
              key={message.id}
              className={`rounded-lg p-3 mb-4 ${
                message.type === 'ai' 
                  ? 'bg-blue-50' 
                  : 'bg-gray-50'
              }`}
            >
              <p className={`text-sm ${
                message.type === 'ai' 
                  ? 'text-blue-800' 
                  : 'text-gray-800'
              }`}>
                <strong>{message.type === 'ai' ? 'AI:' : 'You:'}</strong> {message.content}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))}
          {isSending && (
            <div className="bg-blue-50 rounded-lg p-3 mb-4">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <p className="text-sm text-blue-800">AI is typing...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Chat Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input 
              type="text" 
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your request here..."
              disabled={isSending}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button 
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isSending}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>

      {/* UI Preview/Code Section */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar with Toggle Buttons */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex space-x-2">
                <button 
                  onClick={() => setViewMode('preview')}
                  className={`px-4 py-2 rounded-lg transition ${
                    viewMode === 'preview' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Preview
                </button>
                <button 
                  onClick={() => setViewMode('code')}
                  className={`px-4 py-2 rounded-lg transition ${
                    viewMode === 'code' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Code
                </button>
              </div>
              <h2 className="text-xl font-bold">UI Editor</h2>
            </div>
            
            {/* Reset to Original Template State */}
            <div className="flex space-x-2">
              <button 
                onClick={handleResetButton}
                className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition"
                title="Reset UI template to original state"
              >
                Reset to Original
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {viewMode === 'preview' ? renderPreview() : renderCode()}
        </div>
      </div>
    </div>
  );
}

export default EditorPage; 