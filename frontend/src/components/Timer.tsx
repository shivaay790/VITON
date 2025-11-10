import React, { useEffect, useState, useRef } from 'react';

interface TimerProps {
  seconds: number;
  onExpire?: () => void;
  playerKey: string;
}

const Timer: React.FC<TimerProps> = ({ seconds, onExpire, playerKey }) => {
  const [timeLeft, setTimeLeft] = useState(seconds || 60);
  const prevPlayerKey = useRef(playerKey);

  useEffect(() => {
    if (playerKey !== prevPlayerKey.current) {
      setTimeLeft(seconds || 60);
      prevPlayerKey.current = playerKey;
    }
    if (seconds === null || seconds === undefined) return;
    const interval = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          clearInterval(interval);
          onExpire && onExpire();
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [seconds, onExpire, playerKey]);

  if (seconds === null || seconds === undefined) return null;

  return (
    <div style={{ fontWeight: 'bold', fontSize: '1.2em', margin: '1em 0', color: 'red' }}>
      Time left: {timeLeft} seconds
    </div>
  );
};

export default Timer; 