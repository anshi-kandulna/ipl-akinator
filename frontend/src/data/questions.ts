import type { Question } from '../types';

export const questions: Question[] = [
  { id: '1',  text: 'Is your player currently active in the IPL?',          attribute: 'isActive',           value: true  },
  { id: '2',  text: 'Is your player an overseas (non-Indian) player?',       attribute: 'isOverseas',         value: true  },
  { id: '3',  text: 'Has your player ever captained an IPL franchise?',      attribute: 'hasCaptained',       value: true  },
  { id: '4',  text: 'Has your player won an IPL title?',                     attribute: 'hasWonIPL',          value: true  },
  { id: '5',  text: 'Has your player won the Orange Cap (most runs)?',       attribute: 'hasOrangeCap',       value: true  },
  { id: '6',  text: 'Has your player won the Purple Cap (most wickets)?',    attribute: 'hasPurpleCap',       value: true  },
  { id: '7',  text: 'Has your player played for CSK, MI, or RCB?',          attribute: 'playedForLegacyTeam',value: true  },
  { id: '8',  text: 'Is your player known as a finisher / death-overs bat?', attribute: 'isFinisher',         value: true  },
  { id: '9',  text: 'Does your player regularly bowl in the death overs?',   attribute: 'bowlsDeathOvers',    value: true  },
  { id: '10', text: 'Is your player a batsman / top-order batter?',          attribute: 'position',           value: 'BAT' },
  { id: '11', text: 'Is your player a bowler (pace or spin)?',               attribute: 'position',           value: 'BWL' },
  { id: '12', text: 'Is your player an all-rounder?',                        attribute: 'position',           value: 'AR'  },
];