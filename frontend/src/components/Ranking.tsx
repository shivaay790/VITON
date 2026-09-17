import { API_BASE_URL } from '../config';
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';

const BACKEND_URL = API_BASE_URL;

interface VitonResult {
  player: string;
  cloth: string;
  resultImage: string;
  timestamp: Date;
  status: 'pending' | 'processing' | 'completed' | 'error';
  pickedBy?: string;
}

interface RankingProps {
  sessionId: string;
  roundNum: number;
  player: string;
  clothesList: string[];
  vitonResults: VitonResult[];
  onRankingComplete: (ranking: number[]) => void;
}

const Ranking: React.FC<RankingProps> = ({ sessionId, roundNum, player, clothesList, vitonResults, onRankingComplete }) => {
  const [ranking, setRanking] = useState<number[]>([]);
  const [error, setError] = useState('');
  const [receivedClothes, setReceivedClothes] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getReceivedClothes(sessionId, roundNum, player).then(data => {
      setReceivedClothes(data.received_clothes);
      setLoading(false);
    }).catch(() => setLoading(false));
    setRanking([]);
  }, [sessionId, roundNum, player, clothesList]);

  const handleRank = async () => {
    if (ranking.length !== receivedClothes.length) {
      setError('Please rank all clothes.');
      return;
    }
    await api.rank({
      session_id: sessionId,
      round_num: roundNum,
      player,
      ranking: ranking.map(pos => receivedClothes[pos]),
    });
    onRankingComplete(ranking.map(pos => receivedClothes[pos]));
  };

  if (loading) return <div>Loading received clothes...</div>;

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white rounded-2xl shadow-md mt-8">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left side - Original player image */}
        <div className="lg:w-1/3">
          <div className="sticky top-4">
            <h2 className="text-xl font-bold text-pink-600 mb-4">Current Player: <span className="text-green-600">{player}</span></h2>
            
            {/* Original player image */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-3 text-gray-700">Original Player Image</h3>
              <div className="relative">
                                 <img 
                   src={`${BACKEND_URL}/people/${player}.jpg`} 
                   alt={`${player} original`} 
                   className="w-full h-64 object-contain rounded-lg shadow-md bg-gray-100"
                   onError={(e) => {
                     console.error(`Failed to load image for ${player}`);
                     e.currentTarget.style.display = 'none';
                   }}
                 />
                <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded text-xs font-bold">
                  {player}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right side - VITON results for ranking */}
        <div className="lg:w-2/3">
          <h3 className="text-lg font-semibold mb-4">Rank the VITON results you received (click in order of preference):</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-6">
            {receivedClothes.map((clothIdx, i) => {
              const cloth = clothesList[clothIdx];
              const vitonResult = vitonResults.find(result => 
                result.player === player && result.cloth === cloth && result.status === 'completed'
              );
              const isSelected = ranking.includes(i);
              const rankPosition = ranking.indexOf(i) + 1;
              
              return (
                <div
                  key={i}
                  className={`cursor-pointer border rounded-lg overflow-hidden transition-all duration-200 ${
                    isSelected ? 'border-green-500 shadow-md bg-green-50' : 'border-gray-300 bg-white'
                  } ${!vitonResult ? 'opacity-50' : ''}`}
                  onClick={() => {
                    if (!vitonResult) return; // Don't allow selection if VITON not ready
                    if (!ranking.includes(i)) {
                      setRanking([...ranking, i]);
                    } else {
                      setRanking(ranking.filter(item => item !== i));
                    }
                  }}
                >
                  {isSelected && (
                    <div className="absolute top-1 right-1 bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center font-bold text-xs z-10">
                      {rankPosition}
                    </div>
                  )}
                  
                                     {vitonResult ? (
                     <img src={vitonResult.resultImage} alt={`VITON result ${i}`} className="w-full h-48 object-contain bg-gray-50" />
                   ) : (
                    <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-500 mx-auto mb-2"></div>
                        <span className="text-gray-500 text-sm">Processing...</span>
                      </div>
                    </div>
                  )}
                  
                  <div className="p-2">
                    <div className="text-xs text-gray-600 text-center">Cloth #{clothIdx}</div>
                    <div className="text-xs text-gray-500 text-center truncate">{cloth}</div>
                    {vitonResult?.pickedBy && (
                      <div className="text-xs text-blue-600 text-center">Picked by: {vitonResult.pickedBy}</div>
                    )}
                    {isSelected && (
                      <div className="text-xs text-green-500 text-center font-bold">Rank #{rankPosition}</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      <div className="mt-4">
        <b>Your ranking:</b> {ranking.length > 0 ? ranking.map(pos => `index ${pos} (Cloth ${receivedClothes[pos]})`).join(' → ') : 'None selected'}
      </div>
      <div className="mt-4 flex gap-2">
        <button onClick={() => setRanking([])} className="bg-gray-300 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-400 transition-colors">Clear All</button>
        <button onClick={handleRank} disabled={ranking.length !== receivedClothes.length} className="bg-green-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-600 transition-colors">Submit Ranking</button>
      </div>
      {error && <div className="text-red-500 text-center mt-2">{error}</div>}
    </div>
  );
};

export default Ranking; 