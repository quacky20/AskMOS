import React, { useState } from 'react'
import { Globe } from 'lucide-react';

function KnowledgeGraph() {
    const [graphUrl, setGraphUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadGraph = () => {
        setIsLoading(true);
        setError(null);

        // Simulate loading graph from backend
        setTimeout(() => {
            // In real implementation, this would be the URL to your generated HTML file
            setGraphUrl('/neo4j_graph.html');
            setIsLoading(false);
            // setError("Graph will load here when connected to your Flask backend");
        }, 1000);
    };

    return (
        <div className="h-[70vh] flex flex-col bg-slate-800/50 rounded-xl border border-purple-500/30 shadow-2xl shadow-purple-500/10 backdrop-blur-sm">
            <div className="p-4 border-b border-purple-500/30 bg-gradient-to-r from-slate-800/80 to-slate-700/80 rounded-t-xl">
                <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-purple-400 flex items-center space-x-2">
                        <Globe className="w-5 h-5" />
                        <span>Knowledge Graph</span>
                    </h2>
                    <button
                        onClick={loadGraph}
                        disabled={isLoading}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-colors duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 text-sm"
                    >
                        {isLoading ? 'Loading...' : 'Load Graph'}
                    </button>
                </div>
            </div>

            <div className="flex-1 relative">
                {isLoading ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                            <div className="w-16 h-16 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mb-4"></div>
                            <p className="text-purple-400">Loading knowledge graph...</p>
                        </div>
                    </div>
                ) : error ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center p-8">
                            <Globe className="w-16 h-16 text-purple-400 mx-auto mb-4 opacity-50" />
                            <p className="text-purple-400">{error}</p>
                            <p className="text-gray-400 text-sm mt-2">Connect to your Flask backend to display the graph</p>
                        </div>
                    </div>
                ) : graphUrl ? (
                    <iframe
                        src={graphUrl}
                        className="w-full h-full rounded-b-xl"
                        title="Knowledge Graph"
                        onLoad={() => {setIsLoading(false)}}
                        scrolling='no'
                    />
                ) : (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center p-8">
                            <Globe className="w-16 h-16 text-purple-400 mx-auto mb-4 opacity-50" />
                            <p className="text-purple-400">Click "Load Graph" to visualize the knowledge network</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default KnowledgeGraph