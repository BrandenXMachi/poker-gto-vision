'use client'

import { useEffect, useRef, useState } from 'react'
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

export default function Home() {
  const router = useRouter()
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string>('')
  const [capturedImage, setCapturedImage] = useState<string>('')
  const [isInPosition, setIsInPosition] = useState<boolean>(true)
  const [selectedBlinds, setSelectedBlinds] = useState<string>('0.02/0.05')
  const [villainPositionPreflop, setVillainPositionPreflop] = useState<string>('UTG')
  const [selectedPosition, setSelectedPosition] = useState<string>('BTN')
  const [aiMode, setAiMode] = useState<'odds' | 'flop' | 'preflop'>('preflop')
  const [isOpenRaise, setIsOpenRaise] = useState<boolean>(false)
  
  // Flop Mode specific states
  const [flopHeroPosition, setFlopHeroPosition] = useState<string>('IP')  // "IP" or "OOP"
  const [flopVillainPosition, setFlopVillainPosition] = useState<string>('BTN')  // Position
  const [flopPreflopAction, setFlopPreflopAction] = useState<string>('villain_called')  // Preflop action
  
  // Context inheritance for mode transitions
  const [inheritedContext, setInheritedContext] = useState<{
    fromMode: string
    heroPosition: string
    villainPosition: string
    preflopAction: string
    preflopRecommendation: string
  } | null>(null)
  
  // Main display info
  const [action, setAction] = useState<string>('')
  const [potOdds, setPotOdds] = useState<string>('')
  const [handEquity, setHandEquity] = useState<string>('')
  const [impliedOdds, setImpliedOdds] = useState<string>('')
  const [foldEquity, setFoldEquity] = useState<string>('')
  const [expectedValue, setExpectedValue] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')
  const [reasoning, setReasoning] = useState<string>('')
  
  // Card displays
  const [heroCards, setHeroCards] = useState<string[]>([])
  const [boardCards, setBoardCards] = useState<string[]>([])
  const [street, setStreet] = useState<string>('')
  
  // Detailed info for navigation to details page
  const [detailedInfo, setDetailedInfo] = useState<DetailedInfo | null>(null)

  // Initialize speech synthesis
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
    }
  }, [])

  // Text-to-Speech function
  const speak = (text: string) => {
    if (synthRef.current) {
      synthRef.current.cancel()
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0
      synthRef.current.speak(utterance)
    }
  }

  // Smart action mapping: Preflop recommendation → Flop preflop action
  const mapPreflopToFlopAction = (preflopAction: string): string => {
    const actionLower = preflopAction.toLowerCase()
    
    // If we 3-bet in preflop → villain called our 3-bet
    if (actionLower.includes('3-bet') || actionLower.includes('3bet')) {
      return 'villain_called_3bet'
    }
    
    // If we called villain's raise → villain opened
    if (actionLower.includes('call')) {
      return 'villain_opened'
    }
    
    // If we raised/opened → villain called our open (SRP)
    if (actionLower.includes('raise') || actionLower.includes('open')) {
      return 'villain_called'
    }
    
    // Default fallback
    return 'villain_called'
  }

  // Determine IP/OOP from positions
  const determineIPorOOP = (heroPos: string, villainPos: string): string => {
    const positions = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
    const heroIndex = positions.indexOf(heroPos)
    const villainIndex = positions.indexOf(villainPos)
    
    // If hero is later in position order, they're IP
    return heroIndex > villainIndex ? 'IP' : 'OOP'
  }

  // Continue to Flop mode with context
  const continueToFlop = () => {
    if (!action) return
    
    // Check if we folded - can't continue
    if (action.toLowerCase().includes('fold')) {
      setError('Cannot continue after folding')
      return
    }
    
    // Check if we're opening (no villain identified yet)
    const isOpeningAction = action.toLowerCase().includes('raise') || action.toLowerCase().includes('open')
    
    if (isOpenRaise || !villainPositionPreflop || isOpeningAction) {
      // We opened, no villain yet - show full inputs in flop mode
      setAiMode('flop')
      setInheritedContext(null)
      setCapturedImage('')
      setAction('')
      startCamera()
    } else {
      // We have a villain - pass context
      const flopAction = mapPreflopToFlopAction(action)
      const ipOrOop = determineIPorOOP(selectedPosition, villainPositionPreflop)
      
      setInheritedContext({
        fromMode: 'preflop',
        heroPosition: ipOrOop,
        villainPosition: villainPositionPreflop,
        preflopAction: flopAction,
        preflopRecommendation: action
      })
      
      // Set flop mode states from inherited context
      setFlopHeroPosition(ipOrOop)
      setFlopVillainPosition(villainPositionPreflop)
      setFlopPreflopAction(flopAction)
      
      setAiMode('flop')
      setCapturedImage('')
      setAction('')
      startCamera()
    }
  }

  // Continue to Odds mode
  const continueToOdds = () => {
    if (!action) return
    
    // Check if we folded - can't continue
    if (action.toLowerCase().includes('fold')) {
      setError('Cannot continue after folding')
      return
    }
    
    setAiMode('odds')
    setCapturedImage('')
    setAction('')
    setInheritedContext(null) // Odds mode doesn't use context
    startCamera()
  }

  // Reset inherited context (manual input mode)
  const resetToManualInput = () => {
    setInheritedContext(null)
  }

  // Start camera
  const startCamera = async () => {
    try {
      setError('')
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        setIsCameraActive(true)
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to access camera'
      setError(errorMsg)
      console.error('Camera error:', err)
    }
  }

  // Stop camera
  const stopCamera = () => {
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach(track => track.stop())
      videoRef.current.srcObject = null
      setIsCameraActive(false)
      setAction('')
    }

    if (synthRef.current) {
      synthRef.current.cancel()
    }
  }

  // Handle position click - auto capture and analyze (Flash Mode only)
  const handlePositionClick = async (position: string) => {
    if (isAnalyzing) return
    
    setSelectedPosition(position)
    await captureAndAnalyze(position)  // Pass position directly to avoid state timing issues
  }

  // Handle Deep Mode capture button
  const handleDeepCapture = async () => {
    if (isAnalyzing) return
    await captureAndAnalyze()
  }

  // Capture photo and analyze
  const captureAndAnalyze = async (overridePosition?: string) => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera not ready')
      return
    }
    
    // Use override position if provided, otherwise use current state
    const positionToUse = overridePosition || selectedPosition
    
    const video = videoRef.current
    const canvas = canvasRef.current
    
    // Check if video is ready
    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
      setError('Video not ready. Please wait a moment and try again.')
      return
    }
    
    if (video.videoWidth === 0 || video.videoHeight === 0) {
      setError('Video dimensions invalid. Please restart camera.')
      return
    }
    
    setIsAnalyzing(true)
    setError('')
    setAction('')

    try {
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('Could not get canvas context')
      
      ctx.drawImage(video, 0, 0)
      
      const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9)
      setCapturedImage(imageDataUrl)
      
      // Stop camera during analysis
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
        tracks.forEach(track => track.stop())
        videoRef.current.srcObject = null
        setIsCameraActive(false)
      }
      
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (blob) => blob ? resolve(blob) : reject(new Error('Failed to create blob')),
          'image/jpeg',
          0.9
        )
      })

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      
      const formData = new FormData()
      formData.append('image', blob, 'poker_table.jpg')
      
      // For Flop Mode, pass manual inputs
      if (aiMode === 'flop') {
        formData.append('hero_position', flopHeroPosition)  // "IP" or "OOP"
        formData.append('villain_position', flopVillainPosition)  // "UTG", "MP", etc.
        formData.append('villain_action', flopPreflopAction)  // "villain_called", etc.
        formData.append('blinds', selectedBlinds)
      } else if (aiMode === 'preflop') {
        // Preflop Mode - pass hero position, villain position, blinds, and open raise flag
        formData.append('position', positionToUse)
        formData.append('villain_position', isOpenRaise ? 'NONE' : villainPositionPreflop)
        formData.append('blinds', selectedBlinds)
        formData.append('is_open_raise', isOpenRaise ? 'true' : 'false')
      } else {
        // Flash Mode
        formData.append('position', positionToUse)
        formData.append('blinds', selectedBlinds)
      }
      
      formData.append('ai_mode', aiMode)

      console.log(`📸 Sending image to ${backendUrl}/analyze with AI mode: ${aiMode}`)
      
      const response = await fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      console.log('✅ Analysis result:', data)

      if (data.success && data.recommendation) {
        const rec = data.recommendation
        setAction(rec.action)
        setPotOdds(rec.pot_odds?.value || rec.pot_odds || 'N/A')
        setHandEquity(rec.hand_equity?.value || rec.hand_equity || 'N/A')
        setImpliedOdds(rec.implied_odds?.value || rec.implied_odds || 'N/A')
        setFoldEquity(rec.fold_equity?.value || rec.fold_equity || 'N/A')
        setExpectedValue(rec.expected_value?.value || rec.expected_value || 'N/A')
        setPotSize(rec.pot_size || 'N/A')
        setReasoning(rec.reasoning || '')
        setDetailedInfo(data.detailed_info || null)
        
        // Extract card data from response
        if (data.extracted_data) {
          setHeroCards(data.extracted_data.hero_cards || [])
          setBoardCards(data.extracted_data.board_cards || [])
          setStreet(data.extracted_data.street || '')
        }
        
        // Speak the action for all modes
        speak(rec.action)
      } else if (data.hero_turn === false) {
        setError('Not hero\'s turn detected. Try capturing when action is on you.')
      } else {
        setError(data.message || 'Analysis failed. Please try again.')
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Analysis failed'
      setError(errorMsg)
      console.error('Analysis error:', err)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Reset and prepare for new capture
  const captureAgain = () => {
    setCapturedImage('')
    setAction('')
    setError('')
    startCamera()
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-indigo-950 text-white flex">
      <div className="flex-1 px-4 py-6">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-8">
            <h1 className="text-5xl font-extrabold bg-gradient-to-r from-blue-400 via-cyan-400 to-sky-400 bg-clip-text text-transparent mb-2">
              🎰 Poker Strategy
            </h1>
          </div>
          
          {/* Mode Selector - Show when camera is active */}
          {isCameraActive && !capturedImage && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-purple-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-purple-400 mb-4">
                🎯 Analysis Mode
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => setAiMode('preflop')}
                  className={`py-4 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 ${
                    aiMode === 'preflop'
                      ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg scale-105'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="text-2xl mb-1">🎯</div>
                  <div>Preflop</div>
                  <div className="text-xs opacity-75 mt-1">GTO Ranges</div>
                </button>
                <button
                  onClick={() => setAiMode('flop')}
                  className={`py-4 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 ${
                    aiMode === 'flop'
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg scale-105'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="text-2xl mb-1">🎴</div>
                  <div>Flop</div>
                  <div className="text-xs opacity-75 mt-1">Flop GTO</div>
                </button>
                <button
                  onClick={() => setAiMode('odds')}
                  className={`py-4 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 ${
                    aiMode === 'odds'
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg scale-105'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="text-2xl mb-1">📊</div>
                  <div>Odds</div>
                  <div className="text-xs opacity-75 mt-1">All Streets</div>
                </button>
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-purple-400 font-bold capitalize">{aiMode}</span>
                {aiMode === 'odds' && ' - 📊 Pot odds calculator'}
                {aiMode === 'preflop' && ' - 🎯 Preflop GTO ranges'}
                {aiMode === 'flop' && ' - 🎴 Flop GTO strategy'}
              </p>
            </div>
          )}
          
          {/* Error display */}
          {error && (
            <div className="bg-red-500/90 backdrop-blur text-white p-5 rounded-xl mb-6 border-2 border-red-400 shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <span className="font-semibold">{error}</span>
              </div>
            </div>
          )}

          {/* Main recommendation display - Only for Odds Mode */}
          {action && aiMode === 'odds' && (
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 border-emerald-400/30 text-white p-8 rounded-2xl mb-6 shadow-2xl border-2 backdrop-blur">
              <div className="text-center mb-2">
                <p className="text-sm font-semibold text-white/80 mb-2">📊 ODDS ANALYSIS</p>
              </div>
              <div className="text-5xl font-extrabold text-center mb-8 drop-shadow-lg">
                {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
              </div>
              
              {/* Card Display */}
              {(heroCards.length > 0 || boardCards.length > 0) && (
                <div className="mb-6 bg-white/5 backdrop-blur-sm p-5 rounded-xl border border-white/20">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Hero Cards */}
                    {heroCards.length > 0 && (
                      <div>
                        <div className="text-xs text-white/60 uppercase tracking-wider mb-2">Your Hand:</div>
                        <div className="text-2xl font-bold text-yellow-300">
                          🃏 {heroCards.join(' ')}
                        </div>
                      </div>
                    )}
                    
                    {/* Board Cards */}
                    {boardCards.length > 0 && (
                      <div>
                        <div className="text-xs text-white/60 uppercase tracking-wider mb-2">
                          Board ({street}):
                        </div>
                        <div className="text-2xl font-bold text-cyan-300">
                          🎴 {boardCards.join(' ')}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">Pot Odds</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{potOdds}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">Hand Equity</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{handEquity}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">Implied Odds</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{impliedOdds}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">Fold Equity</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{foldEquity}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">EV</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{expectedValue}</div>
                </div>
              </div>
            </div>
          )}

          {/* Main recommendation display - For Preflop Mode */}
          {action && aiMode === 'preflop' && (
            <div className="bg-gradient-to-br from-orange-600 via-amber-600 to-yellow-600 border-orange-400/30 text-white p-8 rounded-2xl mb-6 shadow-2xl border-2 backdrop-blur">
              <div className="text-center mb-2">
                <p className="text-sm font-semibold text-white/80 mb-2">🎯 PREFLOP GTO</p>
              </div>
              <div className="text-5xl font-extrabold text-center mb-8 drop-shadow-lg">
                {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
              </div>
              
              {/* Card Display */}
              {heroCards.length > 0 && (
                <div className="mb-6 bg-white/5 backdrop-blur-sm p-5 rounded-xl border border-white/20">
                  <div className="text-center">
                    <div className="text-xs text-white/60 uppercase tracking-wider mb-2">Your Hand:</div>
                    <div className="text-3xl font-bold text-yellow-200">
                      🃏 {heroCards.join(' ')}
                    </div>
                  </div>
                </div>
              )}
              
              {/* GTO Reasoning - Display the detailed analysis */}
              <div className="bg-white/5 backdrop-blur-sm p-5 rounded-xl border border-white/20 mb-4">
                <div className="text-sm text-white/90 leading-relaxed whitespace-pre-line">
                  {reasoning || 'Analyzing GTO ranges...'}
                </div>
              </div>

              {/* Continue to Flop Button - Only show if not folding */}
              {!action.toLowerCase().includes('fold') && (
                <button
                  onClick={continueToFlop}
                  className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2"
                >
                  <span>Continue to Flop</span>
                  <span className="text-2xl">🎴 →</span>
                </button>
              )}
            </div>
          )}

          {/* Main recommendation display - For Flop Mode */}
          {action && aiMode === 'flop' && (
            <div className="bg-gradient-to-br from-purple-600 via-pink-600 to-fuchsia-600 border-purple-400/30 text-white p-8 rounded-2xl mb-6 shadow-2xl border-2 backdrop-blur">
              <div className="text-center mb-2">
                <p className="text-sm font-semibold text-white/80 mb-2">🎴 FLOP GTO STRATEGY</p>
              </div>
              <div className="text-5xl font-extrabold text-center mb-8 drop-shadow-lg">
                {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
              </div>
              
              {/* Card Display */}
              {(heroCards.length > 0 || boardCards.length > 0) && (
                <div className="mb-6 bg-white/5 backdrop-blur-sm p-5 rounded-xl border border-white/20">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Hero Cards */}
                    {heroCards.length > 0 && (
                      <div>
                        <div className="text-xs text-white/60 uppercase tracking-wider mb-2">Your Hand:</div>
                        <div className="text-2xl font-bold text-yellow-300">
                          🃏 {heroCards.join(' ')}
                        </div>
                      </div>
                    )}
                    
                    {/* Board Cards */}
                    {boardCards.length > 0 && (
                      <div>
                        <div className="text-xs text-white/60 uppercase tracking-wider mb-2">
                          Flop:
                        </div>
                        <div className="text-2xl font-bold text-cyan-300">
                          🎴 {boardCards.join(' ')}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Flop GTO Analysis - Display the detailed strategy */}
              <div className="bg-white/5 backdrop-blur-sm p-5 rounded-xl border border-white/20 mb-4">
                <div className="text-sm text-white/90 leading-relaxed whitespace-pre-line">
                  {reasoning || 'Analyzing flop GTO strategy...'}
                </div>
              </div>

              {/* Continue to Odds Button - Only show if not folding */}
              {!action.toLowerCase().includes('fold') && (
                <button
                  onClick={continueToOdds}
                  className="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2"
                >
                  <span>Continue to Odds</span>
                  <span className="text-2xl">📊 →</span>
                </button>
              )}
            </div>
          )}

          {/* Context Indicator - Show when flop mode has inherited context */}
          {isCameraActive && !capturedImage && aiMode === 'flop' && inheritedContext && (
            <div className="mb-6 bg-gradient-to-r from-blue-600 to-purple-600 p-5 rounded-2xl border-2 border-blue-400/30 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">
                    📋 Context from Preflop
                  </h3>
                  <div className="text-sm text-white/90 space-y-1">
                    <p>• Position: <span className="font-bold">{inheritedContext.heroPosition}</span> vs Villain at <span className="font-bold">{inheritedContext.villainPosition}</span></p>
                    <p>• Action: <span className="font-bold capitalize">{inheritedContext.preflopAction.replace(/_/g, ' ')}</span></p>
                    <p>• You {inheritedContext.preflopRecommendation}</p>
                  </div>
                </div>
                <button
                  onClick={resetToManualInput}
                  className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg font-bold text-sm transition-all"
                >
                  ⚙️ Manual Input
                </button>
              </div>
            </div>
          )}

          {/* Flop Mode: Hero Position Selector - Hide if context inherited */}
          {isCameraActive && !isAnalyzing && !capturedImage && aiMode === 'flop' && !inheritedContext && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-purple-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-purple-400 mb-4">
                1️⃣ Hero Position
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setFlopHeroPosition('IP')}
                  className={`py-4 px-4 rounded-xl font-bold text-base transition-all transform hover:scale-105 shadow-lg ${
                    flopHeroPosition === 'IP'
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  ✅ In Position
                </button>
                <button
                  onClick={() => setFlopHeroPosition('OOP')}
                  className={`py-4 px-4 rounded-xl font-bold text-base transition-all transform hover:scale-105 shadow-lg ${
                    flopHeroPosition === 'OOP'
                      ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  ❌ Out of Position
                </button>
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-purple-400 font-bold">{flopHeroPosition === 'IP' ? 'In Position' : 'Out of Position'}</span>
              </p>
            </div>
          )}

          {/* Flop Mode: Preflop Action Selector - Hide if context inherited */}
          {isCameraActive && !isAnalyzing && !capturedImage && aiMode === 'flop' && !inheritedContext && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-purple-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-purple-400 mb-4">
                2️⃣ Preflop Action
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setFlopPreflopAction('villain_called')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopAction === 'villain_called'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Villain Called Open
                </button>
                <button
                  onClick={() => setFlopPreflopAction('villain_called_3bet')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopAction === 'villain_called_3bet'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Villain Called 3-Bet
                </button>
                <button
                  onClick={() => setFlopPreflopAction('villain_3bet')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopAction === 'villain_3bet'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Villain 3-Bet
                </button>
                <button
                  onClick={() => setFlopPreflopAction('villain_opened')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopAction === 'villain_opened'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Villain Opened
                </button>
                <button
                  onClick={() => setFlopPreflopAction('villain_4bet')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopAction === 'villain_4bet'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Villain 4-Bet
                </button>
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-purple-400 font-bold capitalize">{flopPreflopAction.replace(/_/g, ' ')}</span>
              </p>
            </div>
          )}

          {/* Flop Mode: Villain Position Selector - Hide if context inherited */}
          {isCameraActive && !isAnalyzing && !capturedImage && aiMode === 'flop' && !inheritedContext && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-purple-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-purple-400 mb-4">
                3️⃣ Villain Position
              </h3>
              <div className="grid grid-cols-6 gap-2">
                {['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'].map((pos) => (
                  <button
                    key={pos}
                    onClick={() => setFlopVillainPosition(pos)}
                    className={`py-3 px-2 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                      flopVillainPosition === pos
                        ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white scale-105 ring-2 ring-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {pos}
                  </button>
                ))}
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Villain is at: <span className="text-purple-400 font-bold">{flopVillainPosition}</span>
              </p>
            </div>
          )}

          {/* Flop Mode: Capture Button - Show above camera */}
          {isCameraActive && !capturedImage && !isAnalyzing && aiMode === 'flop' && (
            <div className="mb-6">
              <button
                onClick={handleDeepCapture}
                className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                📸 Capture & Analyze Flop
              </button>
            </div>
          )}

          {/* Blinds Selector - Show for Odds and Preflop Modes */}
          {isCameraActive && !isAnalyzing && !capturedImage && (aiMode === 'odds' || aiMode === 'preflop') && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-blue-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-blue-400 mb-4">
                💵 Select Blinds
              </h3>
              <div className="grid grid-cols-3 gap-2">
                {['0.02/0.05', '0.05/0.10', '0.10/0.25'].map((blinds) => (
                  <button
                    key={blinds}
                    onClick={() => setSelectedBlinds(blinds)}
                    className={`py-3 px-2 rounded-xl font-bold text-sm md:text-base transition-all transform hover:scale-105 ${
                      selectedBlinds === blinds
                        ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg scale-105'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    ${blinds}
                  </button>
                ))}
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-blue-400 font-bold">${selectedBlinds}</span>
              </p>
            </div>
          )}

          {/* Odds Mode: Simple Capture Button */}
          {isCameraActive && !capturedImage && !isAnalyzing && aiMode === 'odds' && (
            <div className="mb-6">
              <button
                onClick={() => captureAndAnalyze()}
                className="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                📸 Capture & Analyze (Math Only)
              </button>
            </div>
          )}

          {/* Villain Position Selector - Show ONLY for Preflop Mode */}
          {isCameraActive && !isAnalyzing && !capturedImage && aiMode === 'preflop' && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-orange-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-orange-400 mb-4">
                👥 Select Villain Position
              </h3>
              <div className="grid grid-cols-6 gap-2">
                {['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'].map((pos) => (
                  <button
                    key={pos}
                    onClick={() => setVillainPositionPreflop(pos)}
                    className={`py-3 px-2 rounded-xl font-bold text-sm transition-all transform hover:scale-105 ${
                      villainPositionPreflop === pos
                        ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-lg scale-105'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {pos}
                  </button>
                ))}
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Villain is at: <span className="text-orange-400 font-bold">{villainPositionPreflop}</span>
              </p>
            </div>
          )}

          {/* Video/Image display */}
          <div className="relative rounded-2xl overflow-hidden shadow-2xl border-2 border-gray-700">
            {capturedImage ? (
              <img
                src={capturedImage}
                alt="Captured poker table"
                className="w-full"
              />
            ) : (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full bg-black"
              />
            )}
            
            {/* Analyzing overlay */}
            {isAnalyzing && (
              <div className={`absolute inset-0 backdrop-blur-sm flex items-center justify-center z-20 ${
                aiMode === 'odds' 
                  ? 'bg-gradient-to-br from-emerald-900/95 to-teal-900/95'
                  : aiMode === 'preflop'
                  ? 'bg-gradient-to-br from-orange-900/95 to-amber-900/95'
                  : 'bg-gradient-to-br from-purple-900/95 to-indigo-900/95'
              }`}>
                <div className="text-center">
                  <div className={`w-20 h-20 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-6 ${
                    aiMode === 'odds' ? 'border-emerald-400' : aiMode === 'preflop' ? 'border-orange-400' : 'border-purple-400'
                  }`}></div>
                  <div className="text-2xl font-bold text-white drop-shadow-lg">
                    {aiMode === 'odds' ? '📊 Odds Analysis...' : aiMode === 'preflop' ? '🎯 Preflop GTO...' : '🎴 Flop GTO Analysis...'}
                  </div>
                  <div className={`mt-2 ${aiMode === 'odds' ? 'text-emerald-300' : aiMode === 'preflop' ? 'text-orange-300' : 'text-purple-300'}`}>
                    {aiMode === 'odds' ? 'Calculating pot odds...' : aiMode === 'preflop' ? 'Checking GTO ranges...' : 'Gemini extracting cards → Applying flop GTO strategy...'}
                  </div>
                </div>
              </div>
            )}
            

            {/* Position buttons overlay - For Preflop Mode */}
            {isCameraActive && !capturedImage && !isAnalyzing && aiMode === 'preflop' && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/70 to-transparent p-4 z-10">
                {/* Open Raise toggle button */}
                <div className="mb-3 flex justify-center">
                  <button
                    onClick={() => setIsOpenRaise(!isOpenRaise)}
                    className={`py-2 px-6 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                      isOpenRaise
                        ? 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white scale-105 ring-2 ring-yellow-300'
                        : 'bg-gray-700/80 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {isOpenRaise ? '🚀 OPEN RAISE (First to Act)' : '💬 Facing a Raise?'}
                  </button>
                </div>
                
                <p className="text-center text-xs text-gray-300 mb-2">
                  {isOpenRaise ? '🚀 Opening the pot - Click your position' : '👤 Click Your Position to Capture & Analyze'}
                </p>
                <div className="grid grid-cols-6 gap-2">
                  {['BTN', 'CO', 'MP', 'UTG', 'BB', 'SB'].map((pos) => (
                    <button
                      key={pos}
                      onClick={() => handlePositionClick(pos)}
                      className={`py-3 px-2 rounded-lg font-bold text-sm transition-all transform hover:scale-110 shadow-lg ${
                        selectedPosition === pos
                          ? 'bg-gradient-to-r from-blue-500 to-sky-500 text-white scale-105 ring-2 ring-white'
                          : 'bg-gray-800/90 text-gray-200 hover:bg-gray-700'
                      }`}
                    >
                      {pos}
                    </button>
                  ))}
                </div>
              </div>
            )}

          </div>

          {/* Hidden canvas */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Control buttons */}
          <div className="flex justify-center gap-4 mt-8">
            {capturedImage ? (
              <button
                onClick={captureAgain}
                className="px-10 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                🔄 Capture Again
              </button>
            ) : !isCameraActive ? (
              <button
                onClick={startCamera}
                className="px-10 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                📷 Start Camera
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  )
}
