import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import ChatScreen from "./ChatScreen";
import EditorPage from "./EditorPage";
import ReportPage from "./ReportPage";

function Sidebar({ isCollapsed, toggleSidebar }) {
  return (
    <div className={`h-screen bg-white text-black flex flex-col transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-55'
    } p-4 space-y-4`}>
      {/* Toggle Button */}
      <button 
        onClick={toggleSidebar}
        className="self-end mb-4 p-2 hover:bg-gray-100 rounded"
      >
        {isCollapsed ? '→' : '←'}
      </button>
      
      {/* Logo/Title */}
      <h2 className={`font-bold mb-8 ${isCollapsed ? 'text-center text-sm' : 'text-2xl'}`}>
        {isCollapsed ? 'LA' : 'Launchpad AI'}
      </h2>
      
      {/* Navigation Links */}
      <Link to="/" className={`hover:bg-purple-200 rounded px-3 py-2 ${isCollapsed ? 'text-center text-xs' : ''}`}>
        {isCollapsed ? '🏠' : 'Main Page'}
      </Link>
      <Link to="/chat" className={`hover:bg-purple-200 rounded px-3 py-2 ${isCollapsed ? 'text-center text-xs' : ''}`}>
        {isCollapsed ? '🤖' : 'AI UI Workflow'}
      </Link>
      <Link to="/editor" className={`hover:bg-purple-200 rounded px-3 py-2 ${isCollapsed ? 'text-center text-xs' : ''}`}>
        {isCollapsed ? '⚡' : 'UI Editor'}
      </Link>
    </div>
  );
}

function MainPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h1 className="text-3xl font-bold mb-6">Welcome to Launchpad AI</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-xl">
        <Link to="/chat" className="bg-blue-500 text-white rounded-lg p-6 text-center shadow hover:bg-blue-600 transition">AI UI Workflow</Link>
        <Link to="/editor" className="bg-green-500 text-white rounded-lg p-6 text-center shadow hover:bg-green-600 transition">UI Editor (Phase 2)</Link>
      </div>
    </div>
  );
}

function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true); // Default collapsed

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <Router>
      <div className="flex h-screen">
        <Sidebar isCollapsed={isSidebarCollapsed} toggleSidebar={toggleSidebar} />
        <div className="flex-1 bg-gray-50 overflow-auto">
          <Routes>
            <Route path="/" element={<MainPage />} />
            <Route path="/chat" element={<ChatScreen />} />
            <Route path="/editor" element={<EditorPage />} />
            <Route path="/report" element={<ReportPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
