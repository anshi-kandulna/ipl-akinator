import { useAkinator } from './hooks/useAkinator';
import { QuestionCard } from './components/QuestionCard';
import { PlayerCard } from './components/PlayerCard';
import { AsciiSurf } from './components/AsciiSurf';
import iplLogo from './assets/ipl-logo.png';
import { motion, AnimatePresence } from 'framer-motion';
import { RotateCcw, Play, Zap } from 'lucide-react';
import { variants, transitions } from './styles/theme';


function App() {
  const {
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
  } = useAkinator();

  return (
    <div 
      className={`page-wrapper ${gameState === 'start' ? '' : 'bg-grid'}`}
      style={{
        ...(gameState === 'start' ? {
          backgroundImage: 'url(/background.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        } : {})
      }}
    >
      {gameState !== 'start' && (
        <>
          {/* ── ASCII surf background animation ── */}
          <AsciiSurf opacity={0.4} />

          {/* ── Ambient background orbs ── */}
          <div
            className="bg-orb bg-orb--accent"
            style={{ top: '-15%', left: '-10%', width: '55%', height: '55%' }}
          />
          <div
            className="bg-orb bg-orb--gold"
            style={{ bottom: '-15%', right: '-10%', width: '50%', height: '50%' }}
          />
        </>
      )}

      {/* ── Header ── */}
      <header className="site-header">
        <div className="site-logo">
          <div className="site-logo__icon" style={{ background: 'transparent', padding: 0 }}>
            <img src={iplLogo} alt="IPL Logo" style={{ width: '28px', height: '28px', objectFit: 'contain' }} />
          </div>
          <span className="site-logo__text">THE THIRD EYE</span>
        </div>

        {gameState !== 'start' && (
          <button onClick={restart} className="btn-restart" aria-label="Restart">
            <RotateCcw size={18} />
          </button>
        )}
      </header>

      {/* ── Main content ── */}
      <main className="main-content d-flex flex-col items-center">
        <AnimatePresence mode="wait">

          {/* ━━ LANDING SCREEN ━━ */}
          {gameState === 'start' && (
            <motion.div
              key="start"
              variants={variants.fadeInUp}
              initial="hidden"
              animate="visible"
              exit={{ opacity: 0, scale: 0.96 }}
              transition={transitions.spring}
              className="w-full d-flex flex-col items-center"
              style={{ gap: 'var(--space-16)' }}
            >
              {/* Hero text block */}
              <div className="w-full">
                <div className="d-flex flex-col items-start text-left">
                  <motion.div
                    variants={variants.fadeIn}
                    initial="hidden"
                    animate="visible"
                    transition={{ ...transitions.snappy, delay: 0.1 }}
                  >
                    <span className="section-badge section-badge--accent" style={{ marginBottom: 'var(--space-6)', display: 'inline-block' }}>
                      Global Player Database Access
                    </span>
                  </motion.div>

                  <h1 className="hero-heading" style={{ marginBottom: 'var(--space-6)', textAlign: 'left' }}>
                    WHO IS YOUR{' '}
                    <br />
                    <span className="glow-text">LEGENDARY</span>{' '}
                    PLAYER?
                  </h1>

                  <p
                    className="text-secondary text-left"
                    style={{
                      maxWidth: 'var(--max-w-md)',
                      fontSize: 'var(--text-lg)',
                      lineHeight: 'var(--lh-relaxed)',
                      marginBottom: 'var(--space-10)',
                    }}
                  >
                    From the 2008 originals to the modern-day masters. If they've stepped on the IPL turf, our AI scanner already knows the name.
                  </p>

                  {/* CTA row */}
                  <div
                    className="d-flex flex-col items-start"
                    style={{ gap: 'var(--space-6)', marginBottom: 'var(--space-12)', width: '100%' }}
                  >
                    <button
                      onClick={startGame}
                      className="btn btn--primary"
                      style={{ padding: 'var(--space-5) var(--space-12)', fontSize: 'var(--text-xl)' }}
                    >
                      <Play size={22} fill="#000" />
                      Start Session
                    </button>

                    <div className="d-flex items-center" style={{ gap: 'var(--space-3)' }}>
                      <Zap size={14} color="var(--color-accent)" />
                      <span className="stat-item__label" style={{ margin: 0 }}>
                        1,000+ Players Scanned Today
                      </span>
                    </div>
                  </div>

                </div>
              </div>


            </motion.div>
          )}

          {/* ━━ QUESTION SCREEN ━━ */}
          {gameState === 'playing' && currentQuestion && (
            <QuestionCard
              key="question"
              question={currentQuestion}
              onAnswer={handleAnswer}
              remainingCount={remainingCount}
              top5Players={top5Players}
              hasAnsweredQuestion={hasAnsweredQuestion}
              currentMascot={currentMascot}
            />
          )}

          {/* ━━ RESULT SCREEN ━━ */}
          {gameState === 'guessing' && (
            <motion.div
              key="guess"
              variants={variants.scaleIn}
              initial="hidden"
              animate="visible"
              transition={transitions.spring}
              className="relative text-center d-flex flex-col items-center"
              style={{ width: '100%' }}
            >
              {/* Decorative watermark text */}
              <div
                className="result-bg-text"
                style={{ top: '-2rem', left: '-2rem' }}
              >
                {guess?.position}
              </div>
              <div
                className="result-bg-text"
                style={{ bottom: '-2rem', right: '-2rem' }}
              >
                {guess?.rating}
              </div>

              {/* Match banner */}
              <span
                className="section-badge section-badge--gold animate-glow-gold"
                style={{ marginBottom: 'var(--space-6)' }}
              >
                Match Found
              </span>


              {/* Result heading */}
              <h2 className="result-heading">
                {guess ? (
                  <>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.4em', letterSpacing: '0.15em', fontWeight: '500', color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-2)' }}>SYSTEM IDENTIFIED:</span>
                    <span className="glow-text">{guess.name}</span>
                  </>
                ) : (
                  'DATABASE ERROR: NO MATCH'
                )}
              </h2>

              {/* Card or fallback */}
              {guess ? (
                <PlayerCard player={guess} />
              ) : (
                <div className="no-match-card glass">
                  <p className="no-match-card__text">
                    I couldn't figure it out. You win this time!
                  </p>
                </div>
              )}

              {/* Feedback buttons */}
              <div
                className="d-flex"
                style={{ gap: 'var(--space-4)', marginTop: 'var(--space-12)' }}
              >
                {guess ? (
                  <>
                    <button
                      onClick={() => handleFeedback(false)}
                      className="btn btn--secondary"
                    >
                      No, that wasn't my player
                    </button>
                    <button
                      onClick={() => handleFeedback(true)}
                      className="btn btn--primary"
                    >
                      Yes
                    </button>
                  </>
                ) : (
                  <button
                    onClick={restart}
                    className="btn btn--primary"
                  >
                    Play Again
                  </button>
                )}
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* ── Footer ── */}
      <footer className="site-footer">
        Powered by AI
      </footer>
    </div>
  );
}

export default App;
