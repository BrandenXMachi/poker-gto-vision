'use client'

import { useEffect, useRef, useState } from 'react'

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)

  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected')
  const [lastRecommendation, setLastRecommendation] = useState<string>('')
  const [error, setError] = useState<string>('')

  // Initialize speech synthesis
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis
    }
  }, [])

  // Text-to-Speech function
  const speak = (text: string) => {
    if (synthRef.current) {
      // Cancel any ongoing speech
      synthRef.current.cancel()
      
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.0
      utterance.pitch = 1.0
      utterance.volume = 1.0
      synthRef.current.speak(utterance)
    }
  }

  // Start camera and analysis
  const startCamera = async () => {
    try {
      setError('')
      setIsAnalyzing(true) // Set this BEFORE connecting to enable retry logic
      
      // Request camera access with back camera preference
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      })

      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }

      // Connect to WebSocket
      connectWebSocket()
      
      speak('Analysis started. Watching for hero turn.')

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to access camera'
      setError(errorMsg)
      setIsAnalyzing(false) // Reset on error
      console.error('Camera error:', err)
    }
  }

  // Connect to WebSocket server with simple retry
  const connectWebSocket = (retryCount = 0) => {
    setConnectionStatus('connecting')
    
    const backendUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    const wsUrl = `${backendUrl}/ws`
    
    console.log(`Connecting to ${wsUrl} (attempt ${retryCount + 1})...`)
    
    const ws = new WebSocket(wsUrl)
    let connectionTimeout: NodeJS.Timeout

    // Set timeout for connection
    connectionTimeout = setTimeout(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        console.log('Connection timeout, closing...')
        ws.close()
      }
    }, 10000) // 10 second timeout
    
    ws.onopen = () => {
      clearTimeout(connectionTimeout)
      console.log('✅ WebSocket connected')
      setConnectionStatus('connected')
      setError('')
      startFrameCapture()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'recommendation') {
          const recommendation = data.recommendation
          setLastRecommendation(recommendation.action)
          
          let speechText = `Hero turn. ${recommendation.action}.`
          if (recommendation.pot_size) speechText += ` Pot is ${recommendation.pot_size}.`
          if (recommendation.ev) speechText += ` Expected value ${recommendation.ev}.`
          if (recommendation.reasoning) speechText += ` ${recommendation.reasoning}.`
          
          speak(speechText)
        } else if (data.type === 'status') {
          console.log('📡 Status:', data.message)
        }
      } catch (err) {
        console.error('Error parsing message:', err)
      }
    }

    ws.onerror = (error) => {
      clearTimeout(connectionTimeout)
      console.error('❌ WebSocket error:', error)
    }

    ws.onclose = (event) => {
      clearTimeout(connectionTimeout)
      console.log(`🔌 Disconnected (code: ${event.code})`)
      setConnectionStatus('disconnected')
      
      // Simple reconnect if analyzing
      if (isAnalyzing && retryCount < 20) {
        const delay = Math.min(2000 + (retryCount * 1000), 10000)
        setError(`Reconnecting in ${Math.ceil(delay/1000)}s... (${retryCount + 1}/20)`)
        
        setTimeout(() => {
          connectWebSocket(retryCount + 1)
        }, delay)
      } else if (retryCount >= 20) {
        setError('❌ Failed to maintain connection. Backend may be down.')
        setIsAnalyzing(false)
      }
    }

    wsRef.current = ws
  }

  // Capture and send frames
  const startFrameCapture = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    intervalRef.current = setInterval(() => {
      if (videoRef.current && canvasRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        const canvas = canvasRef.current
        const video = videoRef.current
        
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
        
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.drawImage(video, 0, 0)
          
          // Convert to JPEG and send
          canvas.toBlob((blob) => {
            if (blob && wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(blob)
            }
          }, 'image/jpeg', 0.8)
        }
      }
    }, 100) // ~10 FPS
  }

  // Stop analysis
  const stopAnalysis = () => {
    // Stop video stream
    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks()
      tracks.forEach(track => track.stop())
      videoRef.current.srcObject = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Stop frame capture
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    // Stop any ongoing speech
    if (synthRef.current) {
      synthRef.current.cancel()
    }

    setIsAnalyzing(false)
    setConnectionStatus('disconnected')
    setLastRecommendation('')
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAnalysis()
    }
  }, [])

  return (
    <main className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold text-center mb-6">Poker GTO Vision</h1>
        
        {/* Status indicator */}
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' :
            connectionStatus === 'connecting' ? 'bg-yellow-500' :
            'bg-red-500'
          }`} />
          <span className="text-sm">
            {connectionStatus === 'connected' ? 'Connected' :
             connectionStatus === 'connecting' ? 'Connecting...' :
             'Disconnected'}
          </span>
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-red-500 text-white p-4 rounded-lg mb-4">
            {error}
          </div>
        )}

        {/* Video display */}
        <div className="relative max-w-2xl mx-auto">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full rounded-lg bg-black"
          />
          
          {/* Status overlay */}
          {isAnalyzing && (
            <div className="absolute top-4 left-4 bg-black bg-opacity-70 px-4 py-2 rounded-lg">
              <div className="flex items-center gap-2">
                {lastRecommendation ? (
                  <>
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium">HERO TURN</span>
                  </>
                ) : (
                  <>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="text-sm">Analyzing...</span>
                  </>
                )}
              </div>
              {lastRecommendation && (
                <div className="mt-2 text-lg font-bold text-yellow-400">
                  🔊 {lastRecommendation}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Control buttons */}
        <div className="flex justify-center gap-4 mt-6">
          {!isAnalyzing ? (
            <button
              onClick={startCamera}
              className="px-8 py-4 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-lg transition-colors"
            >
              Start Analysis
            </button>
          ) : (
            <button
              onClick={stopAnalysis}
              className="px-8 py-4 bg-red-600 hover:bg-red-700 rounded-lg font-semibold text-lg transition-colors"
            >
              Stop
            </button>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 max-w-2xl mx-auto text-sm text-gray-400">
          <h2 className="font-semibold text-white mb-2">Instructions:</h2>
          <ol className="list-decimal list-inside space-y-1">
            <li>Point your phone camera at the poker table on your laptop screen</li>
            <li>Press Start Analysis to begin</li>
            <li>When the hero turn is detected, you will hear audio recommendations</li>
            <li>Keep the camera steady for best results</li>
          </ol>
        </div>
      </div>
    </main>
  )
}
