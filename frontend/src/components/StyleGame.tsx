import React, { useState, useEffect } from 'react';
import { Clock, Trophy, Users, Play, RotateCcw, CheckCircle, XCircle } from 'lucide-react';
import { GameSession, GamePlayer, Product } from '../types';
import { api } from '../utils/api';
import Timer from './Timer';
import ClothesGrid from './ClothesGrid';
import Ranking from './Ranking';
import Leaderboard from './Leaderboard';
import { BACKEND_URL } from "../config";
// Fixed players for the VITON game (now handled by backend)
// const FIXED_PLAYERS = ['00002_00', '14684_00', '00154_00'];

interface VitonResult {
  player: string;
  cloth: string;
  resultImage: string;
  timestamp: Date;
  status: 'pending' | 'processing' | 'completed' | 'error';
  pickedBy?: string; // Who picked this combination
}

export function StyleGame({ products }: { products: Product[] }) {
  // --- State ---
  const [phase, setPhase] = useState<'lobby' | 'pick' | 'waiting' | 'rank' | 'leaderboard' | 'gameover'>('lobby');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [players, setPlayers] = useState<string[]>([]);
  const [clothesList, setClothesList] = useState<string[]>([]);
  const [currentRound, setCurrentRound] = useState(1);
  const [numRounds, setNumRounds] = useState(1);
  const [timer, setTimer] = useState(60);
  const [currentPickerIdx, setCurrentPickerIdx] = useState(0);
  const [currentRankerIdx, setCurrentRankerIdx] = useState(0);
  const [allPicks, setAllPicks] = useState<any>({});
  const [leaderboardKey, setLeaderboardKey] = useState(0);
  const [setupData, setSetupData] = useState({
    num_players: 3, // Default to 3 players
    num_rounds: 1,
    timer: 60,
    n_clothes: 10
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // VITON processing state
  const [vitonResults, setVitonResults] = useState<VitonResult[]>([]);
  const [processingQueue, setProcessingQueue] = useState<VitonResult[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // --- Process queue when it changes ---
  useEffect(() => {
    if (processingQueue.length > 0 && !isProcessing) {
      processNextInQueue();
    }
  }, [processingQueue, isProcessing]);

  // --- Helper function to get VITON result for a player-cloth combination ---
  const getVitonResult = (player: string, cloth: string): VitonResult | null => {
    return vitonResults.find(result => result.player === player && result.cloth === cloth) || null;
  };

  const handlePicksComplete = (playerPicks: any) => {
    console.log("Picks received:", playerPicks);
  
    setAllPicks((prev: any) => ({
      ...prev,
      [players[currentPickerIdx]]: playerPicks
    }));
  
    transitionAfterPick();
  };

  // --- Process VITON queue ---
  const processNextInQueue = async () => {
    if (processingQueue.length === 0) return;
    
    setIsProcessing(true);
    const nextItem = processingQueue[0];
    
    try {
      // Update status to processing
      setProcessingQueue(prev => prev.map(item => 
        item === nextItem ? { ...item, status: 'processing' } : item
      ));

      console.log(`Processing VITON for player: ${nextItem.player}, cloth: ${nextItem.cloth}`);

      // Create person image file from dataset
      const personImageUrl = `${BACKEND_URL}/people/${nextItem.player}.jpg`;
      console.log(`Fetching person image from: ${personImageUrl}`);
      const personImageBlob = await fetch(personImageUrl);
      if (!personImageBlob.ok) {
        throw new Error(`Failed to fetch person image: ${personImageBlob.status} ${personImageBlob.statusText}`);
      }
      const personImageFile = new File([await personImageBlob.blob()], `${nextItem.player}.jpg`, { type: 'image/jpeg' });
      console.log(`Created person image file: ${personImageFile.name}, size: ${personImageFile.size}`);

      // Create cloth image file from dataset
      const clothImageUrl = `${BACKEND_URL}/clothes/${nextItem.cloth}`;
      console.log(`Fetching cloth image from: ${clothImageUrl}`);
      const clothImageBlob = await fetch(clothImageUrl);
      if (!clothImageBlob.ok) {
        throw new Error(`Failed to fetch cloth image: ${clothImageBlob.status} ${clothImageBlob.statusText}`);
      }
      const clothImageFile = new File([await clothImageBlob.blob()], nextItem.cloth, { type: 'image/jpeg' });
      console.log(`Created cloth image file: ${clothImageFile.name}, size: ${clothImageFile.size}`);

      // Process VITON
      console.log(`Calling VITON API with person: ${personImageFile.name}, cloth: ${clothImageFile.name}`);
      const resultImageUrl = await api.tryOn(personImageFile, clothImageFile);
      console.log(`VITON API returned result URL: ${resultImageUrl}`);
      
      // Update result with completed status
      const completedResult: VitonResult = {
        ...nextItem,
        resultImage: resultImageUrl,
        status: 'completed'
      };

      setVitonResults(prev => [...prev, completedResult]);
      console.log('VITON result completed:', completedResult);

    } catch (err: any) {
      console.error('VITON processing error:', err);
      const errorResult: VitonResult = {
        ...nextItem,
        resultImage: '',
        status: 'error'
      };
      setVitonResults(prev => [...prev, errorResult]);
    } finally {
      // Remove from queue
      setProcessingQueue(prev => prev.slice(1));
      setIsProcessing(false);
    }
  };

  // --- Lobby: Start game and fetch clothes ---
  const startGame = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      console.log("Starting game with setup data:", setupData);
      
      const data = await api.startGame({
        num_players: Number(setupData.num_players),
        num_rounds: Number(setupData.num_rounds),
        timer: Number(setupData.timer),
        n_clothes: Number(setupData.n_clothes),
      });
      
      console.log("Received game data from backend:", data);
      console.log("Number of players received:", data.players?.length);
      console.log("Players:", data.players);
      
      setSessionId(data.session_id);
      setPlayers(data.players);
      setNumRounds(data.num_rounds);
      setTimer(data.timer);
      setCurrentRound(1);
      setCurrentPickerIdx(0);
      setCurrentRankerIdx(0);
      setAllPicks({});
      setPhase('pick');
      const clothes = await api.getTops({ session_id: data.session_id });
      setClothesList(clothes);
      
      // Initialize VITON processing
      setVitonResults([]);
      setProcessingQueue([]);
    } catch (err: any) {
      setError('Failed to start game: ' + err.message);
    }
    setLoading(false);
  };

  const transitionAfterPick = () => {
    // After a player completes their picks, go to loading phase to process VITON
    console.log(`[transitionAfterPick] Current picker index: ${currentPickerIdx}`);
    console.log(`[transitionAfterPick] Total players: ${players.length}`);
    console.log(`[transitionAfterPick] All picks so far:`, allPicks);
    
    setPhase('waiting');
    
    // Process VITON for the current player's picks
    const currentPlayer = players[currentPickerIdx];
    const currentPicks = allPicks[currentPlayer];
    
    console.log(`[transitionAfterPick] Current player: ${currentPlayer}`);
    console.log(`[transitionAfterPick] Current picks:`, currentPicks);
    
    if (currentPicks) {
      console.log(`Processing VITON for ${currentPlayer}'s picks:`, currentPicks);
      
      Object.entries(currentPicks).forEach(([targetPlayer, clothIndex]) => {
        console.log(`Processing VITON for: ${targetPlayer} => cloth index ${clothIndex}`);
    
        const cloth = clothesList[clothIndex as number];
    
        if (!cloth) {
          console.warn(`Cloth not found for index ${clothIndex}`);
          return;
        }
    
        const newItem: VitonResult = {
          player: targetPlayer,
          cloth: cloth,
          resultImage: '',
          timestamp: new Date(),
          status: 'pending',
          pickedBy: currentPlayer
        };
    
        setProcessingQueue(prev => [...prev, newItem]);
        console.log(`Added to VITON queue: ${targetPlayer} + ${cloth} (picked by ${currentPlayer})`);
      });
    }
    
    // Wait for VITON processing to complete for CURRENT PLAYER ONLY before moving to next player
    const checkProcessingComplete = () => {
      // Only check for VITON results that were picked by the current player
      const currentPlayerResults = vitonResults.filter(r => r.pickedBy === currentPlayer);
      const currentPlayerPending = currentPlayerResults.filter(r => r.status === 'pending' || r.status === 'processing').length;
      const currentPlayerInQueue = processingQueue.filter(r => r.pickedBy === currentPlayer).length;
      
      console.log(`[checkProcessingComplete] Current player: ${currentPlayer}`);
      console.log(`[checkProcessingComplete] Current player pending: ${currentPlayerPending}`);
      console.log(`[checkProcessingComplete] Current player in queue: ${currentPlayerInQueue}`);
      
      if (currentPlayerPending === 0 && currentPlayerInQueue === 0) {
        console.log(`All VITON processing completed for ${currentPlayer}, moving to next player`);
        console.log(`[checkProcessingComplete] Current picker index: ${currentPickerIdx}`);
        console.log(`[checkProcessingComplete] Players length: ${players.length}`);
        console.log(`[checkProcessingComplete] Condition: ${currentPickerIdx} < ${players.length - 1} = ${currentPickerIdx < players.length - 1}`);
        
        if (currentPickerIdx < players.length - 1) {
          const nextIndex = currentPickerIdx + 1;
          console.log(`[checkProcessingComplete] Moving to next player: index ${nextIndex} (${players[nextIndex]})`);
          setCurrentPickerIdx(nextIndex);
          setPhase('pick');
        } else {
          console.log(`[checkProcessingComplete] All players done, moving to ranking phase`);
          setCurrentPickerIdx(0);
          setPhase('rank');
        }
      } else {
        // Check again in 2 seconds
        setTimeout(checkProcessingComplete, 2000);
      }
    };
    
    // Start checking after a short delay
    setTimeout(checkProcessingComplete, 1000);
  };

  // --- Rank phase logic ---
  const handleRankingComplete = () => {
    // This function is now called when user manually submits ranking
    // The auto-advance system will handle progression automatically
    console.log(`Manual ranking completed for ${players[currentRankerIdx]}`);
    
    // The auto-advance useEffect will handle moving to the next player
    // No need to manually advance here
  };

  // --- Next round or game over ---
  const handleNextRound = () => {
    if (currentRound < numRounds) {
      setCurrentRound(currentRound + 1);
      setAllPicks({});
      setCurrentPickerIdx(0);
      setCurrentRankerIdx(0);
      // Reset VITON state for new round
      setVitonResults([]);
      setProcessingQueue([]);
      setIsProcessing(false);
      setPhase('pick');
    } else {
      setPhase('gameover');
    }
  };
  

  // --- Lobby UI ---
  if (phase === 'lobby') {
    return (
      <form onSubmit={startGame} className="max-w-xl mx-auto p-8 bg-white rounded-2xl shadow-md mt-8">
        <h2 className="text-2xl font-bold mb-4">Start a New VITON Game</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Players</label>
            <input type="number" min={2} max={10} value={setupData.num_players} onChange={e => setSetupData({ ...setupData, num_players: Number(e.target.value) })} className="w-full border border-gray-300 rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Rounds</label>
            <input type="number" min={1} max={20} value={setupData.num_rounds} onChange={e => setSetupData({ ...setupData, num_rounds: Number(e.target.value) })} className="w-full border border-gray-300 rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Timer (seconds)</label>
            <input type="number" min={10} max={1200} value={setupData.timer} onChange={e => setSetupData({ ...setupData, timer: Number(e.target.value) })} className="w-full border border-gray-300 rounded-lg px-3 py-2" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Clothes</label>
            <input type="number" min={2} max={50} value={setupData.n_clothes} onChange={e => setSetupData({ ...setupData, n_clothes: Number(e.target.value) })} className="w-full border border-gray-300 rounded-lg px-3 py-2" required />
          </div>
        </div>
        {error && <div className="text-red-500 text-center mt-4">{error}</div>}
        <button type="submit" className="mt-6 bg-gradient-to-r from-pink-500 to-purple-500 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:from-pink-600 hover:to-purple-600 transition-all flex items-center space-x-3 mx-auto" disabled={loading}>
          <Play size={24} />
          <span>{loading ? 'Starting...' : 'Start Game'}</span>
        </button>
      </form>
    );
  }
  // --- Waiting phase UI ---
  if (phase === 'waiting') {
    const currentPlayer = players[currentPickerIdx];
    
    // Safety check for undefined player
    if (!currentPlayer) {
      return (
        <div className="max-w-4xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
          <div className="text-center">
            <h2 className="text-xl font-bold text-red-600 mb-4">Error: Player not found</h2>
            <p className="text-gray-600">Please restart the game.</p>
          </div>
        </div>
      );
    }
    
    // Only show stats for current player's processing
    const currentPlayerResults = vitonResults.filter(r => r.pickedBy === currentPlayer);
    const currentPlayerCompleted = currentPlayerResults.filter(r => r.status === 'completed').length;
    const currentPlayerPending = currentPlayerResults.filter(r => r.status === 'pending' || r.status === 'processing').length;
    const currentPlayerInQueue = processingQueue.filter(r => r.pickedBy === currentPlayer).length;
    
    return (
      <div className="max-w-4xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
        <div className="flex flex-col lg:flex-row gap-6 items-center">
          {/* Left side - Current player image */}
          <div className="lg:w-1/3">
            <div className="text-center">
              <h2 className="text-xl font-bold text-pink-600 mb-4">Processing Results for: <span className="text-green-600">{currentPlayer}</span></h2>
              <div className="relative">
                <img 
                  src={`${BACKEND_URL}/people/${currentPlayer}.jpg`} 
                  alt={`${currentPlayer} original`} 
                  className="w-full h-64 object-contain rounded-lg shadow-md bg-gray-100"
                  onError={(e) => {
                    console.error(`Failed to load image for ${currentPlayer}`);
                    e.currentTarget.style.display = 'none';
                  }}
                />
                <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded text-xs font-bold">
                  {currentPlayer}
                </div>
              </div>
            </div>
          </div>

          {/* Right side - Processing status */}
          <div className="lg:w-2/3 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-pink-500 mb-6 mx-auto"></div>
            <h3 className="text-2xl font-bold text-gray-700 mb-4">Processing VITON Results...</h3>
            <p className="text-gray-600 text-lg mb-6">Please wait while we process the virtual try-on results for {currentPlayer}'s picks.</p>
            
            {/* Processing stats for current player only */}
            <div className="grid grid-cols-3 gap-4 text-center mb-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{currentPlayerInQueue}</div>
                <div className="text-sm text-blue-700">In Queue</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{currentPlayerPending}</div>
                <div className="text-sm text-yellow-700">Processing</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{currentPlayerCompleted}</div>
                <div className="text-sm text-green-700">Completed</div>
              </div>
            </div>
            
            {/* Current processing details for current player only */}
            {currentPlayerInQueue > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-700 mb-2">Currently Processing for {currentPlayer}:</h4>
                <div className="space-y-2">
                  {processingQueue.filter(r => r.pickedBy === currentPlayer).slice(0, 3).map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-sm">
                      <span className="text-gray-600">{item.player} + {item.cloth}</span>
                      <span className="text-blue-600">Status: {item.status}</span>
                    </div>
                  ))}
                  {currentPlayerInQueue > 3 && (
                    <div className="text-sm text-gray-500 text-center">
                      +{currentPlayerInQueue - 3} more items in queue
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Next player info */}
            {currentPickerIdx < players.length - 1 && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg">
                <p className="text-green-700 text-sm">
                  Next player: <span className="font-semibold">{players[currentPickerIdx + 1]}</span>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // --- Pick phase UI ---
  if (phase === 'pick') {
    const currentPlayer = players[currentPickerIdx];
    
    // Safety check for undefined player
    if (!currentPlayer) {
      return (
        <div className="max-w-6xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
          <div className="text-center">
            <h2 className="text-xl font-bold text-red-600 mb-4">Error: Player not found</h2>
            <p className="text-gray-600">Please restart the game.</p>
          </div>
        </div>
      );
    }
    
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
        {/* Original ClothesGrid */}
        <ClothesGrid
          sessionId={sessionId || ''}
          players={players}
          currentPlayer={currentPlayer}
          onPicksComplete={handlePicksComplete}
          clothesList={clothesList}
          roundNum={currentRound}
          timer={timer}
        />
      </div>
    );
  }

  // --- Rank phase UI ---
  if (phase === 'rank') {
    const currentPlayer = players[currentRankerIdx];
    
    // Safety check for undefined player
    if (!currentPlayer) {
      return (
        <div className="max-w-6xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
          <div className="text-center">
            <h2 className="text-xl font-bold text-red-600 mb-4">Error: Player not found</h2>
            <p className="text-gray-600">Please restart the game.</p>
          </div>
        </div>
      );
    }
    
    return (
      <Ranking
        sessionId={sessionId || ''}
        roundNum={currentRound}
        player={currentPlayer}
        clothesList={clothesList}
        vitonResults={vitonResults}
        onRankingComplete={handleRankingComplete}
      />
    );
  }

  // --- Leaderboard phase UI ---
  if (phase === 'leaderboard') {
    const completedResults = vitonResults.filter(r => r.status === 'completed');
    const errorResults = vitonResults.filter(r => r.status === 'error');

    return (
      <div>
        <Leaderboard key={leaderboardKey} sessionId={sessionId} />
        
        {/* VITON Results Gallery */}
        {vitonResults.length > 0 && (
          <div className="mt-8 max-w-6xl mx-auto p-6 bg-white rounded-2xl shadow-md">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold text-pink-600">All VITON Results</h2>
              <div className="text-sm text-gray-600">
                Completed: {completedResults.length} • Errors: {errorResults.length}
              </div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {vitonResults.map((result, idx) => (
                <div key={idx} className={`border rounded-lg p-4 shadow-md hover:shadow-lg transition-shadow ${
                  result.status === 'completed' ? 'bg-white' : 
                  result.status === 'error' ? 'bg-red-50' : 'bg-yellow-50'
                }`}>
                  {result.status === 'completed' ? (
                    <img 
                      src={result.resultImage} 
                      alt={`VITON result ${idx + 1}`} 
                      className="w-full h-64 object-contain rounded-md mb-3 bg-gray-50"
                    />
                  ) : (
                    <div className="w-full h-64 bg-gray-200 rounded-md mb-3 flex items-center justify-center">
                      <span className="text-gray-500">
                        {result.status === 'error' ? 'Processing Failed' : 'Processing...'}
                      </span>
                    </div>
                  )}
                  <div className="space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-gray-700">Player:</span>
                      <span className="text-sm text-gray-600">{result.player}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-gray-700">Cloth:</span>
                      <span className="text-sm text-gray-600 truncate">{result.cloth}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-gray-700">Status:</span>
                      <span className={`text-sm ${
                        result.status === 'completed' ? 'text-green-600' :
                        result.status === 'error' ? 'text-red-600' : 'text-yellow-600'
                      }`}>
                        {result.status}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-gray-700">Time:</span>
                      <span className="text-sm text-gray-600">
                        {result.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <button onClick={handleNextRound} className="mt-6 bg-pink-500 text-white px-6 py-3 rounded-xl font-medium hover:bg-pink-600 transition-colors">Next Round</button>
      </div>
    );
  }

  if (phase === 'gameover') {
    return <div className="text-center text-2xl font-bold mt-16">Game Over! Thanks for playing.</div>;
  }

  return null;
}