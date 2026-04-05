import type { CSSProperties, ElementType, ReactNode } from 'react'
import { useEffect, useRef, useState } from 'react'

interface RevealProps {
  as?: ElementType
  children: ReactNode
  className?: string
  delay?: number
  threshold?: number
  style?: CSSProperties
}

export default function Reveal({
  as: Tag = 'div',
  children,
  className = '',
  delay = 0,
  threshold = 0.18,
  style,
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) {
      return
    }

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true)
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (entry?.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      {
        threshold,
        rootMargin: '0px 0px -8% 0px',
      }
    )

    observer.observe(node)

    return () => observer.disconnect()
  }, [threshold])

  return (
    <Tag
      ref={ref}
      className={`scroll-reveal ${visible ? 'is-visible' : ''} ${className}`.trim()}
      style={{
        ...style,
        ['--reveal-delay' as string]: `${delay}ms`,
      }}
    >
      {children}
    </Tag>
  )
}
