'use client'

import { useState } from 'react'
import { useMapStore } from '@/store'
import { encodeUrlState, viewStateToUrlState } from '@/utils/urlState'
import { LAYER_MANIFEST } from '@/data/layerManifest'

interface ExportDialogProps {
  onClose: () => void
  mapRef?: React.RefObject<HTMLCanvasElement>
}

export function ExportDialog({ onClose, mapRef }: ExportDialogProps) {
  const { viewState, mapStyle, layerVisibility, layerData, selectionPolygon } = useMapStore()
  const [exporting, setExporting] = useState(false)

  const exportCSV = () => {
    const rows: string[][] = [['layer', 'osm_id', 'geometry_type', 'name', 'lat', 'lon']]
    layerData.forEach((fc, layerId) => {
      fc.features.forEach(f => {
        const props = f.properties ?? {}
        let lat = '', lon = ''
        if (f.geometry.type === 'Point') {
          lon = f.geometry.coordinates[0].toString()
          lat = f.geometry.coordinates[1].toString()
        }
        rows.push([layerId, props._osm_id ?? '', f.geometry.type, props.name ?? '', lat, lon])
      })
    })
    const csv = rows.map(r => r.join(',')).join('\n')
    download('sat-analysis.csv', csv, 'text/csv')
  }

  const exportJSON = () => {
    const out: Record<string, GeoJSON.FeatureCollection> = {}
    layerData.forEach((fc, id) => { out[id] = fc })
    download('sat-analysis.json', JSON.stringify(out, null, 2), 'application/json')
  }

  const exportURL = () => {
    const visibleLayers = LAYER_MANIFEST.filter(l => layerVisibility[l.id] !== false).map(l => l.id)
    const urlState = viewStateToUrlState(viewState, mapStyle, visibleLayers)
    const hash = encodeUrlState(urlState)
    const url = `${window.location.origin}${window.location.pathname}${hash}`
    navigator.clipboard.writeText(url)
    alert('URL copied to clipboard!')
  }

  const exportPDF = async () => {
    setExporting(true)
    try {
      const { jsPDF } = await import('jspdf')
      const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
      doc.setFontSize(18)
      doc.text('SAT Site Analysis Report', 15, 20)
      doc.setFontSize(11)
      doc.text(`Location: ${viewState.latitude.toFixed(4)}, ${viewState.longitude.toFixed(4)}`, 15, 30)
      doc.text(`Date: ${new Date().toLocaleDateString()}`, 15, 37)

      if (selectionPolygon) {
        doc.text(`Analysis Area: ${selectionPolygon.area.toFixed(2)} km²`, 15, 44)
      }

      let y = 55
      doc.setFontSize(13)
      doc.text('Layer Summary', 15, y)
      y += 7
      doc.setFontSize(9)
      layerData.forEach((fc, id) => {
        const layer = LAYER_MANIFEST.find(l => l.id === id)
        if (layer && fc.features.length > 0) {
          doc.text(`${layer.name}: ${fc.features.length} features`, 15, y)
          y += 5
          if (y > 180) { doc.addPage(); y = 20 }
        }
      })

      doc.save('sat-analysis.pdf')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-5 w-72 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold">Export</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-white">✕</button>
        </div>

        <div className="space-y-2">
          <ExportButton onClick={exportPDF} disabled={exporting} icon="📄" label="PDF Report" desc="Full analysis summary" />
          <ExportButton onClick={exportCSV} icon="📊" label="CSV Data" desc="Feature table with coordinates" />
          <ExportButton onClick={exportJSON} icon="{ }" label="GeoJSON" desc="All layers as GeoJSON" />
          <ExportButton onClick={exportURL} icon="🔗" label="Share URL" desc="Copies link to clipboard" />
        </div>
      </div>
    </div>
  )
}

function ExportButton({ onClick, disabled, icon, label, desc }: {
  onClick: () => void; disabled?: boolean; icon: string; label: string; desc: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full flex items-center gap-3 px-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 rounded-lg text-left transition-colors"
    >
      <span className="text-lg">{icon}</span>
      <div>
        <div className="text-sm text-white font-medium">{label}</div>
        <div className="text-xs text-zinc-500">{desc}</div>
      </div>
    </button>
  )
}

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}
