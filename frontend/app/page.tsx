'use client'

import { useEffect, useRef, useState } from 'react'

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)
  const autoModeTimerRef = useRef<NodeJS.Timeout | null>(null)

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [lastRecommendation, setLastRecommendation] = useState<string>('')
  const [error, setError] = useState<string>('')
  const [capturedImage, setCapturedImage] = useState<string>('')
  const [showResult, setShowResult] = useState(false)
  const [isAutoMode, setIsAutoMode] = useState(false)
  const [autoModeCount, setAutoModeCount] = useState(0)
  const [gameInfo, setGameInfo] = useState<{potSize?: string, position?: string, reasoning?: string} | null>(null)

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
          facingMode: 'environment', // Use back camera on mobile
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
      setLastRecommendation('')
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
    setLastRecommendation('')
    setShowResult(false)

    try {
      const canvas = canvasRef.current
      const video = videoRef.current
      
      // Set canvas size to match video
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      // Draw current frame to canvas
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('Could not get canvas context')
      
      ctx.drawImage(video, 0, 0)
      
      // Store captured image as data URL for display
      const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9)
      setCapturedImage(imageDataUrl)
      
      // Stop camera to save resources during analysis
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
        tracks.forEach(track => track.stop())
        videoRef.current.srcObject = null
        setIsCameraActive(false)
      }
      
      // Convert canvas to blob for upload
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (blob) => blob ? resolve(blob) : reject(new Error('Failed to create blob')),
          'image/jpeg',
          0.9
        )
      })

      // Send to backend for analysis
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

      if (data.recommendation) {
        const rec = data.recommendation
        setLastRecommendation(rec.action)
        setGameInfo({
          potSize: rec.pot_size || undefined,
          position: data.game_state?.hero_position || undefined,
          reasoning: rec.reasoning || undefined
        })
        setShowResult(true)
      } else if (data.hero_turn === false) {
        setError('Not hero\'s turn detected. Try capturing when action is on you.')
      } else {
        setError('No clear recommendation. Make sure the poker table is clearly visible.')
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
    setShowResult(false)
    setLastRecommendation('')
    setError('')
    startCamera()
  }

  // Auto-mode: Capture and analyze continuously
  const captureAndAnalyzeAuto = async () => {
    if (!videoRef.current || !canvasRef.current || !isAutoMode) return
    
    setIsAnalyzing(true)
    setError('')

    try {
      const canvas = canvasRef.current
      const video = videoRef.current
      
      // Set canvas size to match video
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      
      // Draw current frame to canvas
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('Could not get canvas context')
      
      ctx.drawImage(video, 0, 0)
      
      // Convert canvas to blob for upload (no image display in auto-mode)
      const blob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob(
          (blob) => blob ? resolve(blob) : reject(new Error('Failed to create blob')),
          'image/jpeg',
          0.9
        )
      })

      // Send to backend for analysis
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      
      const formData = new FormData()
      formData.append('image', blob, 'poker_table.jpg')

      console.log(`🤖 Auto-mode capture ${autoModeCount + 1}`)
      
      const response = await fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()

      if (data.recommendation) {
        const rec = data.recommendation
        setLastRecommendation(rec.action)
        setShowResult(true)
        
        // Auto-speak recommendation
        speak(rec.action)
        
        // Increment counter
        setAutoModeCount(prev => prev + 1)
      }

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Analysis failed'
      console.error('Auto-mode analysis error:', err)
      // Don't stop auto-mode on errors, just log them
    } finally {
      setIsAnalyzing(false)
      
      // Schedule next capture if auto-mode is still active
      if (isAutoMode) {
        autoModeTimerRef.current = setTimeout(() => {
          captureAndAnalyzeAuto()
        }, 3000)
      }
    }
  }

  // Start auto-mode
  const startAutoMode = async () => {
    // Start camera if not active
    if (!isCameraActive) {
      await startCamera()
    }
    
    setIsAutoMode(true)
    setAutoModeCount(0)
    setCapturedImage('') // Clear any captured image
    setShowResult(false)
    
    // Start the capture loop after a brief delay
    setTimeout(() => {
      captureAndAnalyzeAuto()
    }, 500)
  }

  // Stop auto-mode
  const stopAutoMode = () => {
    setIsAutoMode(false)
    
    // Clear the timer
    if (autoModeTimerRef.current) {
      clearTimeout(autoModeTimerRef.current)
      autoModeTimerRef.current = null
    }
    
    setShowResult(false)
    setLastRecommendation('')
  }

  // Cleanup on unmount or when auto-mode changes
  useEffect(() => {
    return () => {
      if (autoModeTimerRef.current) {
        clearTimeout(autoModeTimerRef.current)
      }
      stopCamera()
    }
  }, [])

  // Trigger auto-mode capture loop when enabled
  useEffect(() => {
    if (isAutoMode && isCameraActive) {
      // Initial capture already triggered in startAutoMode
    } else if (!isAutoMode && autoModeTimerRef.current) {
      clearTimeout(autoModeTimerRef.current)
      autoModeTimerRef.current = null
    }
  }, [isAutoMode, isCameraActive])

  return (
    <main className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold text-center mb-6">Poker GTO Vision</h1>
        
        {/* Error display */}
        {error && (
          <div className="bg-red-500 text-white p-4 rounded-lg mb-4 max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {/* Recommendation display with details */}
        {lastRecommendation && (
          <div className="bg-gradient-to-r from-green-600 to-green-700 text-white p-6 rounded-lg mb-4 max-w-2xl mx-auto shadow-lg">
            <div className="text-2xl font-bold mb-3 text-center">
              🔊 {lastRecommendation}
            </div>
            {gameInfo && (
              <div className="grid grid-cols-2 gap-4 text-sm mt-4 bg-green-800 bg-opacity-40 p-4 rounded">
                <div>
                  <span className="text-green-200">Pot Size:</span>
                  <span className="font-semibold ml-2">{gameInfo.potSize || 'Unknown'}</span>
                </div>
                <div>
                  <span className="text-green-200">Position:</span>
                  <span className="font-semibold ml-2">{gameInfo.position || 'Detecting...'}</span>
                </div>
                {gameInfo.reasoning && (
                  <div className="col-span-2 mt-2 pt-2 border-t border-green-600">
                    <span className="text-green-200">Reasoning:</span>
                    <p className="text-white mt-1">{gameInfo.reasoning}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Auto-mode indicator */}
        {isAutoMode && (
          <div className="bg-purple-600 text-white p-3 rounded-lg mb-4 max-w-2xl mx-auto">
            <div className="text-center font-bold">
              🤖 AUTO MODE ACTIVE - Analyzing every 3 seconds ({autoModeCount} captures)
            </div>
          </div>
        )}

        {/* Video/Image display */}
        <div className={`relative max-w-2xl mx-auto ${isAutoMode ? 'ring-4 ring-purple-500 ring-opacity-50 animate-pulse' : ''}`}>
          {capturedImage ? (
            /* Show captured image */
            <img
              src={capturedImage}
              alt="Captured poker table"
              className="w-full rounded-lg"
            />
          ) : (
            /* Show live video */
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
                <div className="text-xl font-bold">Analyzing...</div>
              </div>
            </div>
          )}

          {/* Recommendation overlay - Compact and semi-transparent */}
          {showResult && lastRecommendation && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 rounded-lg">
              <div className="bg-gradient-to-br from-green-500 to-green-700 bg-opacity-90 text-white px-6 py-4 rounded-xl shadow-2xl border-2 border-white backdrop-blur-sm">
                <div className="text-center">
                  <div className="text-3xl font-bold inline-block mr-3">
                    {lastRecommendation.includes('Fold') ? '❌' : 
                     lastRecommendation.includes('Call') ? '✅' : '🚀'}
                  </div>
                  <div className="text-2xl font-extrabold inline-block uppercase tracking-wide">
                    {lastRecommendation}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Hidden canvas for photo capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Control buttons */}
        <div className="flex flex-col items-center gap-4 mt-6">
          <div className="flex justify-center gap-4">
            {showResult || capturedImage ? (
              /* After capture/analysis */
              <button
                onClick={captureAgain}
                className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition-colors"
              >
                🔄 Capture Again
              </button>
            ) : !isCameraActive ? (
              /* Initial state */
              <button
                onClick={startCamera}
                className="px-8 py-4 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold text-lg transition-colors"
              >
                📷 Start Camera
              </button>
            ) : (
              /* Camera active state */
              <>
                <button
                  onClick={captureAndAnalyze}
                  disabled={isAnalyzing || isAutoMode}
                  className={`px-8 py-4 rounded-lg font-semibold text-lg transition-colors ${
                    isAnalyzing || isAutoMode
                      ? 'bg-gray-600 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isAnalyzing ? '⏳ Analyzing...' : '📸 Capture & Analyze'}
                </button>
                <button
                  onClick={stopCamera}
                  disabled={isAutoMode}
                  className={`px-8 py-4 rounded-lg font-semibold text-lg transition-colors ${
                    isAutoMode
                      ? 'bg-gray-600 cursor-not-allowed'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  ❌ Stop Camera
                </button>
              </>
            )}
          </div>
          
          {/* Auto-mode button (only show when camera is active) */}
          {isCameraActive && !capturedImage && (
            <button
              onClick={isAutoMode ? stopAutoMode : startAutoMode}
              className={`px-8 py-4 rounded-lg font-semibold text-lg transition-colors ${
                isAutoMode
                  ? 'bg-purple-600 hover:bg-purple-700 ring-2 ring-purple-300'
                  : 'bg-purple-500 hover:bg-purple-600'
              }`}
            >
              {isAutoMode ? '⏸️ Stop Auto Mode' : '🤖 Start Auto Mode'}
            </button>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 max-w-2xl mx-auto text-sm text-gray-400">
          <h2 className="font-semibold text-white mb-2">Instructions:</h2>
          <ol className="list-decimal list-inside space-y-1">
            <li>Click &quot;Start Camera&quot; to activate your phone camera</li>
            <li>Point camera at the poker table on your laptop screen</li>
            <li><strong className="text-white">Manual Mode:</strong> Click &quot;Capture & Analyze&quot; when it&apos;s your turn</li>
            <li><strong className="text-purple-400">Auto Mode:</strong> Click &quot;Start Auto Mode&quot; for continuous analysis every 3 seconds</li>
            <li>Listen for audio recommendations spoken aloud</li>
            <li>Click &quot;Stop Auto Mode&quot; to disable continuous analysis</li>
          </ol>
        </div>
      </div>
    </main>
  )
}
