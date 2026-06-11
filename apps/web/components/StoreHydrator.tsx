'use client'

import { useEffect } from 'react'
import { useMapStore } from '@/store'

export function StoreHydrator() {
  useEffect(() => {
    useMapStore.persist.rehydrate()
  }, [])
  return null
}
