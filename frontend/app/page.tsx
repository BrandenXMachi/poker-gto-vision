'use client'

import { useEffect, useRef, useState } from 'react'

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const synthRef = useRef<SpeechSynthesis | null>(null)

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
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
      
      // Convert canvas to blob
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
        
        // Construct speech text
        let speechText = `${rec.action}.`
        if (rec.pot_size) speechText += ` Pot is ${rec.pot_size}.`
        if (rec.reasoning) speechText += ` ${rec.reasoning}.`
        
        speak(speechText)
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

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

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

        {/* Recommendation display */}
        {lastRecommendation && (
          <div className="bg-green-600 text-white p-4 rounded-lg mb-4 max-w-2xl mx-auto">
            <div className="text-lg font-bold">
              🔊 Recommendation: {lastRecommendation}
            </div>
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
          
          {/* Analyzing overlay */}
          {isAnalyzing && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <div className="text-xl font-bold">Analyzing...</div>
              </div>
            </div>
          )}
        </div>

        {/* Hidden canvas for photo capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Control buttons */}
        <div className="flex justify-center gap-4 mt-6">
          {!isCameraActive ? (
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
                  isAnalyzing
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {isAnalyzing ? '⏳ Analyzing...' : '📸 Capture & Analyze'}
              </button>
              <button
                onClick={stopCamera}
                className="px-8 py-4 bg-red-600 hover:bg-red-700 rounded-lg font-semibold text-lg transition-colors"
              >
                ❌ Stop Camera
              </button>
            </>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 max-w-2xl mx-auto text-sm text-gray-400">
          <h2 className="font-semibold text-white mb-2">Instructions:</h2>
          <ol className="list-decimal list-inside space-y-1">
            <li>Click &quot;Start Camera&quot; to activate your phone camera</li>
            <li>Point camera at the poker table on your laptop screen</li>
            <li>When it&apos;s your turn, click &quot;Capture & Analyze&quot;</li>
            <li>Wait a few seconds for the GTO recommendation</li>
            <li>You&apos;ll hear the recommendation spoken aloud</li>
          </ol>
        </div>
      </div>
    </main>
  )
}
