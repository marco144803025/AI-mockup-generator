import React, { useState } from 'react';

function EditorPage() {
  const [viewMode, setViewMode] = useState('preview'); // 'preview' or 'code'

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Chat Interface Section */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-bold">AI Editor Chat</h2>
          <p className="text-sm text-gray-600">Ask me to modify your UI</p>
        </div>
        
        {/* Chat Messages Area */}
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="bg-blue-50 rounded-lg p-3 mb-4">
            <p className="text-sm text-blue-800">
              <strong>AI:</strong> I'm ready to help you edit your UI! What would you like to change?
            </p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <p className="text-sm text-gray-800">
              <strong>You:</strong> Make the button red
            </p>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-3 mb-4">
            <p className="text-sm text-blue-800">
              <strong>AI:</strong> I've changed the button color to red. How does that look?
            </p>
          </div>
        </div>
        
        {/* Chat Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input 
              type="text" 
              placeholder="Type your request here..."
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600">
              Send
            </button>
          </div>
        </div>
      </div>

      {/* UI Preview/Code Section */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar with Toggle Buttons */}
        <div className="bg-white border-b border-gray-200 p-4">
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
        </div>

        {/* Content Area */}
        <div className="flex-1 p-4">
          {viewMode === 'preview' ? (
            /* Preview Iframe */
            <div className="bg-white rounded-lg shadow-lg h-full">
              <iframe 
                id="preview-frame"
                className="w-full h-full border-0 rounded-lg"
                title="UI Preview"
                srcDoc={`
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI Preview</title>
  <style>
    body {
      margin: 0;
      padding: 20px;
      font-family: Arial, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .preview-container {
      background: white;
      padding: 40px;
      border-radius: 10px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.2);
      text-align: center;
      max-width: 400px;
      width: 100%;
    }
    .preview-title {
      font-size: 2em;
      color: #333;
      margin-bottom: 10px;
    }
    .preview-subtitle {
      color: #666;
      margin-bottom: 30px;
    }
    .preview-button {
      background: #4CAF50;
      color: white;
      border: none;
      padding: 12px 30px;
      border-radius: 5px;
      font-size: 16px;
      cursor: pointer;
      transition: background 0.3s;
    }
    .preview-button:hover {
      background: #45a049;
    }
    .placeholder-text {
      color: #999;
      font-style: italic;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <div class="preview-container">
    <h1 class="preview-title">Welcome!</h1>
    <p class="preview-subtitle">This is a placeholder preview. Your UI will appear here.</p>
    <button class="preview-button" id="demo-button">Click Me!</button>
    <p class="placeholder-text">Template content will be loaded from MongoDB</p>
  </div>
  
  <script>
    // Demo interaction
    document.getElementById('demo-button').addEventListener('click', function() {
      this.style.background = '#ff4444';
      this.textContent = 'Button Clicked!';
    });
  </script>
</body>
</html>
                `}
              />
            </div>
          ) : (
            /* Code View */
            <div className="bg-white rounded-lg shadow-lg h-full p-4">
              <div className="bg-gray-100 rounded p-4 h-full overflow-auto">
                <pre className="text-sm text-gray-700">
{`// HTML Code
<!DOCTYPE html>
<html>
<head>
  <title>UI Preview</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="preview-container">
    <h1 class="preview-title">Welcome!</h1>
    <p class="preview-subtitle">This is a placeholder preview.</p>
    <button class="preview-button" id="demo-button">Click Me!</button>
  </div>
</body>
</html>

// CSS Code
body {
  margin: 0;
  padding: 20px;
  font-family: Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-container {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.preview-button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 12px 30px;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s;
}`}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default EditorPage; 