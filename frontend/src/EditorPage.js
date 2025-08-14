import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

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
  
  // Report generation is now handled by the separate ReportPage
  
  // Logo upload state
  const [uploadedLogo, setUploadedLogo] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const fileInputRef = useRef(null);
  
  // Phase transition state
  const [isFromPhase1, setIsFromPhase1] = useState(false);
  const [sessionId, setSessionId] = useState("demo_session");
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [category, setCategory] = useState(null);
  
  // Code tab state
  const [activeCodeTab, setActiveCodeTab] = useState('html');
  
  // Store original UI template state for reset functionality
  const [originalUICodes, setOriginalUICodes] = useState(null);
  
  // Zoom state for preview
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panPosition, setPanPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });
  const previewContainerRef = useRef(null);
  
  const location = useLocation();
  const navigate = useNavigate();

  // Zoom control functions
  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.25, 3)); // Max zoom 3x
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.25, 0.25)); // Min zoom 0.25x
  };

  const handleZoomReset = () => {
    setZoomLevel(1);
    setPanPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (zoomLevel > 1) {
      setIsDragging(true);
      setLastMousePos({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging && zoomLevel > 1) {
      const deltaX = e.clientX - lastMousePos.x;
      const deltaY = e.clientY - lastMousePos.y;
      setPanPosition(prev => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY
      }));
      setLastMousePos({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e) => {
    // Only zoom when holding Ctrl key
    if (e.ctrlKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      setZoomLevel(prev => Math.max(0.25, Math.min(3, prev + delta)));
    }
    // Otherwise, allow normal scrolling (don't preventDefault)
  };

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
        content: `Welcome to the UI Editor! You can now make modifications to your ${category || 'template'}. What would you like to change?`,
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
  }, [location.state, category]);

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
  
  // Debug popup state changes
  // Report generation is now handled by the separate ReportPage

  const fetchUICodes = useCallback(async () => {
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
        // Combine UI codes with screenshot preview
        const combinedData = {
          ...data.ui_codes,
          screenshot_preview: data.screenshot_preview
        };
        
        setUiCodes(combinedData);
        
        // Store original UI codes for reset functionality (only on first load or when not already stored)
        if (!originalUICodes || Object.keys(originalUICodes).length === 0) {
          setOriginalUICodes(combinedData);
          console.log('Original UI codes stored for reset functionality');
        }
        
        console.log('UI codes loaded successfully:', combinedData ? 'with data' : 'empty');
        if (combinedData) {
          console.log('UI codes structure:', Object.keys(combinedData));
          console.log('Template name:', combinedData.template_info?.name || combinedData.current_codes?.template_info?.name);
          console.log('HTML content length:', combinedData.current_codes?.html_export?.length || combinedData.html_export?.length || 0);
          console.log('HTML export available:', !!combinedData.current_codes?.html_export || !!combinedData.html_export);
          console.log('Screenshot preview available:', !!combinedData.screenshot_preview);
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
  }, [isFromPhase1, sessionId, selectedTemplate]);

  // Fetch UI codes from backend on component mount
  useEffect(() => {
    // Clear any cached data by forcing a fresh fetch
    const timestamp = Date.now();
    console.log('Forcing fresh UI codes fetch at:', timestamp);
    fetchUICodes();
  }, [fetchUICodes]);

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
      let response;
      let data;

      // Check if logo is uploaded to determine which endpoint to use
      if (uploadedLogo) {
        // Logo analysis endpoint
        console.log('Logo detected, using logo analysis endpoint');
        
        // Convert file to base64
        const base64Logo = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const base64 = e.target.result.split(',')[1]; // Remove data:image/...;base64, prefix
            resolve(base64);
          };
          reader.readAsDataURL(uploadedLogo);
        });

        // Send logo analysis request
        response = await fetch('http://localhost:8000/api/ui-editor/analyze-logo', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: inputMessage.trim(),
            logo_image: base64Logo,
            logo_filename: uploadedLogo.name,
            session_id: sessionId,
            current_ui_codes: uiCodes?.current_codes || uiCodes
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();
        
        if (data.success) {
          // Add the analysis request and response to chat
          const userMessageWithLogo = {
            id: Date.now(),
            type: 'user',
            content: `📎 [Logo Analysis Request] ${inputMessage.trim()}`,
            timestamp: new Date().toISOString(),
            hasLogo: true,
            logoPreview: logoPreview
          };
          
          const aiMessage = {
            id: Date.now() + 1,
            type: 'ai',
            content: data.response,
            timestamp: new Date().toISOString(),
            logoAnalysis: data.logo_analysis
          };
          
          setChatMessages(prev => [...prev, userMessageWithLogo, aiMessage]);
          
          // Update UI codes if modifications were applied
          if (data.ui_modifications) {
            await applyModifications(data.ui_modifications);
          }
        } else {
          throw new Error(data.error || 'Failed to analyze logo');
        }
      } else {
        // Regular chat endpoint
        console.log('No logo detected, using regular chat endpoint');
        
        const chatRequest = {
          message: inputMessage.trim(),
          session_id: sessionId,
          current_ui_codes: uiCodes
        };

        response = await fetch('http://localhost:8000/api/ui-editor/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(chatRequest)
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        data = await response.json();
        
        if (data.success) {
          // Add AI response to chat
          const aiMessage = {
            id: Date.now() + 1,
            type: 'ai',
            content: data.response,
            timestamp: new Date().toISOString()
          };
          setChatMessages(prev => [...prev, aiMessage]);
          
          // Refresh UI codes if modifications were made
          if (data.ui_modifications && data.metadata?.intent === "modification_request") {
            console.log('Modifications detected, refreshing UI codes from session...');
            await fetchUICodes();
          }
        } else {
          throw new Error(data.response || 'Failed to get AI response');
        }
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
        content: `Error applying changes: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };



  const handleResetButton = async () => {
    try {
      // Call backend to reset session to original state
      const response = await fetch(`http://localhost:8000/api/ui-codes/session/${sessionId}/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to reset session to original state');
      }

      const data = await response.json();
      
      if (data.success) {
        // Refresh UI codes from the reset session
        await fetchUICodes();
        
        // Add success message to chat
        const successMessage = {
          id: Date.now(),
          type: 'ai',
          content: "I've restored the UI template to its original state! All modifications have been reset.",
          timestamp: new Date().toISOString()
        };
        setChatMessages(prev => [...prev, successMessage]);
        
        console.log('UI template restored to original state via backend');
      } else {
        throw new Error(data.message || 'Failed to reset session');
      }
    } catch (error) {
      console.error('Error resetting UI template:', error);
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `Error: ${error.message}`,
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

  // Report generation is now handled by the separate ReportPage



  // Logo upload functions
  const handleLogoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file (PNG, JPG, JPEG, etc.)');
        return;
      }
      
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB');
        return;
      }
      
      setUploadedLogo(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };



  const removeLogo = () => {
    setUploadedLogo(null);
    setLogoPreview(null);
    setInputMessage(''); // Clear input message when logo is removed
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const renderPreview = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Generating UI preview...</p>
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

    // Check if we have a screenshot preview from the backend
    const screenshotPreview = uiCodes.screenshot_preview;
    
    if (screenshotPreview && screenshotPreview.length > 0) {
      return (
        <div className="bg-white rounded-lg shadow-lg h-full overflow-hidden flex flex-col">
          {/* Header with Live Preview indicator and Zoom Controls */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              Live Preview
            </div>
            
            {/* Zoom Controls */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleZoomOut}
                className="p-1 hover:bg-gray-100 rounded text-gray-600 text-sm"
                disabled={zoomLevel <= 0.25}
              >
                Zoom−
              </button>
              <span className="text-xs text-gray-500 min-w-[50px] text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-1 hover:bg-gray-100 rounded text-gray-600 text-sm"
                disabled={zoomLevel >= 3}
              >
                Zoom+
              </button>
              <button
                onClick={handleZoomReset}
                className="p-1 hover:bg-gray-100 rounded text-gray-600 text-xs"
              >
                Reset
              </button>
            </div>
          </div>

          {/* Preview Container */}
          <div className="flex-1 overflow-hidden relative">
            <div 
              ref={previewContainerRef}
              className="w-full h-full overflow-auto cursor-grab active:cursor-grabbing"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
              style={{
                cursor: zoomLevel > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default'
              }}
            >
              <div className="flex justify-center items-start p-4">
                <img 
                  src={`data:image/png;base64,${screenshotPreview}`}
                  alt="UI Preview"
                  className="rounded-lg shadow-lg border border-gray-200 select-none"
                  style={{
                    transform: `scale(${zoomLevel}) translate(${panPosition.x / zoomLevel}px, ${panPosition.y / zoomLevel}px)`,
                    transformOrigin: 'center top',
                    transition: isDragging ? 'none' : 'transform 0.1s ease',
                    maxWidth: 'none'
                  }}
                  draggable={false}
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Preview generated from headless browser • Ctrl+scroll to zoom • Drag when zoomed • Use zoom buttons for control
            </p>
          </div>
        </div>
      );
    }

    // Fallback: Show loading state while generating screenshot
    return (
      <div className="bg-white rounded-lg shadow-lg h-full overflow-hidden flex flex-col">
        <div className="flex-1 overflow-auto flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Generating screenshot preview...</p>
            <button 
              onClick={fetchUICodes}
              className="mt-4 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
            >
              Refresh
            </button>
          </div>
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
        <div className="p-4 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold">AI Editor Chat</h2>
            <p className="text-sm text-gray-600">Ask me to modify your UI</p>
          </div>
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
              {/* Logo Preview for User Messages */}
              {message.hasLogo && message.logoPreview && (
                <div className="mb-2 p-2 border border-gray-200 rounded bg-white">
                  <div className="flex items-center space-x-2">
                    <img 
                      src={message.logoPreview} 
                      alt="Uploaded logo" 
                      className="w-6 h-6 object-contain rounded"
                    />
                    <span className="text-xs text-gray-600">Logo uploaded for analysis</span>
                  </div>
                </div>
              )}
              
              <p className={`text-sm ${
                message.type === 'ai' 
                  ? 'text-blue-800' 
                  : 'text-gray-800'
              }`}>
                <strong>{message.type === 'ai' ? 'AI:' : 'You:'}</strong> {message.content}
              </p>
              
              {/* Logo Analysis Results for AI Messages */}
              {message.logoAnalysis && (
                <div className="mt-2 p-2 bg-blue-100 rounded border border-blue-200">
                  <p className="text-xs text-blue-700 font-semibold mb-1"> Logo Analysis Results:</p>
                  <div className="text-xs text-blue-600">
                    {message.logoAnalysis.colors && (
                      <p><strong>Colors:</strong> {message.logoAnalysis.colors.join(', ')}</p>
                    )}
                    {message.logoAnalysis.style && (
                      <p><strong>Style:</strong> {message.logoAnalysis.style}</p>
                    )}
                    {message.logoAnalysis.fonts && (
                      <p><strong>Fonts:</strong> {message.logoAnalysis.fonts.join(', ')}</p>
                    )}
                  </div>
                </div>
              )}
              
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
          {/* Logo Upload Section */}
          <div className="mb-4">
            <div className="flex items-center space-x-2 mb-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleLogoUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition"
              >
                📎 Upload Logo
              </button>
              {uploadedLogo && (
                <button
                  onClick={removeLogo}
                  className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition"
                >
                  ✕ Remove
                </button>
              )}
            </div>
            
            {/* Logo Preview */}
            {logoPreview && (
              <div className="mb-3 p-2 border border-gray-200 rounded bg-gray-50">
                <div className="flex items-center space-x-2">
                  <img 
                    src={logoPreview} 
                    alt="Logo preview" 
                    className="w-8 h-8 object-contain rounded"
                  />
                  <span className="text-sm text-gray-600">{uploadedLogo?.name}</span>
                </div>
              </div>
            )}
            

          </div>
          
          <div className="flex space-x-2">
            <input 
              type="text" 
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={uploadedLogo ? "Describe what you want to do with the logo..." : "Type your request here..."}
              disabled={isSending}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button 
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isSending}
              className={`px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed ${
                uploadedLogo 
                  ? 'bg-purple-500 text-white hover:bg-purple-600' 
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
                              {isSending ? 'Sending...' : (uploadedLogo ? 'Analyze Logo' : 'Send')}
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
              
              <button 
                onClick={() => navigate('/report', { 
                  state: { 
                    sessionData: {
                      sessionId: sessionId,
                      uiCodes: uiCodes,
                      projectInfo: {
                        template_name: selectedTemplate?.name || 'Unknown',
                        category: category,
                        created_at: new Date().toISOString()
                      }
                    }
                  } 
                })}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition"
                title="Generate custom report"
              >
                Generate Report
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