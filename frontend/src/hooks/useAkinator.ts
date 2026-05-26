import { useState } from 'react';

const API = 'http://localhost:8000';

interface Guess {
  name: string;
  image_url?: string;
  confidence: number;
  reasoning: string;
  display_message: string;
}

export const useAkinator = () => {
  const [gameState, setGameState] = useState<'start' | 'playing' | 'guessing'>('start');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
  const [remainingCount, setRemainingCount] = useState<number>(0);
  const [guess, setGuess] = useState<Guess | null>(null);
  const [top5Players, setTop5Players] = useState<any[]>([]);
  const [hasAnsweredQuestion, setHasAnsweredQuestion] = useState(false);
  const [questionCount, setQuestionCount] = useState(0);
  const [lastTwoAnswers, setLastTwoAnswers] = useState<string[]>([]);
  const [currentMascot, setCurrentMascot] = useState('akinator-mascot-bg-removed.png');

  const startGame = async () => {
    const res  = await fetch(`${API}/game/new`, { method: 'POST' });
    const data = await res.json();

    setSessionId(data.session_id);
    setCurrentQuestion(data.question);
    setRemainingCount(data.remaining_count);
    setTop5Players(data.top_candidates || []);
    setGuess(null);
    setHasAnsweredQuestion(false);
    setQuestionCount(0);
    setLastTwoAnswers([]);
    setCurrentMascot('akinator-mascot-bg-removed.png');
    setGameState('playing');
  };

  const handleAnswer = async (answer: string) => {
    if (!sessionId) return;

    const res  = await fetch(`${API}/game/answer`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session_id: sessionId, answer }),
    });
    const data = await res.json();

    // Update tracking
    const newQuestionCount = questionCount + 1;
    setQuestionCount(newQuestionCount);
    
    const newLastTwoAnswers = [...lastTwoAnswers.slice(-1), answer];
    setLastTwoAnswers(newLastTwoAnswers);

    setTop5Players(data.top_candidates || []);
    setHasAnsweredQuestion(true);

    // Determine mascot based on rules
    const topConfidence = (data.top_candidates?.[0]?.probability || 0) * 100;
    const answersUnchanged = newLastTwoAnswers.length === 2 && newLastTwoAnswers[0] === newLastTwoAnswers[1];

    if (newQuestionCount <= 5) {
      // Initial 5 questions: default mascot
      setCurrentMascot('akinator-mascot-bg-removed.png');
    } else if (data.state === 'guessing' || data.state === 'done') {
      // Final prediction
      if (!data.guess || data.guess === 'No match found') {
        setCurrentMascot('akinator-suprised.png');
      } else if (topConfidence > 60) {
        setCurrentMascot('akinator-sure.png');
      }
    } else {
      // After initial questions
      if (answersUnchanged) {
        // Last two answers are the same
        setCurrentMascot('akinator-puzzled.png');
      } else if (topConfidence < 60) {
        // Low confidence
        if (currentMascot === 'akinator-puzzled.png' || currentMascot === 'akinator-unsure.png') {
          // If coming from puzzled/unsure and confidence increased
          setCurrentMascot('akinator-confident.png');
        } else {
          setCurrentMascot('akinator-unsure.png');
        }
      } else if (topConfidence > 60) {
        // High confidence
        setCurrentMascot('akinator-sure.png');
      }
    }

    if (data.state === 'playing') {
      setCurrentQuestion(data.question);
      setRemainingCount(data.remaining_count);
    } else if (data.state === 'guessing' || data.state === 'done') {
      const matchedCandidate = data.top_candidates?.find(
        (c: any) => c.player_name === data.guess
      ) || data.top_candidates?.[0];

      setGuess({
        name:            data.guess,
        image_url:       matchedCandidate?.image_url,
        confidence:      data.confidence,
        reasoning:       data.reasoning,
        display_message: data.display_message,
      });
      setGameState('guessing');
    }
  };

  const handleFeedback = async (wasCorrect: boolean) => {
    if (sessionId) {
      const res = await fetch(`${API}/game/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, was_correct: wasCorrect }),
      });
      const data = await res.json();
      
      if (!wasCorrect && data.state === 'playing') {
        // Backend eliminated the wrong guess — continue game with new question
        setCurrentQuestion(data.question);
        setRemainingCount(data.remaining_count);
        setTop5Players(data.top_candidates || []);
        setGameState('playing');
        setHasAnsweredQuestion(false);
        setCurrentMascot('akinator-mascot-bg-removed.png');
        return;
      }

      // Feedback returned another guess (1-2 players left)
      if (!wasCorrect && data.state === 'guessing') {
        const matchedCandidate = data.top_candidates?.find(
          (c: any) => c.player_name === data.guess
        ) || data.top_candidates?.[0];
        setGuess({
          name:            data.guess,
          image_url:       matchedCandidate?.image_url,
          confidence:      data.top_candidates?.[0]?.probability,
          reasoning:       data.reasoning,
          display_message: data.display_message,
        });
        setCurrentMascot('akinator-sure.png');
        setGameState('guessing');
        return;
      }

      // state === 'done' from feedback = ran out of players
      if (!wasCorrect && data.state === 'done') {
        setGuess(null);              // null guess triggers "couldn't figure it out" UI
        setCurrentMascot('akinator-suprised.png');
        setGameState('guessing');    // reuse guessing screen, null guess = sorry message
        return;
      }
    }
    // wasCorrect or other cases — go back to start
    restart();
  };

  const restart = async () => {
    if (sessionId) {
      await fetch(`${API}/game/${sessionId}`, { method: 'DELETE' });
    }
    setSessionId(null);
    setCurrentQuestion(null);
    setRemainingCount(0);
    setGuess(null);
    setTop5Players([]);
    setHasAnsweredQuestion(false);
    setQuestionCount(0);
    setLastTwoAnswers([]);
    setCurrentMascot('akinator-mascot-bg-removed.png');
    setGameState('start');
  };

  return {
    gameState,
    currentQuestion,
    handleAnswer,
    handleFeedback,
    guess,
    startGame,
    restart,
    remainingCount,
    top5Players,
    hasAnsweredQuestion,
    currentMascot,
  };
};