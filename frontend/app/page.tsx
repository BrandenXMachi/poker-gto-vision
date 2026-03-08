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

  // Password gate
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [passwordInput, setPasswordInput] = useState('')
  const [passwordError, setPasswordError] = useState('')

  const PASS_HASH = '243144ab0e9df2ce4dc94c6967aab8642e37299bcb4aef11b1e02d1e86fbcf63'

  const hashPassword = async (text: string): Promise<string> => {
    const encoder = new TextEncoder()
    const data = encoder.encode(text)
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data)
    return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('')
  }

  const handlePasswordSubmit = async () => {
    const hashed = await hashPassword(passwordInput)
    if (hashed === PASS_HASH) {
      setIsAuthenticated(true)
      setShowPasswordModal(false)
      setPasswordInput('')
      setPasswordError('')
      startCamera()
    } else {
      setPasswordError('Incorrect password. Access denied.')
      setPasswordInput('')
    }
  }

  const [isCameraActive, setIsCameraActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string>('')
  const [capturedImage, setCapturedImage] = useState<string>('')
  const [isInPosition, setIsInPosition] = useState<boolean>(true)
  const [selectedBlinds, setSelectedBlinds] = useState<string>('0.02/0.05')
  const [villainPositionPreflop, setVillainPositionPreflop] = useState<string>('UTG')
  const [selectedPosition, setSelectedPosition] = useState<string>('BTN')
  const [aiMode, setAiMode] = useState<'tr' | 'flop' | 'preflop'>('preflop')
  const [isOpenRaise, setIsOpenRaise] = useState<boolean>(false)
  const [is3BetToggle, setIs3BetToggle] = useState<boolean>(false)
  
  // Flop Mode specific states
  const [flopHeroPosition, setFlopHeroPosition] = useState<string>('IP')  // "IP" or "OOP"
  const [flopVillainPosition, setFlopVillainPosition] = useState<string>('BTN')  // Position
  const [flopPreflopPotType, setFlopPreflopPotType] = useState<string>('open_raise')  // "open_raise", "3bet", "4bet"
  
  // Context inheritance for mode transitions
  const [inheritedContext, setInheritedContext] = useState<{
    fromMode: string
    heroPosition: string
    villainPosition: string
    preflopAction?: string
    preflopRecommendation?: string
    heroCards?: string[]
    flopCards?: string[]
    flopAction?: string
    flopRecommendation?: string
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
  const [boardDescription, setBoardDescription] = useState<string>('')
  const [handDescription, setHandDescription] = useState<string>('')
  
  // Detailed info for navigation to details page
  const [detailedInfo, setDetailedInfo] = useState<DetailedInfo | null>(null)
  
  // Flop metrics (fold probability + EFE) for badge display
  const [flopFoldProbability, setFlopFoldProbability] = useState<string>('')
  const [flopEfeDollars, setFlopEfeDollars] = useState<string>('')

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

  // Smart pot type inference: Preflop recommendation → Flop pot type
  // Based on user's 3 rules:
  // Rule 1: Assume hero did suggested action (unless open raise)
  // Rule 2: Villain who opened called our 3-bet
  // Rule 3: Villain who 3-bet called our 4-bet
  const mapPreflopToPotType = (preflopAction: string): string => {
    const actionLower = preflopAction.toLowerCase()
    
    // Rule 1 + Rule 3: If we 4-bet → assume villain called → "4bet" pot
    if (actionLower.includes('4-bet') || actionLower.includes('4bet')) {
      return '4bet'
    }
    
    // Rule 1 + Rule 2: If we 3-bet → assume villain called → "3bet" pot
    if (actionLower.includes('3-bet') || actionLower.includes('3bet')) {
      return '3bet'
    }
    
    // Rule 1: If we called villain's raise → "open_raise" pot (single raised pot)
    if (actionLower.includes('call')) {
      return 'open_raise'
    }
    
    // Default: "open_raise" pot (most common)
    return 'open_raise'
  }

  // Determine IP/OOP from positions
  const determineIPorOOP = (heroPos: string, villainPos: string): string => {
    const positions = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
    const heroIndex = positions.indexOf(heroPos)
    const villainIndex = positions.indexOf(villainPos)
    
    // If hero is later in position order, they're IP
    return heroIndex > villainIndex ? 'IP' : 'OOP'
  }

  // Handle position click when hero opened - transfers to Flop with context
  const handleOpenRaisePositionClick = (villainPos: string) => {
    // Determine pot type based on 3-Bet toggle
    const potType = is3BetToggle ? '3bet' : 'open_raise'
    
    // Calculate IP/OOP
    const ipOrOop = determineIPorOOP(selectedPosition, villainPos)
    
    console.log('📋 Open raise → Flop transfer:', {
      heroPosition: selectedPosition,
      villainPosition: villainPos,
      heroIPorOOP: ipOrOop,
      potType: potType,
      toggleState: is3BetToggle
    })
    
    const contextData = {
      fromMode: 'preflop',
      heroPosition: ipOrOop,
      villainPosition: villainPos,
      preflopAction: potType,
      preflopRecommendation: `Opened from ${selectedPosition}, ${is3BetToggle ? 'villain 3-bet and we called' : 'villain called'}`
    }
    
    // Set flop states
    setFlopHeroPosition(ipOrOop)
    setFlopVillainPosition(villainPos)
    setFlopPreflopPotType(potType)
    setInheritedContext(contextData)
    
    // Clear UI and switch to Flop mode
    setCapturedImage('')
    setAction('')
    setIs3BetToggle(false)  // Reset toggle
    setAiMode('flop')
    startCamera()
  }

  // Continue to Flop mode with context
  const continueToFlop = () => {
    if (!action) return
    
    // NOTE: This function is now only called for non-open-raise scenarios
    // Open raise scenarios use handleOpenRaisePositionClick instead
    
    // We have a villain - pass context with smart pot type inference
    const potType = mapPreflopToPotType(action)
    const ipOrOop = determineIPorOOP(selectedPosition, villainPositionPreflop)
    
    console.log('📋 Passing context to Flop:', {
      heroPosition: ipOrOop,
      villainPosition: villainPositionPreflop,
      potType: potType,
      recommendation: action
    })
    
    const contextData = {
      fromMode: 'preflop',
      heroPosition: ipOrOop,
      villainPosition: villainPositionPreflop,
      preflopAction: potType,
      preflopRecommendation: action
    }
    
    // Set all flop states BEFORE changing mode
    setFlopHeroPosition(ipOrOop)
    setFlopVillainPosition(villainPositionPreflop)
    setFlopPreflopPotType(potType)
    setInheritedContext(contextData)
    
    // Clear UI states
    setCapturedImage('')
    setAction('')
    
    // Change mode and start camera
    setAiMode('flop')
    startCamera()
  }

  // Continue to T/R mode with context from Flop
  const continueToTR = () => {
    if (!action) return
    
    // Pass flop context to T/R mode (even if fold recommended - for learning)
    const contextData = {
      fromMode: 'flop',
      heroPosition: flopHeroPosition,  // "IP" or "OOP"
      villainPosition: flopVillainPosition,
      heroCards: heroCards,  // Save hero's 2 cards from flop
      flopCards: boardCards.slice(0, 3),  // Save first 3 board cards (flop only)
      flopAction: flopPreflopPotType,
      flopRecommendation: action
    }
    
    console.log('📋 Passing context to T/R:', contextData)
    
    setInheritedContext(contextData)
    setAiMode('tr')
    setCapturedImage('')
    setAction('')
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
      
      // For Flop Mode, pass manual inputs with new hybrid analyzer
      if (aiMode === 'flop') {
        formData.append('hero_position', flopHeroPosition)  // "IP" or "OOP"
        formData.append('villain_position', flopVillainPosition)  // "UTG", "MP", etc.
        formData.append('preflop_pot_type', flopPreflopPotType)  // "open_raise", "3bet", "4bet"
        formData.append('blinds', selectedBlinds)
      } else if (aiMode === 'preflop') {
        // Preflop Mode - pass hero position, villain position, blinds, and open raise flag
        formData.append('position', positionToUse)
        formData.append('villain_position', isOpenRaise ? 'NONE' : villainPositionPreflop)
        formData.append('blinds', selectedBlinds)
        formData.append('is_open_raise', isOpenRaise ? 'true' : 'false')
      } else if (aiMode === 'tr') {
        // T/R Mode - pass blinds and context if available
        formData.append('blinds', selectedBlinds)
        
        // If we have context from flop, pass the known cards and positional info
        if (inheritedContext && inheritedContext.fromMode === 'flop') {
          if (inheritedContext.heroCards && inheritedContext.heroCards.length === 2) {
            formData.append('hero_cards', JSON.stringify(inheritedContext.heroCards))
            console.log('✅ Passing hero cards from flop:', inheritedContext.heroCards)
          }
          if (inheritedContext.flopCards && inheritedContext.flopCards.length === 3) {
            formData.append('flop_cards', JSON.stringify(inheritedContext.flopCards))
            console.log('✅ Passing flop cards:', inheritedContext.flopCards)
          }
          if (inheritedContext.heroPosition) {
            formData.append('hero_position', inheritedContext.heroPosition)
          }
          if (inheritedContext.villainPosition) {
            formData.append('villain_position', inheritedContext.villainPosition)
          }
          if (inheritedContext.flopAction) {
            formData.append('flop_action', inheritedContext.flopAction)
          }
        }
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
        
        // For T/R mode, get variables from analysis object instead of recommendation
        if (aiMode === 'tr' && data.analysis) {
          setPotOdds(data.analysis.pot_odds?.percent || 'N/A')
          setHandEquity(data.analysis.equity?.value || 'N/A')
          setImpliedOdds('N/A')  // Not calculated in T/R mode
          setFoldEquity('N/A')   // Not calculated in T/R mode
          setExpectedValue(data.analysis.expected_value?.value || 'N/A')
        } else {
          // For other modes, use recommendation object
          setPotOdds(rec.pot_odds?.value || rec.pot_odds || 'N/A')
          setHandEquity(rec.hand_equity?.value || rec.hand_equity || 'N/A')
          setImpliedOdds(rec.implied_odds?.value || rec.implied_odds || 'N/A')
          setFoldEquity(rec.fold_equity?.value || rec.fold_equity || 'N/A')
          setExpectedValue(rec.expected_value?.value || rec.expected_value || 'N/A')
        }
        
        setPotSize(rec.pot_size || 'N/A')
        setReasoning(rec.reasoning || '')
        setDetailedInfo(data.detailed_info || null)
        
        // Extract card data from response
        if (data.extracted_data) {
          setHeroCards(data.extracted_data.hero_cards || [])
          setBoardCards(data.extracted_data.board_cards || [])
          setStreet(data.extracted_data.street || '')
          setBoardDescription(data.extracted_data.board_description || '')
          setHandDescription(data.extracted_data.hand_description || '')
        }
        
        // Extract flop metrics (fold probability + EFE) for badge display
        if (aiMode === 'flop' && data.metrics) {
          setFlopFoldProbability(data.metrics.fold_probability || '')
          setFlopEfeDollars(data.metrics.efe_dollars || '')
        }
        
        // Speak the action for all modes
        speak(rec.action)
      } else if (data.hero_turn === false) {
        setError("Not hero's turn detected. Try capturing when action is on you.")
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
    <main className="min-h-screen text-white flex" style={{background: '#0f0e1a'}}>
      {/* Ambient background blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="blob w-96 h-96 bg-blue-600" style={{top: '-5%', left: '-5%', animationDelay: '0s'}} />
        <div className="blob w-80 h-80 bg-purple-600" style={{top: '20%', right: '-5%', animationDelay: '2s'}} />
        <div className="blob w-64 h-64 bg-emerald-500" style={{bottom: '10%', left: '20%', animationDelay: '4s'}} />
        <div className="blob w-72 h-72 bg-orange-500" style={{bottom: '-5%', right: '10%', animationDelay: '1s'}} />
      </div>

      <div className="flex-1 px-4 py-6 relative z-10">
        <div className="container mx-auto max-w-4xl">

          {/* ── LANDING PAGE (camera not active) ── */}
          {!isCameraActive && !capturedImage && (
            <div className="mb-2">
              {/* Hero Section */}
              <div className="text-center mb-10 pt-4">
                {/* Floating card art */}
                <div className="flex justify-center items-end gap-3 mb-6 h-28 select-none">
                  <div className="animate-float-slow text-6xl" style={{animationDelay: '0.2s'}}>🂡</div>
                  <div className="animate-float text-8xl" style={{animationDelay: '0s'}}>🃑</div>
                  <div className="animate-float-slow text-6xl" style={{animationDelay: '0.8s'}}>🂱</div>
                  <div className="animate-float text-8xl drop-shadow-2xl" style={{animationDelay: '0.4s'}}>🂺</div>
                  <div className="animate-float-slow text-6xl" style={{animationDelay: '1.2s'}}>🃁</div>
                </div>

                <h1 className="text-6xl font-black mb-3 leading-tight">
                  <span className="bg-gradient-to-r from-yellow-300 via-orange-400 to-red-400 bg-clip-text text-transparent drop-shadow">
                    Poker Strategy
                  </span>
                </h1>
                <p className="text-xl text-white/70 font-medium mb-2">
                  AI-powered GTO advice • Point. Capture. Win.
                </p>
                <div className="flex justify-center gap-2 flex-wrap mb-8">
                  <span className="px-3 py-1 rounded-full text-sm font-bold bg-blue-500/20 border border-blue-400/30 text-blue-300">🎯 Preflop GTO</span>
                  <span className="px-3 py-1 rounded-full text-sm font-bold bg-purple-500/20 border border-purple-400/30 text-purple-300">🎴 Flop Strategy</span>
                  <span className="px-3 py-1 rounded-full text-sm font-bold bg-emerald-500/20 border border-emerald-400/30 text-emerald-300">📊 Turn/River Math</span>
                </div>
              </div>

              {/* Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                {/* Preflop Card */}
                <div className="clay-card-orange card-shine p-5 text-center hover:scale-105 transition-transform duration-200">
                  <div className="text-5xl mb-3 animate-float-slow">🎯</div>
                  <h3 className="text-lg font-black text-orange-300 mb-2">Preflop GTO</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    Instant open/call/3-bet/fold decisions powered by real GTO range charts
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1 justify-center">
                    <span className="text-xs px-2 py-1 rounded-full bg-orange-500/20 text-orange-300 font-bold">AA-22</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-orange-500/20 text-orange-300 font-bold">AKs</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-orange-500/20 text-orange-300 font-bold">6 Positions</span>
                  </div>
                </div>

                {/* Flop Card */}
                <div className="clay-card-purple card-shine p-5 text-center hover:scale-105 transition-transform duration-200">
                  <div className="text-5xl mb-3 animate-float">🎴</div>
                  <h3 className="text-lg font-black text-purple-300 mb-2">Flop AI</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    Gemini reads your cards + board. AI gives optimal bet, check, or fold
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1 justify-center">
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-300 font-bold">IP/OOP</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-300 font-bold">3-Bet Pots</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-300 font-bold">Board Texture</span>
                  </div>
                </div>

                {/* T/R Card */}
                <div className="clay-card-green card-shine p-5 text-center hover:scale-105 transition-transform duration-200">
                  <div className="text-5xl mb-3 animate-float-reverse">📊</div>
                  <h3 className="text-lg font-black text-emerald-300 mb-2">Turn/River</h3>
                  <p className="text-sm text-white/70 leading-relaxed">
                    Pure math: pot odds, equity from outs, EV calculations in real-time
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1 justify-center">
                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">Pot Odds</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">Outs</span>
                    <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-bold">+EV/-EV</span>
                  </div>
                </div>
              </div>

              {/* How It Works */}
              <div className="clay-card p-6 mb-8">
                <h2 className="text-center text-lg font-black text-white/90 mb-5">⚡ How It Works</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex flex-col items-center text-center gap-2">
                    <div className="w-12 h-12 rounded-2xl bg-blue-500/30 border border-blue-400/40 flex items-center justify-center text-2xl font-black text-blue-300 shadow-lg">1</div>
                    <div className="text-3xl animate-float-slow">📱</div>
                    <p className="text-sm text-white/70 font-medium">Open on your phone & tap <span className="text-white font-bold">Start Camera</span></p>
                  </div>
                  <div className="flex flex-col items-center text-center gap-2">
                    <div className="w-12 h-12 rounded-2xl bg-purple-500/30 border border-purple-400/40 flex items-center justify-center text-2xl font-black text-purple-300 shadow-lg">2</div>
                    <div className="text-3xl animate-float">🃏</div>
                    <p className="text-sm text-white/70 font-medium">Point camera at your poker table & <span className="text-white font-bold">capture</span></p>
                  </div>
                  <div className="flex flex-col items-center text-center gap-2">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500/30 border border-emerald-400/40 flex items-center justify-center text-2xl font-black text-emerald-300 shadow-lg">3</div>
                    <div className="text-3xl animate-float-reverse">🏆</div>
                    <p className="text-sm text-white/70 font-medium">Get instant <span className="text-white font-bold">GTO decision</span> with reasoning</p>
                  </div>
                </div>
              </div>

              {/* Stats bar */}
              <div className="grid grid-cols-3 gap-3 mb-8">
                <div className="clay-card-blue p-4 text-center">
                  <div className="text-3xl font-black text-blue-300">6</div>
                  <div className="text-xs text-white/60 mt-1">Positions</div>
                </div>
                <div className="clay-card-purple p-4 text-center">
                  <div className="text-3xl font-black text-purple-300">3</div>
                  <div className="text-xs text-white/60 mt-1">AI Modes</div>
                </div>
                <div className="clay-card-green p-4 text-center">
                  <div className="text-3xl font-black text-emerald-300">∞</div>
                  <div className="text-xs text-white/60 mt-1">Hands</div>
                </div>
              </div>
            </div>
          )}

          {/* Title shown when camera is active */}
          {(isCameraActive || capturedImage) && (
            <div className="text-center mb-6">
              <h1 className="text-4xl font-extrabold bg-gradient-to-r from-yellow-300 via-orange-400 to-red-400 bg-clip-text text-transparent mb-1">
                🎰 Poker Strategy
              </h1>
            </div>
          )}
          
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
                  <div className="text-xs opacity-75 mt-1">Hybrid AI</div>
                </button>
                <button
                  onClick={() => setAiMode('tr')}
                  className={`py-4 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 ${
                    aiMode === 'tr'
                      ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg scale-105'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  <div className="text-2xl mb-1">📊</div>
                  <div>T/R</div>
                  <div className="text-xs opacity-75 mt-1">Turn/River</div>
                </button>
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-purple-400 font-bold capitalize">{aiMode}</span>
                {aiMode === 'tr' && ' - 📊 Turn/River math'}
                {aiMode === 'preflop' && ' - 🎯 Preflop GTO ranges'}
                {aiMode === 'flop' && ' - 🎴 Gemini 2.0 + 3.0 hybrid'}
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

          {/* Main recommendation display - Only for T/R Mode */}
          {action && aiMode === 'tr' && (
            <div className="bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 border-emerald-400/30 text-white p-8 rounded-2xl mb-6 shadow-2xl border-2 backdrop-blur">
              <div className="text-center mb-2">
                <p className="text-sm font-semibold text-white/80 mb-2">📊 T/R ANALYSIS</p>
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
              
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">Pot Odds</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{potOdds}</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm p-5 rounded-xl border border-white/20 hover:bg-white/15 transition-all">
                  <div className="text-white/80 text-xs font-semibold uppercase tracking-wider mb-2">Hand Equity</div>
                  <div className="text-2xl md:text-3xl font-bold text-white drop-shadow">{handEquity}</div>
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

              {/* Position Selector for Open Raise - OR - Continue Button */}
              {isOpenRaise ? (
                <>
                  {/* 3-Bet Toggle */}
                  <div className="mb-4 flex justify-center">
                    <button
                      onClick={() => setIs3BetToggle(!is3BetToggle)}
                      className={`py-3 px-6 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                        is3BetToggle
                          ? 'bg-gradient-to-r from-red-500 to-pink-500 text-white scale-105 ring-2 ring-white'
                          : 'bg-gray-700/80 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {is3BetToggle ? '🔥 3-BET MODE (Villain 3-bet, we called)' : '📢 Villain Called Our Open?'}
                    </button>
                  </div>

                  {/* Position List */}
                  <div className="bg-white/5 backdrop-blur-sm p-5 rounded-xl border border-white/20 mb-4">
                    <h4 className="text-center text-sm font-bold text-white/80 mb-3">
                      Select Villain Position to Continue to Flop
                    </h4>
                    <div className="grid grid-cols-6 gap-2">
                      {/* Show positions that are after hero's position */}
                      {['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
                        .filter(pos => {
                          const positions = ['SB', 'BB', 'UTG', 'MP', 'CO', 'BTN']
                          const heroIndex = positions.indexOf(selectedPosition)
                          const posIndex = positions.indexOf(pos)
                          return posIndex !== heroIndex  // Exclude hero's own position
                        })
                        .map((pos) => (
                          <button
                            key={pos}
                            onClick={() => handleOpenRaisePositionClick(pos)}
                            className="py-3 px-2 rounded-xl font-bold text-xs bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white transition-all transform hover:scale-110 shadow-lg"
                          >
                            {pos}
                          </button>
                        ))}
                    </div>
                    <p className="text-center text-xs text-white/70 mt-3">
                      {is3BetToggle 
                        ? '🔥 Click a position → Assumes villain 3-bet, we called (3-Bet Pot)'
                        : '📢 Click a position → Assumes villain called our open (Single Raised Pot)'}
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <button
                    onClick={continueToFlop}
                    className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2"
                  >
                    <span>Continue to Flop</span>
                    <span className="text-2xl">🎴 →</span>
                  </button>
                  {action.toLowerCase().includes('fold') && (
                    <p className="text-center text-sm text-white/70 mt-2">
                      💡 Continue anyway to see flop analysis (assumes action checks through)
                    </p>
                  )}
                </>
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

              {/* Flop Metrics Badge Row — Fold Probability + EFE (Option B) */}
              {(flopFoldProbability || flopEfeDollars) && (
                <div className="flex gap-3 justify-center mb-4">
                  {flopFoldProbability && (
                    <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
                      <span className="text-xs text-white/60 font-semibold uppercase tracking-wider">Fold Prob</span>
                      <span className="text-base font-black text-pink-300">{flopFoldProbability}</span>
                    </div>
                  )}
                  {flopEfeDollars && flopEfeDollars !== '$0.00' && (
                    <div className="flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
                      <span className="text-xs text-white/60 font-semibold uppercase tracking-wider">Fold EV</span>
                      <span className="text-base font-black text-emerald-300">{flopEfeDollars}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Board and Hand Analysis - Show detailed descriptions */}
              {(boardDescription || handDescription) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  {/* Board Analysis */}
                  {boardDescription && (
                    <div className="bg-cyan-500/10 backdrop-blur-sm p-4 rounded-xl border border-cyan-400/30">
                      <div className="text-xs text-cyan-300 font-bold uppercase tracking-wider mb-2">🎴 Board:</div>
                      <div className="text-sm text-white/90 whitespace-pre-line">
                        {boardDescription}
                      </div>
                    </div>
                  )}
                  
                  {/* Hand Analysis */}
                  {handDescription && (
                    <div className="bg-yellow-500/10 backdrop-blur-sm p-4 rounded-xl border border-yellow-400/30">
                      <div className="text-xs text-yellow-300 font-bold uppercase tracking-wider mb-2">🃏 Hero&apos;s Hand:</div>
                      <div className="text-sm text-white/90 whitespace-pre-line">
                        {handDescription}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Continue to T/R Button - Always show, even if fold recommended */}
              <button
                onClick={continueToTR}
                className="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center justify-center gap-2"
              >
                <span>Continue to T/R</span>
                <span className="text-2xl">📊 →</span>
              </button>
              {action.toLowerCase().includes('fold') && (
                <p className="text-center text-sm text-white/70 mt-2">
                  💡 Continue anyway to see turn/river analysis (assumes action checks through)
                </p>
              )}
            </div>
          )}

          {/* Context Indicator - Show when flop mode has inherited context from Preflop */}
          {isCameraActive && !capturedImage && aiMode === 'flop' && inheritedContext && inheritedContext.fromMode === 'preflop' && (
            <div className="mb-6 bg-gradient-to-r from-blue-600 to-purple-600 p-5 rounded-2xl border-2 border-blue-400/30 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">
                    📋 Context from Preflop
                  </h3>
                  <div className="text-sm text-white/90 space-y-1">
                    <p>• Position: <span className="font-bold">{inheritedContext.heroPosition}</span> vs Villain at <span className="font-bold">{inheritedContext.villainPosition}</span></p>
                    {inheritedContext.preflopAction && (
                      <p>• Action: <span className="font-bold capitalize">{inheritedContext.preflopAction.replace(/_/g, ' ')}</span></p>
                    )}
                    {inheritedContext.preflopRecommendation && (
                      <p>• You {inheritedContext.preflopRecommendation}</p>
                    )}
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

          {/* Context Indicator - Show when T/R mode has inherited context from Flop */}
          {isCameraActive && !capturedImage && aiMode === 'tr' && inheritedContext && inheritedContext.fromMode === 'flop' && (
            <div className="mb-6 bg-gradient-to-r from-emerald-600 to-teal-600 p-5 rounded-2xl border-2 border-emerald-400/30 shadow-xl">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-white mb-2">
                    📋 Cards from Flop Analysis
                  </h3>
                  <div className="text-sm text-white/90 space-y-1">
                    {inheritedContext.heroCards && inheritedContext.heroCards.length === 2 && (
                      <p>• Your Hand: <span className="font-bold">{inheritedContext.heroCards.join(' ')}</span></p>
                    )}
                    {inheritedContext.flopCards && inheritedContext.flopCards.length === 3 && (
                      <p>• Flop: <span className="font-bold">{inheritedContext.flopCards.join(' ')}</span></p>
                    )}
                    <p>• Position: <span className="font-bold">{inheritedContext.heroPosition}</span> vs <span className="font-bold">{inheritedContext.villainPosition}</span></p>
                    <p className="text-xs opacity-75 mt-2">Gemini will only identify turn/river card + pot/call amounts</p>
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
                2️⃣ Preflop Pot Type
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <button
                  onClick={() => setFlopPreflopPotType('open_raise')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopPotType === 'open_raise'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Open Raise Pot
                </button>
                <button
                  onClick={() => setFlopPreflopPotType('3bet')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopPotType === '3bet'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  3-Bet Pot
                </button>
                <button
                  onClick={() => setFlopPreflopPotType('4bet')}
                  className={`py-3 px-3 rounded-xl font-bold text-sm transition-all transform hover:scale-105 shadow-lg ${
                    flopPreflopPotType === '4bet'
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white scale-105 ring-2 ring-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  4-Bet Pot
                </button>
              </div>
              <p className="text-center text-sm text-gray-400 mt-3">
                Selected: <span className="text-purple-400 font-bold capitalize">{flopPreflopPotType.replace(/_/g, ' ')}</span>
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

          {/* Blinds Selector - Show for T/R and Preflop Modes */}
          {isCameraActive && !isAnalyzing && !capturedImage && (aiMode === 'tr' || aiMode === 'preflop') && (
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

          {/* T/R Mode: Simple Capture Button */}
          {isCameraActive && !capturedImage && !isAnalyzing && aiMode === 'tr' && (
            <div className="mb-6">
              <button
                onClick={() => captureAndAnalyze()}
                className="w-full py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                📸 Capture & Analyze T/R
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
                aiMode === 'tr' 
                  ? 'bg-gradient-to-br from-emerald-900/95 to-teal-900/95'
                  : aiMode === 'preflop'
                  ? 'bg-gradient-to-br from-orange-900/95 to-amber-900/95'
                  : 'bg-gradient-to-br from-purple-900/95 to-indigo-900/95'
              }`}>
                <div className="text-center">
                  <div className={`w-20 h-20 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-6 ${
                    aiMode === 'tr' ? 'border-emerald-400' : aiMode === 'preflop' ? 'border-orange-400' : 'border-purple-400'
                  }`}></div>
                  <div className="text-2xl font-bold text-white drop-shadow-lg">
                    {aiMode === 'tr' ? '📊 T/R Analysis...' : aiMode === 'preflop' ? '🎯 Preflop GTO...' : '🎴 Flop GTO Analysis...'}
                  </div>
                  <div className={`mt-2 ${aiMode === 'tr' ? 'text-emerald-300' : aiMode === 'preflop' ? 'text-orange-300' : 'text-purple-300'}`}>
                    {aiMode === 'tr' ? 'Calculating pot odds...' : aiMode === 'preflop' ? 'Checking GTO ranges...' : 'Gemini extracting cards → Applying flop GTO strategy...'}
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
                onClick={() => {
                  if (isAuthenticated) {
                    startCamera()
                  } else {
                    setShowPasswordModal(true)
                  }
                }}
                className="clay-btn px-14 py-5 bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 hover:from-yellow-300 hover:via-orange-400 hover:to-red-400 text-white font-black text-xl tracking-wide transition-all shadow-2xl hover:scale-110 active:scale-95"
              >
                🔐 Initiate Protocol
              </button>
            ) : null}
          </div>
        </div>
      </div>
      {/* ── PASSWORD MODAL ── */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(8px)'}}>
          <div className="clay-card-blue card-shine p-8 w-full max-w-sm text-center">
            <div className="text-5xl mb-4 animate-float">🔐</div>
            <h2 className="text-2xl font-black text-white mb-1">Access Required</h2>
            <p className="text-sm text-white/60 mb-6">Enter the protocol password to continue</p>

            <input
              type="password"
              value={passwordInput}
              onChange={e => { setPasswordInput(e.target.value); setPasswordError('') }}
              onKeyDown={e => e.key === 'Enter' && handlePasswordSubmit()}
              placeholder="••••••••"
              autoFocus
              className="w-full px-4 py-3 rounded-2xl bg-white/10 border-2 border-white/20 text-white text-center text-xl tracking-widest placeholder-white/30 focus:outline-none focus:border-yellow-400/60 transition-colors mb-3"
            />

            {passwordError && (
              <p className="text-red-400 text-sm font-semibold mb-3">⚠️ {passwordError}</p>
            )}

            <div className="flex gap-3 mt-2">
              <button
                onClick={() => { setShowPasswordModal(false); setPasswordInput(''); setPasswordError('') }}
                className="flex-1 py-3 rounded-2xl font-bold text-white/70 bg-white/10 hover:bg-white/20 border border-white/20 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handlePasswordSubmit}
                className="flex-1 clay-btn py-3 bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 text-white font-black rounded-2xl transition-all hover:scale-105"
              >
                Unlock 🚀
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
