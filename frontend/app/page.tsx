'use client'

import { useEffect, useRef, useState } from 'react'

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
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string>('')
  const [capturedImage, setCapturedImage] = useState<string>('')
  const [selectedPosition, setSelectedPosition] = useState<string>('BTN')
  
  // Main display info
  const [action, setAction] = useState<string>('')
  const [potOdds, setPotOdds] = useState<string>('')
  const [handEquity, setHandEquity] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')
  const [betSize, setBetSize] = useState<string>('')
  
  // Detailed side panel info
  const [detailedInfo, setDetailedInfo] = useState<DetailedInfo | null>(null)
  const [showSidePanel, setShowSidePanel] = useState(false)

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

  // Capture photo and analyze
  const captureAndAnalyze = async () => {
    if (!videoRef.current || !canvasRef.current) return
    
    setIsAnalyzing(true)
    setError('')
    setAction('')

    try {
      const canvas = canvasRef.current
      const video = videoRef.current
      
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
      formData.append('position', selectedPosition)

      console.log(`📸 Sending image to ${backendUrl}/analyze with position: ${selectedPosition}`)
      
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
        setPotOdds(rec.pot_odds)
        setHandEquity(rec.hand_equity)
        setPotSize(rec.pot_size || 'N/A')
        setBetSize(rec.bet_size || 'N/A')
        setDetailedInfo(data.detailed_info || null)
        
        // Speak the action
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
    setShowSidePanel(false)
    startCamera()
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-green-900 to-gray-900 text-white flex">
      {/* Main content area */}
      <div className="flex-1 px-4 py-6">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-8">
            <h1 className="text-5xl font-extrabold bg-gradient-to-r from-green-400 via-emerald-500 to-teal-400 bg-clip-text text-transparent mb-2">
              🎰 Poker Vision
            </h1>
            <p className="text-gray-400 text-lg">Powered by Google Gemini AI 🤖</p>
          </div>
          
          {/* Error display */}
          {error && (
            <div className="bg-red-500/90 backdrop-blur text-white p-5 rounded-xl mb-6 border-2 border-red-400 shadow-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">⚠️</span>
                <span className="font-semibold">{error}</span>
              </div>
            </div>
          )}

          {/* Main recommendation display - Enhanced */}
          {action && (
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 text-white p-8 rounded-2xl mb-6 shadow-2xl border-2 border-emerald-400/30 backdrop-blur">
              <div className="text-5xl font-extrabold text-center mb-8 drop-shadow-lg">
                {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
              </div>
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-emerald-200 text-xs font-semibold uppercase tracking-wider mb-2">Pot Odds</div>
                  <div className="text-3xl font-bold text-white drop-shadow">{potOdds}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-emerald-200 text-xs font-semibold uppercase tracking-wider mb-2">Hand Equity</div>
                  <div className="text-3xl font-bold text-white drop-shadow">{handEquity}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-emerald-200 text-xs font-semibold uppercase tracking-wider mb-2">Bet Size</div>
                  <div className="text-3xl font-bold text-white drop-shadow">{betSize}</div>
                </div>
              </div>
              
              {detailedInfo && (
                <button
                  onClick={() => setShowSidePanel(!showSidePanel)}
                  className="mt-6 w-full bg-white text-emerald-700 font-bold py-3 rounded-xl hover:bg-emerald-50 transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
                >
                  {showSidePanel ? '← Hide Details' : 'View Detailed Analysis →'}
                </button>
              )}
            </div>
          )}

          {/* Position Selector - Only show when camera is active and not analyzing */}
          {isCameraActive && !isAnalyzing && !capturedImage && (
            <div className="mb-6 bg-gray-800/90 backdrop-blur p-6 rounded-2xl border-2 border-emerald-500/30 shadow-xl">
              <h3 className="text-center text-lg font-bold text-emerald-400 mb-4">
                👤 Select Your Position
              </h3>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                {['BTN', 'SB', 'BB', 'UTG', 'MP', 'CO'].map((pos) => (
                  <button
                    key={pos}
                    onClick={() => setSelectedPosition(pos)}
                    className={`py-3 px-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 ${
                      selectedPosition === pos
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg scale-105'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {pos}
                  </button>
                ))}
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-emerald-400 font-bold">{selectedPosition}</span>
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
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/95 to-teal-900/95 backdrop-blur-sm flex items-center justify-center">
                <div className="text-center">
                  <div className="w-20 h-20 border-4 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
                  <div className="text-2xl font-bold text-white drop-shadow-lg">🤖 Gemini AI Analyzing...</div>
                  <div className="text-emerald-300 mt-2">Processing poker table...</div>
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
            ) : (
              <>
                <button
                  onClick={captureAndAnalyze}
                  disabled={isAnalyzing}
                  className={`px-10 py-4 rounded-xl font-bold text-lg transition-all shadow-lg transform ${
                    isAnalyzing 
                      ? 'bg-gray-600 cursor-not-allowed opacity-70' 
                      : 'bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 hover:shadow-xl hover:scale-105'
                  }`}
                >
                  {isAnalyzing ? '⏳ Analyzing...' : '📸 Capture & Analyze'}
                </button>
                <button
                  onClick={stopCamera}
                  className="px-10 py-4 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  ❌ Stop
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Side panel - Detailed analysis */}
      {showSidePanel && detailedInfo && (
        <div className="w-96 bg-gray-800 border-l border-gray-700 p-6 overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Detailed Analysis</h2>
            <button
              onClick={() => setShowSidePanel(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          {/* Game State */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-blue-400 mb-2">Game State</h3>
            <div className="bg-gray-700 p-3 rounded">
              <div><span className="text-gray-400">Street:</span> <span className="capitalize">{detailedInfo.game_state.street}</span></div>
              <div><span className="text-gray-400">Pot:</span> {detailedInfo.game_state.pot_dollars} ({potSize})</div>
              {detailedInfo.game_state.board_cards.length > 0 && (
                <div><span className="text-gray-400">Board:</span> {detailedInfo.game_state.board_cards.join(' ')}</div>
              )}
            </div>
          </div>

          {/* Reasoning */}
          {detailedInfo.reasoning && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">Reasoning</h3>
              <div className="bg-gray-700 p-3 rounded text-sm">
                {detailedInfo.reasoning}
              </div>
            </div>
          )}

          {/* Range Analysis */}
          {detailedInfo.range_analysis && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">Range Analysis</h3>
              <div className="bg-gray-700 p-3 rounded text-sm">
                {detailedInfo.range_analysis}
              </div>
            </div>
          )}

          {/* EV Calculation */}
          {detailedInfo.ev_calculation && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">EV Breakdown</h3>
              <div className="bg-gray-700 p-3 rounded text-sm">
                {detailedInfo.ev_calculation}
              </div>
            </div>
          )}

          {/* Action History */}
          {detailedInfo.action_history && detailedInfo.action_history.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">Action History</h3>
              <div className="bg-gray-700 p-3 rounded text-sm space-y-1">
                {detailedInfo.action_history.map((action, idx) => (
                  <div key={idx}>• {action}</div>
                ))}
              </div>
            </div>
          )}

          {/* Alternative Lines */}
          {detailedInfo.alternative_lines && detailedInfo.alternative_lines.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">Alternative Lines</h3>
              <div className="bg-gray-700 p-3 rounded text-sm space-y-1">
                {detailedInfo.alternative_lines.map((line, idx) => (
                  <div key={idx}>• {line}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
