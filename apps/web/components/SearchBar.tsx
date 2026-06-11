'use client'

import { useState, useRef } from 'react'
import { useMapStore } from '@/store'

interface NominatimResult {
  lat: string
  lon: string
  display_name: string
}

export function SearchBar() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<NominatimResult[]>([])
  const [loading, setLoading] = useState(false)
  const { setViewState, viewState, addFavoriteLocation } = useMapStore()
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const search = async (q: string) => {
    if (q.length < 3) { setResults([]); return }
    setLoading(true)
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5`,
        { headers: { 'Accept-Language': 'en' } }
      )
      setResults(await res.json())
    } catch {}
    setLoading(false)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => search(e.target.value), 400)
  }

  const selectResult = (r: NominatimResult) => {
    setViewState({ ...viewState, latitude: parseFloat(r.lat), longitude: parseFloat(r.lon), zoom: 15 })
    setQuery(r.display_name.split(',')[0])
    setResults([])
  }

  return (
    <div className="relative">
      <div className="flex items-center gap-2 bg-zinc-800 rounded-lg px-3 py-2 border border-zinc-700">
        <svg className="w-4 h-4 text-zinc-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          value={query}
          onChange={handleChange}
          placeholder="Search location…"
          className="bg-transparent text-sm text-white placeholder-zinc-500 outline-none w-48"
        />
        {loading && <div className="w-3 h-3 border border-zinc-400 border-t-transparent rounded-full animate-spin shrink-0" />}
      </div>

      {results.length > 0 && (
        <div className="absolute top-full mt-1 left-0 right-0 bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden z-50 shadow-xl">
          {results.map((r, i) => (
            <button
              key={i}
              onClick={() => selectResult(r)}
              className="w-full text-left px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-700 truncate"
            >
              {r.display_name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
