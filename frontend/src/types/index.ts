export interface Player {
  id: string;
  name: string;
  nationality: string;
  team: string;
  position: 'BAT' | 'BWL' | 'AR' | 'WK';
  isActive: boolean;
  isOverseas: boolean;
  hasCaptained: boolean;
  hasWonIPL: boolean;
  hasOrangeCap: boolean;
  hasPurpleCap: boolean;
  playedForLegacyTeam: boolean;
  isFinisher: boolean;
  bowlsDeathOvers: boolean;
  rating: number;
  stats: {
    batting: number;
    bowling: number;
    fielding: number;
    power: number;
    consistency: number;
  };
  imageUrl?: string;
  confidenceScore?: number;
}

export type Answer = 'yes' | 'no' | 'maybe' | 'unknown';

export interface Question {
  id: string;
  text: string;
  attribute: keyof Player;
  value: string | number | boolean;
}