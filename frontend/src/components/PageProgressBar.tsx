import { useEffect, useState } from 'react'

export default function PageProgressBar() {
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let frameId = 0

    const updateProgress = () => {
      const documentHeight =
        document.documentElement.scrollHeight - window.innerHeight

      if (documentHeight <= 0) {
        setProgress(0)
        return
      }

      const nextProgress = Math.min(
        Math.max(window.scrollY / documentHeight, 0),
        1
      )

      setProgress(nextProgress)
    }

    const scheduleUpdate = () => {
      cancelAnimationFrame(frameId)
      frameId = window.requestAnimationFrame(updateProgress)
    }

    scheduleUpdate()
    window.addEventListener('scroll', scheduleUpdate, { passive: true })
    window.addEventListener('resize', scheduleUpdate)

    return () => {
      cancelAnimationFrame(frameId)
      window.removeEventListener('scroll', scheduleUpdate)
      window.removeEventListener('resize', scheduleUpdate)
    }
  }, [])

  return (
    <div className="page-progress" aria-hidden="true">
      <div
        className="page-progress-bar"
        style={{ transform: `scaleX(${progress})` }}
      />
    </div>
  )
}
