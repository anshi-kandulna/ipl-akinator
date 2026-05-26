import React from 'react';
import { motion } from 'framer-motion';
import { variants, transitions } from '../styles/theme';

interface BackendPlayer {
  name: string;
  image_url?: string;
  confidence?: number;
  reasoning?: string;
  display_message?: string;
}

interface PlayerCardProps {
  player: BackendPlayer;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({ player }) => {
  return (
    <motion.div
      variants={variants.cardReveal}
      initial="hidden"
      animate="visible"
      transition={transitions.cardFlip}
      className="player-card"
    >
      <div className="player-card__border">
        <div className="player-card__inner">
          <div className="player-card__dot-pattern" />

          {/* Confidence as rating */}
          <div className="player-card__header">
            <div style={{ textAlign: 'center' }}>
              <div className="player-card__rating">
                {player.confidence ? Math.round(player.confidence * 100) : '?'}
              </div>
              <div className="player-card__position">CONF</div>
            </div>
          </div>

          {/* Avatar */}
          <div className="player-card__avatar">
            <img
              src={player.image_url || '/player-placeholder.png'}
              alt={player.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Name */}
          <div className="player-card__name">{player.name}</div>

          <div className="player-card__divider" />

          {/* Reasoning */}
          {player.reasoning && (
            <div style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-secondary)',
              textAlign: 'center',
              padding: '0 0.5rem',
              lineHeight: 1.4,
            }}>
              {player.reasoning}
            </div>
          )}

          <div className="player-card__bottom-bar" />
        </div>
      </div>

      <div className="player-card__glow" />
    </motion.div>
  );
};