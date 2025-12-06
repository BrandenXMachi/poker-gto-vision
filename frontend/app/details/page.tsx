'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface DetailedInfo {
  game_state: {
    street: string
    pot_dollars: string
    board_cards: string[]
  }
  reasoning: string
  range_analysis: string
  ev_calculation: string
  action_history: string[]
  stack_sizes: Record<string, number>
  alternative_lines: string[]
}

export default function DetailsPage() {
  const router = useRouter()
  const [detailedInfo, setDetailedInfo] = useState<DetailedInfo | null>(null)
  const [action, setAction] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')

  useEffect(() => {
    // Load detailed info from localStorage
    const storedInfo = localStorage.getItem('poker_detailed_info')
    const storedAction = localStorage.getItem('poker_action')
    const storedPotSize = localStorage.getItem('poker_pot_size')
    
    if (storedInfo) {
      setDetailedInfo(JSON.parse(storedInfo))
    }
    if (storedAction) {
      setAction(storedAction)
    }
    if (storedPotSize) {
      setPotSize(storedPotSize)
    }
  }, [])

  if (!detailedInfo) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl mb-4">No analysis data available</p>
          <button
            onClick={() => router.push('/')}
            className="px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-xl font-bold text-lg transition-all shadow-lg"
          >
            ← Back to Camera
          </button>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-gray-900 text-white">
      <div className="container mx-auto max-w-4xl px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-xl font-bold transition-all"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 via-emerald-500 to-teal-400 bg-clip-text text-transparent">
            Detailed Analysis
          </h1>
          <div className="w-24"></div> {/* Spacer for centering */}
        </div>

        {/* Action Summary */}
        <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 text-white p-6 rounded-2xl mb-6 shadow-2xl border-2 border-emerald-400/30">
          <div className="text-3xl font-bold text-center">
            {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
          </div>
        </div>

        {/* Game State */}
        <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
          <h2 className="text-2xl font-bold text-emerald-400 mb-4">Game State</h2>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Street:</span>
              <span className="font-bold capitalize">{detailedInfo.game_state.street}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Pot:</span>
              <span className="font-bold">{detailedInfo.game_state.pot_dollars} ({potSize})</span>
            </div>
            {detailedInfo.game_state.board_cards.length > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Board:</span>
                <span className="font-bold">{detailedInfo.game_state.board_cards.join(' ')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Reasoning */}
        {detailedInfo.reasoning && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">💡 Reasoning</h2>
            <p className="text-gray-200 leading-relaxed">{detailedInfo.reasoning}</p>
          </div>
        )}

        {/* Range Analysis */}
        {detailedInfo.range_analysis && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">🎯 Range Analysis</h2>
            <p className="text-gray-200 leading-relaxed">{detailedInfo.range_analysis}</p>
          </div>
        )}

        {/* EV Calculation */}
        {detailedInfo.ev_calculation && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">💰 EV Breakdown</h2>
            <p className="text-gray-200 leading-relaxed">{detailedInfo.ev_calculation}</p>
          </div>
        )}

        {/* Action History */}
        {detailedInfo.action_history && detailedInfo.action_history.length > 0 && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">📋 Action History</h2>
            <div className="space-y-2">
              {detailedInfo.action_history.map((action, idx) => (
                <div key={idx} className="text-gray-200">• {action}</div>
              ))}
            </div>
          </div>
        )}

        {/* Alternative Lines */}
        {detailedInfo.alternative_lines && detailedInfo.alternative_lines.length > 0 && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">🔀 Alternative Lines</h2>
            <div className="space-y-2">
              {detailedInfo.alternative_lines.map((line, idx) => (
                <div key={idx} className="text-gray-200">• {line}</div>
              ))}
            </div>
          </div>
        )}

        {/* Bottom Back Button */}
        <div className="flex justify-center mt-8">
          <button
            onClick={() => router.push('/')}
            className="px-10 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            ← Back to Camera
          </button>
        </div>
      </div>
    </main>
  )
}
