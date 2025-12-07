'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface DetailedInfo {
  game_state: {
    street: string
    pot_dollars: string
    hero_cards: string[]
    board_cards: string[]
  }
  players: Record<string, {
    name: string
    position: string
  }>
  pot_odds: {
    value: string
    calculation: string
  }
  hand_equity: {
    value: string
    calculation: string
  }
  implied_odds: {
    value: string
    calculation: string
  }
  fold_equity: {
    value: string
    calculation: string
  }
  expected_value: {
    value: string
    calculation: string
  }
  optimal_play: string
  action_history: string[]
}

export default function DetailsPage() {
  const router = useRouter()
  const [detailedInfo, setDetailedInfo] = useState<DetailedInfo | null>(null)
  const [action, setAction] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')
  const [capturedImage, setCapturedImage] = useState<string>('')

  useEffect(() => {
    // Load detailed info from localStorage
    const storedInfo = localStorage.getItem('poker_detailed_info')
    const storedAction = localStorage.getItem('poker_action')
    const storedPotSize = localStorage.getItem('poker_pot_size')
    const storedImage = localStorage.getItem('poker_captured_image')
    
    if (storedInfo) {
      setDetailedInfo(JSON.parse(storedInfo))
    }
    if (storedAction) {
      setAction(storedAction)
    }
    if (storedPotSize) {
      setPotSize(storedPotSize)
    }
    if (storedImage) {
      setCapturedImage(storedImage)
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

        {/* Captured Image */}
        {capturedImage && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-4 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">📸 Analyzed Table</h2>
            <img
              src={capturedImage}
              alt="Analyzed poker table"
              className="w-full rounded-xl"
            />
          </div>
        )}

        {/* Game State */}
        <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
          <h2 className="text-2xl font-bold text-emerald-400 mb-4">🎮 Game State</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Street:</span>
              <span className="font-bold capitalize">{detailedInfo.game_state.street}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Pot:</span>
              <span className="font-bold">{detailedInfo.game_state.pot_dollars} ({potSize})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Hero's Hand:</span>
              <span className="font-bold text-xl">
                {detailedInfo.game_state.hero_cards && detailedInfo.game_state.hero_cards.length > 0
                  ? detailedInfo.game_state.hero_cards.join(' ')
                  : 'N/A'}
              </span>
            </div>
            {detailedInfo.game_state.board_cards && detailedInfo.game_state.board_cards.length > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Board:</span>
                <span className="font-bold text-xl">{detailedInfo.game_state.board_cards.join(' ')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Players */}
        {detailedInfo.players && Object.keys(detailedInfo.players).length > 0 && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">👥 Players</h2>
            <div className="space-y-2">
              {Object.entries(detailedInfo.players).map(([position, playerData]) => (
                <div key={position} className="text-gray-200">
                  <span className="font-bold text-emerald-300">{playerData.name}</span>
                  <span className="text-gray-400"> is </span>
                  <span className="font-bold">{position}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pot Odds */}
        {detailedInfo.pot_odds && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-3">📊 Pot Odds</h2>
            <div className="text-3xl font-bold text-white mb-3">
              {typeof detailedInfo.pot_odds === 'object' ? detailedInfo.pot_odds.value : detailedInfo.pot_odds}
            </div>
            {typeof detailedInfo.pot_odds === 'object' && detailedInfo.pot_odds.calculation && (
              <p className="text-gray-300 leading-relaxed">{detailedInfo.pot_odds.calculation}</p>
            )}
          </div>
        )}

        {/* Hand Equity */}
        {detailedInfo.hand_equity && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-3">🎯 Hand Equity</h2>
            <div className="text-3xl font-bold text-white mb-3">
              {typeof detailedInfo.hand_equity === 'object' ? detailedInfo.hand_equity.value : detailedInfo.hand_equity}
            </div>
            {typeof detailedInfo.hand_equity === 'object' && detailedInfo.hand_equity.calculation && (
              <p className="text-gray-300 leading-relaxed">{detailedInfo.hand_equity.calculation}</p>
            )}
          </div>
        )}

        {/* Implied Odds */}
        {detailedInfo.implied_odds && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-3">💰 Implied Odds</h2>
            <div className="text-3xl font-bold text-white mb-3">
              {typeof detailedInfo.implied_odds === 'object' ? detailedInfo.implied_odds.value : detailedInfo.implied_odds}
            </div>
            {typeof detailedInfo.implied_odds === 'object' && detailedInfo.implied_odds.calculation && (
              <p className="text-gray-300 leading-relaxed">{detailedInfo.implied_odds.calculation}</p>
            )}
          </div>
        )}

        {/* Fold Equity */}
        {detailedInfo.fold_equity && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-3">🃏 Fold Equity</h2>
            <div className="text-3xl font-bold text-white mb-3">
              {typeof detailedInfo.fold_equity === 'object' ? detailedInfo.fold_equity.value : detailedInfo.fold_equity}
            </div>
            {typeof detailedInfo.fold_equity === 'object' && detailedInfo.fold_equity.calculation && (
              <p className="text-gray-300 leading-relaxed">{detailedInfo.fold_equity.calculation}</p>
            )}
          </div>
        )}

        {/* Expected Value */}
        {detailedInfo.expected_value && (
          <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-emerald-400 mb-3">💵 Expected Value (EV)</h2>
            <div className="text-3xl font-bold text-white mb-3">
              {typeof detailedInfo.expected_value === 'object' ? detailedInfo.expected_value.value : detailedInfo.expected_value}
            </div>
            {typeof detailedInfo.expected_value === 'object' && detailedInfo.expected_value.calculation && (
              <p className="text-gray-300 leading-relaxed">{detailedInfo.expected_value.calculation}</p>
            )}
          </div>
        )}

        {/* Optimal Play */}
        {detailedInfo.optimal_play && (
          <div className="mb-6 bg-gradient-to-br from-purple-900/50 to-indigo-900/50 backdrop-blur p-6 rounded-2xl border-2 border-purple-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-purple-300 mb-4">🎲 Optimal Play</h2>
            <p className="text-gray-200 leading-relaxed text-lg">{detailedInfo.optimal_play}</p>
          </div>
        )}

        {/* Action History (optional, smaller) */}
        {detailedInfo.action_history && detailedInfo.action_history.length > 0 && (
          <div className="mb-6 bg-gray-800/70 backdrop-blur p-4 rounded-2xl border border-gray-700/30 shadow-lg">
            <h3 className="text-lg font-bold text-gray-400 mb-3">📋 Action History</h3>
            <div className="space-y-1">
              {detailedInfo.action_history.map((action, idx) => (
                <div key={idx} className="text-gray-300 text-sm">• {action}</div>
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
