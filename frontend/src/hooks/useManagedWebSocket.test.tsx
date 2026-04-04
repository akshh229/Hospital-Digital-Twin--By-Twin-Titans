import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useManagedWebSocket } from './useManagedWebSocket'

class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3
  static instances: MockWebSocket[] = []

  readonly url: string
  readyState = MockWebSocket.CONNECTING
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent<string>) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  send = vi.fn()

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  close() {
    this.readyState = MockWebSocket.CLOSED
  }

  emitOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.(new Event('open'))
  }

  emitMessage(data: string) {
    this.onmessage?.({ data } as MessageEvent<string>)
  }

  emitClose(code = 1011) {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.({ code } as CloseEvent)
  }
}

describe('useManagedWebSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.spyOn(Math, 'random').mockReturnValue(0)
    MockWebSocket.instances = []
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('reconnects with backoff and returns to live state after the socket comes back', async () => {
    const onMessage = vi.fn()

    const { result } = renderHook(() =>
      useManagedWebSocket<{ type: 'patients_snapshot' }>({
        path: '/ws/overview',
        onMessage,
      })
    )

    expect(result.current.connectionState).toBe('connecting')
    expect(MockWebSocket.instances).toHaveLength(1)

    act(() => {
      MockWebSocket.instances[0].emitOpen()
    })

    expect(result.current.connectionState).toBe('live')

    act(() => {
      MockWebSocket.instances[0].emitClose(1011)
    })

    expect(result.current.connectionState).toBe('reconnecting')
    expect(result.current.retryAttempt).toBe(1)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(MockWebSocket.instances).toHaveLength(2)

    act(() => {
      MockWebSocket.instances[1].emitOpen()
      MockWebSocket.instances[1].emitMessage(
        JSON.stringify({ type: 'patients_snapshot' })
      )
    })

    expect(result.current.connectionState).toBe('live')
    expect(result.current.retryAttempt).toBe(0)
    expect(onMessage).toHaveBeenCalledWith({ type: 'patients_snapshot' })
  })
})
