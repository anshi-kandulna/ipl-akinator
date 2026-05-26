import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface BackendPlayer {
  player_name: string;
  probability: number;
  image_url?: string;
}

interface Top5RankingsProps {
  players: BackendPlayer[];
}

export const Top5Rankings: React.FC<Top5RankingsProps> = ({ players }) => {
  return (
    <div className="top5-rankings">
      <AnimatePresence mode="popLayout">
        {players.map((player, index) => (
          <motion.div
            key={player.player_name}
            initial={{ opacity: 0, x: -20, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.95 }}
            transition={{ delay: index * 0.05, duration: 0.3, ease: "easeOut" }}
            layout
            className="top5-rankings__item glass"
          >
            <div className="top5-rankings__rank">{index + 1}</div>
            <div className="top5-rankings__info">
              <div className="top5-rankings__name">{player.player_name}</div>
            </div>
            <div className="top5-rankings__score">
              <div className="top5-rankings__score-value">
                {Math.round(player.probability * 100)}%
              </div>
              <div className="top5-rankings__score-bar">
                <motion.div
                  className="top5-rankings__score-fill"
                  initial={{ width: 0 }}
                  animate={{ width: `${player.probability * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};