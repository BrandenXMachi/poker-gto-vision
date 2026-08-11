export const metadata = {
  title: 'GTO Preflop Trainer',
  description: '6-Max 100bb GTO preflop hand chart trainer',
}

export default function GtoTrainerPage() {
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
