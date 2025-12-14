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
  const [selectedPosition, setSelectedPosition] = useState<string>('BTN')
  const [selectedBlinds, setSelectedBlinds] = useState<string>('0.02/0.05')
  const [aiMode, setAiMode] = useState<'flash' | 'deep'>('flash')
  
  // Deep Mode specific states
  const [heroPosition, setHeroPosition] = useState<string>('BTN')
  const [villainPosition, setVillainPosition] = useState<string>('BB')
  const [villainAction, setVillainAction] = useState<string>('last-to-act')
  
  // Main display info
  const [action, setAction] = useState<string>('')
  const [potOdds, setPotOdds] = useState<string>('')
  const [handEquity, setHandEquity] = useState<string>('')
  const [impliedOdds, setImpliedOdds] = useState<string>('')
  const [foldEquity, setFoldEquity] = useState<string>('')
  const [expectedValue, setExpectedValue] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')
  
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
    await captureAndAnalyze()
  }

  // Handle Deep Mode capture button
  const handleDeepCapture = async () => {
    if (isAnalyzing) return
    await captureAndAnalyze()
  }

  // Capture photo and analyze
  const captureAndAnalyze = async () => {
    if (!videoRef.current || !canvasRef.current) {
      setError('Camera not ready')
      return
    }
    
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
      
      // For Deep Mode, pass manual inputs
      if (aiMode === 'deep') {
        formData.append('hero_position', heroPosition)
        formData.append('villain_position', villainPosition)
        formData.append('blinds', selectedBlinds)
        formData.append('villain_action', villainAction)
      } else {
        // Flash Mode
        formData.append('position', selectedPosition)
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
        setDetailedInfo(data.detailed_info || null)
        
        // Extract card data from response
        if (data.extracted_data) {
          setHeroCards(data.extracted_data.hero_cards || [])
          setBoardCards(data.extracted_data.board_cards || [])
          setStreet(data.extracted_data.street || '')
        }
        
        // For Deep Mode, auto-redirect to details page
        if (aiMode === 'deep' && data.detailed_info) {
          localStorage.setItem('poker_detailed_info', JSON.stringify(data.detailed_info))
          localStorage.setItem('poker_action', rec.action)
          localStorage.setItem('poker_pot_size', potSize)
          localStorage.setItem('poker_captured_image', capturedImage)
          localStorage.setItem('poker_ai_mode', aiMode)
          router.push('/details')
        } else {
          // Flash mode: speak the action
          speak(rec.action)
        }
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
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setAiMode('flash')}
                  className={`py-5 px-4 rounded-xl font-bold text-base transition-all transform hover:scale-105 ${
                    aiMode === 'flash'
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg scale-105'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="text-3xl mb-2">⚡</div>
                  <div>Flash</div>
                  <div className="text-xs opacity-75 mt-1">Fast Analysis</div>
                </button>
                <button
                  onClick={() => setAiMode('deep')}
                  className={`py-5 px-4 rounded-xl font-bold text-base transition-all transform hover:scale-105 ${
                    aiMode === 'deep'
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg scale-105'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="text-3xl mb-2">🧠</div>
                  <div>Deep</div>
                  <div className="text-xs opacity-75 mt-1">Advanced GTO</div>
                </button>
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-purple-400 font-bold capitalize">{aiMode}</span>
                {aiMode === 'flash' && ' - ⚡ Gemini Flash analysis'}
                {aiMode === 'deep' && ' - 🔄 Gemini + Claude Hybrid GTO'}
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

          {/* Main recommendation display - Only for Flash Mode */}
          {action && aiMode === 'flash' && (
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 border-emerald-400/30 text-white p-8 rounded-2xl mb-6 shadow-2xl border-2 backdrop-blur">
              <div className="text-center mb-2">
                <p className="text-sm font-semibold text-white/80 mb-2">⚡ FLASH ANALYSIS</p>
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
              
              {detailedInfo && (
                <button
                  onClick={() => {
                    localStorage.setItem('poker_detailed_info', JSON.stringify(detailedInfo))
                    localStorage.setItem('poker_action', action)
                    localStorage.setItem('poker_pot_size', potSize)
                    localStorage.setItem('poker_captured_image', capturedImage)
                    localStorage.setItem('poker_ai_mode', aiMode)
                    router.push('/details')
                  }}
                  className="mt-6 w-full bg-white text-emerald-700 hover:bg-emerald-50 font-bold py-3 rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                >
                  View Detailed Analysis →
                </button>
              )}
            </div>
          )}

          {/* Blinds Selector - Only show for Flash Mode */}
          {isCameraActive && !isAnalyzing && !capturedImage && aiMode === 'flash' && (
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
                aiMode === 'flash' 
                  ? 'bg-gradient-to-br from-emerald-900/95 to-teal-900/95'
                  : 'bg-gradient-to-br from-purple-900/95 to-indigo-900/95'
              }`}>
                <div className="text-center">
                  <div className={`w-20 h-20 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-6 ${
                    aiMode === 'flash' ? 'border-emerald-400' : 'border-purple-400'
                  }`}></div>
                  <div className="text-2xl font-bold text-white drop-shadow-lg">
                    {aiMode === 'flash' ? '⚡ Flash Analysis...' : '🔄 Hybrid Analysis...'}
                  </div>
                  <div className={`mt-2 ${aiMode === 'flash' ? 'text-emerald-300' : 'text-purple-300'}`}>
                    {aiMode === 'flash' ? 'Processing poker table...' : 'Gemini extracting → Claude analyzing GTO...'}
                  </div>
                </div>
              </div>
            )}
            
            {/* Position buttons overlay - Only for Flash Mode */}
            {isCameraActive && !capturedImage && !isAnalyzing && aiMode === 'flash' && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/70 to-transparent p-4 z-10">
                <p className="text-center text-xs text-gray-300 mb-2">
                  👤 Click Your Position to Capture & Analyze
                </p>
                <div className="grid grid-cols-6 gap-2">
                  {['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO'].map((pos) => (
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

            {/* Deep Mode Manual Inputs */}
            {isCameraActive && !capturedImage && !isAnalyzing && aiMode === 'deep' && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/70 to-transparent p-4 z-10">
                <div className="grid grid-cols-2 gap-3 mb-3">
                  {/* Hero Position */}
                  <div className="bg-gray-800/90 p-3 rounded-lg">
                    <label className="text-xs text-gray-400 mb-1 block">Hero Position</label>
                    <select
                      value={heroPosition}
                      onChange={(e) => setHeroPosition(e.target.value)}
                      className="w-full bg-gray-700 text-white py-2 px-3 rounded font-bold text-sm"
                    >
                      <option value="BTN">BTN</option>
                      <option value="SB">SB</option>
                      <option value="BB">BB</option>
                      <option value="UTG">UTG</option>
                      <option value="MP">MP</option>
                      <option value="CO">CO</option>
                    </select>
                  </div>

                  {/* Villain Position */}
                  <div className="bg-gray-800/90 p-3 rounded-lg">
                    <label className="text-xs text-gray-400 mb-1 block">Villain Position</label>
                    <select
                      value={villainPosition}
                      onChange={(e) => setVillainPosition(e.target.value)}
                      className="w-full bg-gray-700 text-white py-2 px-3 rounded font-bold text-sm"
                    >
                      <option value="BTN">BTN</option>
                      <option value="SB">SB</option>
                      <option value="BB">BB</option>
                      <option value="UTG">UTG</option>
                      <option value="MP">MP</option>
                      <option value="CO">CO</option>
                    </select>
                  </div>

                  {/* Blinds */}
                  <div className="bg-gray-800/90 p-3 rounded-lg">
                    <label className="text-xs text-gray-400 mb-1 block">Blinds</label>
                    <select
                      value={selectedBlinds}
                      onChange={(e) => setSelectedBlinds(e.target.value)}
                      className="w-full bg-gray-700 text-white py-2 px-3 rounded font-bold text-sm"
                    >
                      <option value="0.02/0.05">$0.02/$0.05</option>
                      <option value="0.05/0.10">$0.05/$0.10</option>
                      <option value="0.10/0.25">$0.10/$0.25</option>
                      <option value="0.25/0.50">$0.25/$0.50</option>
                      <option value="0.50/1.00">$0.50/$1.00</option>
                    </select>
                  </div>

                  {/* Villain Action */}
                  <div className="bg-gray-800/90 p-3 rounded-lg">
                    <label className="text-xs text-gray-400 mb-1 block">Villain Action</label>
                    <select
                      value={villainAction}
                      onChange={(e) => setVillainAction(e.target.value)}
                      className="w-full bg-gray-700 text-white py-2 px-3 rounded font-bold text-sm"
                    >
                      <option value="last-to-act">Last to Act (Hero First)</option>
                      <option value="checked">Checked</option>
                      <option value="raised">Raised</option>
                      <option value="check-raised">Check-Raised</option>
                      <option value="re-raised">Re-Raised</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleDeepCapture}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl font-bold text-base transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  📸 Capture & Analyze (Heads-Up)
                </button>
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
