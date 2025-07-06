import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="h-screen w-56 bg-gray-900 text-white flex flex-col p-4 space-y-4">
      <h2 className="text-2xl font-bold mb-8">AI Mockup Tool</h2>
      <Link to="/" className="hover:bg-gray-700 rounded px-3 py-2">Main Page</Link>
      <Link to="/chat" className="hover:bg-gray-700 rounded px-3 py-2">Chat</Link>
      <Link to="/ui-recommendation" className="hover:bg-gray-700 rounded px-3 py-2">UI Recommendation</Link>
      <Link to="/created" className="hover:bg-gray-700 rounded px-3 py-2">Created</Link>
    </div>
  );
}

function MainPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h1 className="text-3xl font-bold mb-6">Welcome to the AI Mockup Tool</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-xl">
        <Link to="/chat" className="bg-blue-500 text-white rounded-lg p-6 text-center shadow hover:bg-blue-600 transition">Go to Chat</Link>
        <Link to="/ui-recommendation" className="bg-green-500 text-white rounded-lg p-6 text-center shadow hover:bg-green-600 transition">UI Recommendations</Link>
        <Link to="/created" className="bg-purple-500 text-white rounded-lg p-6 text-center shadow hover:bg-purple-600 transition">View Created Pages</Link>
      </div>
    </div>
  );
}

function ChatPage() {
  return (
    <div className="flex flex-col h-full p-8">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>
      <div className="flex-1 bg-gray-100 rounded-lg p-4 mb-4">Chat feature coming soon...</div>
      <input className="border rounded p-2 w-full" placeholder="Type your message..." disabled />
    </div>
  );
}

function UIRecommendationPage() {
  // Placeholder images, replace with real UI recommendations later
  const images = [
    "https://via.placeholder.com/300x180?text=UI+1",
    "https://via.placeholder.com/300x180?text=UI+2",
    "https://via.placeholder.com/300x180?text=UI+3",
    "https://via.placeholder.com/300x180?text=UI+4",
  ];
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">UI Recommendations</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {images.map((src, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer">
            <img src={src} alt={`UI ${idx + 1}`} className="rounded-t-lg w-full h-40 object-cover" />
            <div className="p-4 text-center">UI Template {idx + 1}</div>
          </div>
        ))}
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
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/ui-recommendation" element={<UIRecommendationPage />} />
            <Route path="/created" element={<CreatedPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
