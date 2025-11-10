import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import Timer from './Timer';

const BACKEND_URL = "http://localhost:8000";

interface ClothesGridProps {
  sessionId: string;
  players: string[];
  currentPlayer: string;
  onPicksComplete: (picks: Record<string, number>) => void;
  clothesList: string[];
  roundNum: number;
  timer: number;
}

const ClothesGrid: React.FC<ClothesGridProps> = ({ sessionId, players, currentPlayer, onPicksComplete, clothesList, roundNum, timer }) => {
  const [clothes, setClothes] = useState<string[]>(clothesList);
  const [picks, setPicks] = useState<Record<string, number>>({});
  const [otherPlayers, setOtherPlayers] = useState<string[]>([]);
  const [currentOther, setCurrentOther] = useState(0);
  const [timeExpired, setTimeExpired] = useState(false);
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    setClothes(clothesList);
    const others = players.filter(p => p !== currentPlayer);
    setOtherPlayers(others);
    setPicks({});
    setCurrentOther(0);
    setTimeExpired(false);
    setCountdown(3);
    
    console.log(`ClothesGrid initialized for ${currentPlayer}:`);
    console.log(`- Total players: ${players.length}`);
    console.log(`- Other players: ${others.length} (${others.join(', ')})`);
    console.log(`- Current other index: 0`);
  }, [sessionId, players, currentPlayer, clothesList]);

  useEffect(() => {
    if (timeExpired) {
      const submitCurrentPicks = async () => {
        let finalPicks = { ...picks };
        if (Object.keys(finalPicks).length === 0) {
          otherPlayers.forEach(other => {
            const randomIndex = Math.floor(Math.random() * clothes.length);
            finalPicks[other] = randomIndex;
          });
        } else {
          otherPlayers.forEach(other => {
            if (!(other in finalPicks)) {
              const randomIndex = Math.floor(Math.random() * clothes.length);
              finalPicks[other] = randomIndex;
            }
          });
        }
        await api.pick({
          session_id: sessionId,
          round_num: roundNum,
          player: currentPlayer,
          picks: finalPicks,
        });
        onPicksComplete(finalPicks);
      };
      const timeout = setTimeout(() => {
        submitCurrentPicks();
      }, 3000);
      return () => clearTimeout(timeout);
    }
  }, [timeExpired, sessionId, roundNum, currentPlayer, picks, onPicksComplete, otherPlayers, clothes.length]);

  useEffect(() => {
    if (timeExpired && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [timeExpired, countdown]);

  // Ensure picks are submitted when component unmounts or when all picks are done
  useEffect(() => {
    if (Object.keys(picks).length === otherPlayers.length && otherPlayers.length > 0) {
      console.log(`All picks detected for ${currentPlayer}, auto-submitting:`, picks);
      const submitPicks = async () => {
        await api.pick({
          session_id: sessionId,
          round_num: roundNum,
          player: currentPlayer,
          picks: picks,
        });
        onPicksComplete(picks);
      };
      submitPicks();
    }
  }, [picks, otherPlayers.length, currentPlayer, sessionId, roundNum, onPicksComplete]);

  if (timeExpired) {
    return (
      <div className="text-center p-8 bg-yellow-100 border-2 border-yellow-400 rounded-lg max-w-lg mx-auto mt-8">
        <h2 className="text-xl font-bold text-yellow-800 mb-2">Time's Up!</h2>
        <p className="text-yellow-800 mb-2">
          {currentPlayer} ran out of time! {Object.keys(picks).length === 0 ? "Random selections will be made." : "Current selections will be submitted."}
        </p>
        <p className="text-yellow-800">Moving to next player in {countdown} seconds...</p>
      </div>
    );
  }

  const handlePick = async (clothIdx: number) => {
    const other = otherPlayers[currentOther];
    const newPicks = { ...picks, [other]: clothIdx };
    setPicks(newPicks);
    
    console.log(`Pick made by ${currentPlayer} for ${other}: cloth ${clothIdx}`);
    console.log(`- Current other index: ${currentOther}`);
    console.log(`- Total other players: ${otherPlayers.length}`);
    console.log(`- Condition: ${currentOther} < ${otherPlayers.length - 1} = ${currentOther < otherPlayers.length - 1}`);
    
    // Check if this was the last pick needed
    if (currentOther < otherPlayers.length - 1) {
      // Move to next player to pick for
      const nextOther = currentOther + 1;
      console.log(`Moving to next player: index ${nextOther} (${otherPlayers[nextOther]})`);
      setCurrentOther(nextOther);
    } else {
      // All picks completed, submit and move to next phase
      console.log(`All picks completed for ${currentPlayer}:`, newPicks);
      await api.pick({
        session_id: sessionId,
        round_num: roundNum,
        player: currentPlayer,
        picks: newPicks,
      });
      onPicksComplete(newPicks);
    }
  };

  const handleSkip = async () => {
    let finalPicks = { ...picks };
    otherPlayers.forEach(other => {
      if (!(other in finalPicks)) {
        const randomIndex = Math.floor(Math.random() * clothes.length);
        finalPicks[other] = randomIndex;
      }
    });
    await api.pick({
      session_id: sessionId,
      round_num: roundNum,
      player: currentPlayer,
      picks: finalPicks,
    });
    onPicksComplete(finalPicks);
  };

  if (!clothes.length) return <div>Loading clothes...</div>;
  if (currentOther >= otherPlayers.length) {
    console.log(`All picks completed for ${currentPlayer}, redirecting to next phase`);
    return <div>All picks done! Moving to next phase...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left side - Original player image */}
        <div className="lg:w-1/3">
          <div className="sticky top-4">
            <h2 className="text-xl font-bold text-pink-600 mb-4">Current Player: <span className="text-green-600">{currentPlayer}</span></h2>
            <Timer seconds={timer} onExpire={() => setTimeExpired(true)} playerKey={currentPlayer} />
            
            {/* Original player image */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-3 text-gray-700">Original Player Image</h3>
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
        </div>

        {/* Right side - Clothes selection */}
        <div className="lg:w-2/3">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Pick a cloth for <span className="text-red-500 font-bold">{otherPlayers[currentOther]}</span></h3>
            <div className="text-sm text-gray-600">
              Pick {currentOther + 1} of {otherPlayers.length} • {otherPlayers.length - currentOther - 1} remaining
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div 
              className="bg-pink-500 h-2 rounded-full transition-all duration-300" 
              style={{ width: `${((currentOther + 1) / otherPlayers.length) * 100}%` }}
            ></div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
            {clothes.map((filename, idx) => (
                             <div key={filename} className="cursor-pointer border border-gray-300 p-2 rounded-lg hover:shadow-md transition hover:border-pink-400" onClick={() => handlePick(idx)}>
                 <img src={`${BACKEND_URL}/clothes/${filename}`} alt={filename} className="w-24 h-24 object-contain rounded-md mx-auto bg-gray-50" />
                 <div className="text-xs text-gray-600 text-center mt-1">{idx}</div>
               </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="mt-4">
        <b>Picks so far:</b>
        <ul className="list-disc list-inside text-sm text-gray-700">
          {Object.entries(picks).map(([other, idx]) => (
            <li key={other}>
              {other}: {idx} {clothes[idx]}
            </li>
          ))}
        </ul>
        {Object.keys(picks).length > 0 && Object.keys(picks).length < otherPlayers.length && (
          <p className="text-yellow-800 mt-2">{otherPlayers.length - Object.keys(picks).length} player(s) still need selection</p>
        )}
        {Object.keys(picks).length > 0 && Object.keys(picks).length < otherPlayers.length && (
          <button onClick={handleSkip} className="mt-2 bg-yellow-400 text-yellow-900 px-4 py-2 rounded font-bold">Skip & Random Select Remaining</button>
        )}
      </div>
    </div>
  );
};

export default ClothesGrid; 