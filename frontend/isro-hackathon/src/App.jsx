import { useState } from 'react'
import Navbar from './components/Navbar'
import SpaceBG from './components/SpaceBG';
import KnowledgeGraph from './components/KnowledgeGraph';
import Chatbox from './components/Chatbox';
import './App.css'
import { Users } from 'lucide-react';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  return (
    <>
      <div className='min-h-screen bg-slate-900 text-white relative'>
        <SpaceBG />
        <Navbar currentPage={currentPage} setCurrentPage={setCurrentPage} />
        <main className="pt-20 px-6 pb-6 relative z-10">
          {currentPage === 'home' ? (
            <div className="max-w-7xl mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent mb-4">
                  Satellite Data Archive Center
                </h1>
                <p className="text-gray-300 text-lg max-w-2xl mx-auto">
                  Explore our comprehensive satellite data archive through intelligent search and interactive knowledge graphs
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-200px)]">
                <div className="h-full">
                  <Chatbox />
                </div>
                <div className="h-full">
                  <KnowledgeGraph />
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              <div className="text-center mb-8">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 bg-clip-text text-transparent mb-4">
                  Admin Portal
                </h1>
                <p className="text-gray-300 text-lg">
                  Administrative tools and system management
                </p>
              </div>

              <div className="bg-slate-800/50 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-500/10 backdrop-blur-sm p-8">
                <div className="text-center">
                  <Users className="w-16 h-16 text-cyan-400 mx-auto mb-4" />
                  <h2 className="text-2xl font-semibold text-cyan-400 mb-4">Admin Features</h2>
                  <p className="text-gray-300">
                    Administrative features will be implemented here. Connect this to your Flask backend for system management capabilities.
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  )
}

export default App
