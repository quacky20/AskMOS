import React from 'react'
import { Satellite, Users, Home } from 'lucide-react';

function Navbar({ currentPage, setCurrentPage }) {
    return (
        <>
            <nav className="fixed top-0 left-0 right-0 z-50 bg-slate-900/80 backdrop-blur-lg border-b border-cyan-500/30">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <Satellite className="w-8 h-8 text-cyan-400 animate-pulse" />
                            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                                AskMOS
                            </h1>
                        </div>
                        <div className="flex items-center space-x-8">
                            <button
                                onClick={() => setCurrentPage('home')}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-300 ${currentPage === 'home'
                                        ? 'bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/25'
                                        : 'text-gray-300 hover:text-cyan-400 hover:bg-cyan-500/10'
                                    }`}
                            >
                                <Home className="w-4 h-4" />
                                <span>Home</span>
                            </button>
                            {/* <button
                                onClick={() => setCurrentPage('admin')}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-300 ${currentPage === 'admin'
                                        ? 'bg-cyan-500/20 text-cyan-400 shadow-lg shadow-cyan-500/25'
                                        : 'text-gray-300 hover:text-cyan-400 hover:bg-cyan-500/10'
                                    }`}
                            >
                                <Users className="w-4 h-4" />
                                <span>For Admins</span>
                            </button> */}
                        </div>
                    </div>
                </div>
            </nav>
        </>
    )
}

export default Navbar