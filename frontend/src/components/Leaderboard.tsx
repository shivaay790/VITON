import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';

interface LeaderboardProps {
  sessionId: string | null;
}

const Leaderboard: React.FC<LeaderboardProps> = ({ sessionId }) => {
  const [leaderboardData, setLeaderboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    api.getDetailedLeaderboard(sessionId)
      .then(data => {
        setLeaderboardData(data);
        setLoading(false);
      })
      .catch(err => {
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) return <div>Loading leaderboard...</div>;
  if (!leaderboardData) return <div>Failed to load leaderboard</div>;

  const { leaderboard, round_scores, players, num_rounds } = leaderboardData;
  const sortedPlayers = Object.entries(leaderboard)
    .sort(([,a], [,b]) => b - a)
    .map(([player]) => player);

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold text-center mb-6 text-blue-700">🏆 Leaderboard</h2>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse bg-white rounded-lg shadow-md">
          <thead>
            <tr className="bg-blue-50">
              <th className="py-2 px-4 text-left font-bold text-blue-900">Rank</th>
              <th className="py-2 px-4 text-left font-bold text-blue-900">Player</th>
              {Array.from({ length: num_rounds }, (_, i) => i + 1).map(round => (
                <th key={round} className="py-2 px-4 text-center font-bold text-blue-900">Round {round}</th>
              ))}
              <th className="py-2 px-4 text-center font-bold text-blue-900 bg-blue-100">Total</th>
            </tr>
          </thead>
          <tbody>
            {sortedPlayers.map((player, index) => (
              <tr key={player} className={index === 0 ? 'bg-yellow-100' : index === 1 ? 'bg-gray-100' : index === 2 ? 'bg-orange-100' : ''}>
                <td className="py-2 px-4 text-center font-bold">{index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}</td>
                <td className="py-2 px-4 font-bold">{player}</td>
                {Array.from({ length: num_rounds }, (_, i) => i + 1).map(round => (
                  <td key={round} className="py-2 px-4 text-center">{round_scores[round]?.[player] || 0}</td>
                ))}
                <td className="py-2 px-4 text-center font-bold bg-blue-100 text-blue-700">{leaderboard[player]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 text-center text-gray-600 text-sm">
        <p>🏆 Gold: 1st Place | 🥈 Silver: 2nd Place | 🥉 Bronze: 3rd Place</p>
      </div>
    </div>
  );
};

export default Leaderboard;
