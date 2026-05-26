import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { transitions, variants } from '../styles/theme';
import { Top5Rankings } from './Top5Rankings';

interface QuestionCardProps {
  question: string;          // ← plain string now, not Question object
  onAnswer: (answer: string) => void;
  remainingCount: number;
  top5Players: any[];        // ← backend shape
  hasAnsweredQuestion: boolean;
  currentMascot: string;
}

const ANSWERS = [
  { label: 'Yes',          value: 'yes',       indicatorClass: 'indicator--yes',      key: '1' },
  { label: 'No',           value: 'no',         indicatorClass: 'indicator--no',       key: '2' },
  { label: 'Maybe',        value: 'maybe',      indicatorClass: 'indicator--probably', key: '3' },
  { label: "I Don't Know", value: 'dont_know',  indicatorClass: 'indicator--maybe',    key: '4' },  // ← was 'unknown', now 'dont_know'
];

const TOTAL_PLAYERS = 462;  // ← was 20, now real count

export const QuestionCard: React.FC<QuestionCardProps> = ({
  question,
  onAnswer,
  remainingCount,
  top5Players,
  hasAnsweredQuestion,
  currentMascot,
}) => {
  const progress = Math.min(
    100,
    Math.max(0, ((TOTAL_PLAYERS - remainingCount) / TOTAL_PLAYERS) * 100),
  );

  return (
    <div className="question-page-layout">

      <div className="question-mascot-col">
        {top5Players.length > 0 && <Top5Rankings players={top5Players} />}
        
        <motion.div
          className="question-mascot animate-float-alt"
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ ...transitions.spring, delay: 0.2 }}
        >
          <img src={`/${currentMascot}`} alt="The Third Eye Mascot" />
        </motion.div>
      </div>

      <div className="question-col">
        <div className="progress-bar">
          <div className="progress-bar__header">
            <span>Neural Scan in Progress</span>
            <span>Analysis: {Math.round(progress)}% Complete</span>
          </div>
          <div className="progress-bar__track">
            <motion.div
              className="progress-bar__fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={transitions.snappy}
            />
          </div>
        </div>

        <div className="match-count">{remainingCount} matches in database</div>

        <AnimatePresence mode="wait">
          <motion.div
            key={question}          // ← was question.id, now just the string
            variants={variants.slideRight}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={transitions.spring}
            className="question-card glass"
          >
            <div className="card-stripe" />

            <h2 className="question-heading">{question}</h2>   {/* ← was question.text */}

            <div className="d-flex flex-col" style={{ gap: '0.75rem' }}>
              {ANSWERS.map((ans) => (
                <motion.button
                  key={ans.value}
                  whileHover={{ scale: 1.015 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => onAnswer(ans.value)}
                  className="answer-btn"
                >
                  <div className="d-flex items-center" style={{ gap: '1rem' }}>
                    <span className="answer-btn__key">{ans.key}</span>
                    <span className="answer-btn__label">{ans.label}</span>
                  </div>
                  <div className={`answer-btn__indicator ${ans.indicatorClass}`} />
                  <div className="answer-btn__underline" />
                </motion.button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};