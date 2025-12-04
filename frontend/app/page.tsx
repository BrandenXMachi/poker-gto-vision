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
  
  // Main display info
  const [action, setAction] = useState<string>('')
  const [potOdds, setPotOdds] = useState<string>('')
  const [handEquity, setHandEquity] = useState<string>('')
  const [potSize, setPotSize] = useState<string>('')
  const [position, setPosition] = useState<string>('')
  
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

      console.log(`📸 Sending image to ${backendUrl}/analyze`)
      
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
        setPosition(rec.position || 'Unknown')
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
    <main className="min-h-screen bg-gray-900 text-white flex">
      {/* Main content area */}
      <div className="flex-1 px-4 py-6">
        <div className="container mx-auto max-w-4xl">
          <h1 className="text-3xl font-bold text-center mb-6">Poker GTO Vision - Gemini AI</h1>
          
          {/* Error display */}
          {error && (
            <div className="bg-red-500 text-white p-4 rounded-lg mb-4">
              {error}
            </div>
          )}

          {/* Main recommendation display - Simplified */}
          {action && (
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-8 rounded-xl mb-4 shadow-2xl">
              <div className="text-4xl font-bold text-center mb-6">
                {action.includes('Fold') ? '❌' : action.includes('Call') ? '✅' : '🚀'} {action}
              </div>
              
              <div className="grid grid-cols-3 gap-6 text-center">
                <div className="bg-blue-800 bg-opacity-40 p-4 rounded-lg">
                  <div className="text-blue-200 text-sm mb-1">Pot Odds</div>
                  <div className="text-2xl font-bold">{potOdds}</div>
                </div>
                <div className="bg-blue-800 bg-opacity-40 p-4 rounded-lg">
                  <div className="text-blue-200 text-sm mb-1">Hand Equity</div>
                  <div className="text-2xl font-bold">{handEquity}</div>
                </div>
                <div className="bg-blue-800 bg-opacity-40 p-4 rounded-lg">
                  <div className="text-blue-200 text-sm mb-1">Position</div>
                  <div className="text-2xl font-bold">{position}</div>
                </div>
              </div>
              
              {detailedInfo && (
                <button
                  onClick={() => setShowSidePanel(!showSidePanel)}
                  className="mt-4 w-full bg-white text-blue-600 font-semibold py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {showSidePanel ? '← Hide Details' : 'View Detailed Analysis →'}
                </button>
              )}
            </div>
          )}

          {/* Video/Image display */}
          <div className="relative">
            {capturedImage ? (
              <img
                src={capturedImage}
                alt="Captured poker table"
                className="w-full rounded-lg"
              />
            ) : (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full rounded-lg bg-black"
              />
            )}
            
            {/* Analyzing overlay */}
            {isAnalyzing && (
              <div className="absolute inset-0 bg-black bg-opacity-70 flex items-center justify-center rounded-lg">
                <div className="text-center">
                  <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <div className="text-xl font-bold">🤖 Gemini AI Analyzing...</div>
                </div>
              </div>
            )}
          </div>

          {/* Hidden canvas */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Control buttons */}
          <div className="flex justify-center gap-4 mt-6">
            {capturedImage ? (
              <button
                onClick={captureAgain}
                className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition-colors"
              >
                🔄 Capture Again
              </button>
            ) : !isCameraActive ? (
              <button
                onClick={startCamera}
                className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition-colors"
              >
                📷 Start Camera
              </button>
            ) : (
              <>
                <button
                  onClick={captureAndAnalyze}
                  disabled={isAnalyzing}
                  className={`px-8 py-4 rounded-lg font-semibold text-lg transition-colors ${
                    isAnalyzing ? 'bg-gray-600 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isAnalyzing ? '⏳ Analyzing...' : '📸 Capture & Analyze'}
                </button>
                <button
                  onClick={stopCamera}
                  className="px-8 py-4 bg-red-600 hover:bg-red-700 rounded-lg font-semibold text-lg transition-colors"
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
