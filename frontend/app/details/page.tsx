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
  players?: Record<string, {
    name: string
    position: string
    stack?: string
    vpip?: string
  }>
  reasoning?: string
  pot_odds?: {
    value: string
    calculation: string
  } | string
  hand_equity?: {
    value: string
    calculation: string
  } | string
  implied_odds?: {
    value: string
    calculation: string
  } | string
  fold_equity?: {
    value: string
    calculation: string
  } | string
  expected_value?: {
    value: string
    calculation: string
  } | string
  optimal_play?: string
  action_history?: string[]
}

export default function DetailsPage() {
  const router = useRouter()
  const [detailedInfo, setDetailedInfo] = useState<DetailedInfo | null>(null)
  const [action, setAction] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')
  const [capturedImage, setCapturedImage] = useState<string>('')
  const [aiMode, setAiMode] = useState<string>('hybrid')
  const [isLoading, setIsLoading] = useState(true)

  // Helper function to convert card text to symbols
  const convertCardToSymbol = (card: string): string => {
    // If card is already in symbol format (e.g., "K♦"), return as is
    if (card.length <= 3 && /[♠♥♦♣]/.test(card)) {
      return card
    }
    
    // Parse card like "King of Diamonds" or "Kd"
    const rankMap: Record<string, string> = {
      'ace': 'A', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
      'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': 'T',
      'jack': 'J', 'queen': 'Q', 'king': 'K',
      'a': 'A', 't': 'T', 'j': 'J', 'q': 'Q', 'k': 'K'
    }
    
    const suitMap: Record<string, string> = {
      'spades': '♠', 'hearts': '♥', 'diamonds': '♦', 'clubs': '♣',
      's': '♠', 'h': '♥', 'd': '♦', 'c': '♣'
    }
    
    const cardLower = card.toLowerCase().trim()
    
    // Try to match "Rank of Suit" pattern
    const match = cardLower.match(/(\w+)\s+of\s+(\w+)/)
    if (match) {
      const rank = rankMap[match[1]] || match[1].toUpperCase()
      const suit = suitMap[match[2]] || ''
      return rank + suit
    }
    
    // Try to match "Rs" pattern (e.g., "Kd", "As")
    if (cardLower.length === 2) {
      const rank = rankMap[cardLower[0]] || cardLower[0].toUpperCase()
      const suit = suitMap[cardLower[1]] || ''
      return rank + suit
    }
    
    return card // Return original if can't parse
  }

  const convertCards = (cards: string[]): string => {
    return cards.map(convertCardToSymbol).join(' ')
  }

  useEffect(() => {
    // Load detailed info from localStorage
    const storedInfo = localStorage.getItem('poker_detailed_info')
    const storedAction = localStorage.getItem('poker_action')
    const storedPotSize = localStorage.getItem('poker_pot_size')
    const storedImage = localStorage.getItem('poker_captured_image')
    const storedAiMode = localStorage.getItem('poker_ai_mode')
    
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
    if (storedAiMode) {
      setAiMode(storedAiMode)
    }
    
    setIsLoading(false)
  }, [])

  const isGptMode = aiMode === 'gpt' || aiMode === 'hybrid'

  if (isLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl">Loading analysis...</p>
        </div>
      </main>
    )
  }

  if (!detailedInfo) {
    return (
      <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 text-white flex items-center justify-center">
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
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 text-white">
      <div className="container mx-auto max-w-4xl px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-xl font-bold transition-all"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-400 to-sky-400 bg-clip-text text-transparent">
            {isGptMode ? '🧠 GPT Analysis' : '⚡ Gemini Analysis'}
          </h1>
          <div className="w-24"></div> {/* Spacer for centering */}
        </div>

        {/* Action Summary */}
        <div className={`text-white p-6 rounded-2xl mb-6 shadow-2xl ${
          isGptMode 
            ? 'bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 border-2 border-blue-400/30'
            : 'bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 border-2 border-emerald-400/30'
        }`}>
          <div className="text-3xl font-bold text-center">
            {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
          </div>
        </div>

        {/* Captured Image */}
        {capturedImage && (
          <div className={`mb-6 bg-gray-800/90 backdrop-blur p-4 rounded-2xl shadow-xl ${
            isGptMode ? 'border-2 border-blue-500/30' : 'border-2 border-emerald-500/30'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${isGptMode ? 'text-blue-400' : 'text-emerald-400'}`}>
              📸 Analyzed Table
            </h2>
            <img
              src={capturedImage}
              alt="Analyzed poker table"
              className="w-full rounded-xl"
            />
          </div>
        )}

        {/* Game State */}
        <div className={`mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl shadow-xl ${
          isGptMode ? 'border-2 border-blue-500/30' : 'border-2 border-emerald-500/30'
        }`}>
          <h2 className={`text-2xl font-bold mb-4 ${isGptMode ? 'text-blue-400' : 'text-emerald-400'}`}>
            🎮 Game State
          </h2>
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
              <span className="text-gray-400">Hero&apos;s Hand:</span>
              <span className="font-bold text-xl">
                {detailedInfo.game_state.hero_cards && detailedInfo.game_state.hero_cards.length > 0
                  ? convertCards(detailedInfo.game_state.hero_cards)
                  : 'N/A'}
              </span>
            </div>
            {detailedInfo.game_state.board_cards && detailedInfo.game_state.board_cards.length > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-400">Board:</span>
                <span className="font-bold text-xl">{convertCards(detailedInfo.game_state.board_cards)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Players - Only show for GPT/Hybrid/Deep modes, not for Odds mode */}
        {isGptMode && detailedInfo.players && Object.keys(detailedInfo.players).length > 0 && (
          <div className={`mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl shadow-xl ${
            isGptMode ? 'border-2 border-blue-500/30' : 'border-2 border-emerald-500/30'
          }`}>
            <h2 className={`text-2xl font-bold mb-4 ${isGptMode ? 'text-blue-400' : 'text-emerald-400'}`}>
              👥 Active Players
            </h2>
            <div className="space-y-3">
              {Object.entries(detailedInfo.players).map(([position, playerData]) => (
                <div key={position} className="bg-gray-700/50 p-3 rounded-lg">
                  <div className="text-gray-200">
                    <span className={`font-bold ${isGptMode ? 'text-blue-300' : 'text-emerald-300'}`}>
                      {playerData.name}
                    </span>
                    <span className="text-gray-400"> at </span>
                    <span className="font-bold">{position}</span>
                  </div>
                  {(playerData.stack || playerData.vpip) && (
                    <div className="text-sm text-gray-400 mt-1">
                      {playerData.stack && <span>Stack: {playerData.stack}</span>}
                      {playerData.stack && playerData.vpip && <span> • </span>}
                      {playerData.vpip && <span>VPIP: {playerData.vpip}</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* GPT/Hybrid Mode: Reasoning */}
        {isGptMode && detailedInfo.reasoning && (
          <div className="mb-6 bg-gradient-to-br from-purple-900/50 to-indigo-900/50 backdrop-blur p-6 rounded-2xl border-2 border-purple-500/30 shadow-xl">
            <h2 className="text-2xl font-bold text-purple-300 mb-4">💡 GPT Reasoning</h2>
            <p className="text-gray-200 leading-relaxed text-lg">{detailedInfo.reasoning}</p>
          </div>
        )}

        {/* Gemini Mode: 5 Metrics */}
        {!isGptMode && (
          <>
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
          </>
        )}

        {/* Action History */}
        {detailedInfo.action_history && detailedInfo.action_history.length > 0 && (
          <div className="mb-6 bg-gray-800/70 backdrop-blur p-4 rounded-2xl border border-gray-700/30 shadow-lg">
            <h3 className="text-lg font-bold text-gray-400 mb-3">📋 Action History</h3>
            <div className="space-y-1">
              {detailedInfo.action_history.map((historyAction, idx) => (
                <div key={idx} className="text-gray-300 text-sm">• {historyAction}</div>
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
