export const metadata = {
  title: 'GTO Preflop Trainer',
  description: '6-max 100bb GTO preflop hand chart trainer',
}

/**
 * The trainer itself is a self-contained static app in public/gto-trainer/.
 * It is framed full-viewport here so it is served at the site root.
 */
export default function Home() {
  return (
    <iframe
      src="/gto-trainer/index.html"
      title="GTO Preflop Trainer"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        border: 'none',
        margin: 0,
        padding: 0,
      }}
    />
  )
}
