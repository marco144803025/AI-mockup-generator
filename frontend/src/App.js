import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import UIRecommendationPage from "./UIRecommendationPage";
import ChatScreen from "./ChatScreen";

function Sidebar() {
  return (
    <div className="h-screen w-55 bg-white text-black flex flex-col p-4 space-y-4">
      <h2 className="text-2xl font-bold mb-8">Launchpad AI</h2>
      <Link to="/" className="hover:bg-purple-200 rounded px-3 py-2">Main Page</Link>
      <Link to="/chat" className="hover:bg-purple-200 rounded px-3 py-2">AI UI Workflow</Link>
      <Link to="/ui-recommendation" className="hover:bg-purple-200 rounded px-3 py-2">UI Recommendation</Link>
      <Link to="/created" className="hover:bg-purple-200 rounded px-3 py-2">Created</Link>
    </div>
  );
}

function MainPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h1 className="text-3xl font-bold mb-6">Welcome to Launchpad AI</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-xl">
        <Link to="/chat" className="bg-blue-500 text-white rounded-lg p-6 text-center shadow hover:bg-blue-600 transition">AI UI Workflow</Link>
        <Link to="/ui-recommendation" className="bg-purple-500 text-white rounded-lg p-6 text-center shadow hover:bg-purple-600 transition">UI Recommendations</Link>
        <Link to="/created" className="bg-orange-500 text-white rounded-lg p-6 text-center shadow hover:bg-orange-600 transition">View Created Pages</Link>
      </div>
    </div>
  );
}

function CreatedPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Created Pages</h1>
      <div className="bg-gray-100 rounded-lg p-4">No pages created yet.</div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 bg-gray-50 overflow-auto">
          <Routes>
            <Route path="/" element={<MainPage />} />
            <Route path="/chat" element={<ChatScreen />} />
            <Route path="/ui-recommendation" element={<UIRecommendationPage />} />
            <Route path="/created" element={<CreatedPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
