// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { Circle, Polyline, Polygon, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { Play, Square, Wind } from "lucide-react";
import * as turf from "@turf/turf";
import type { ModuleResult, WindCycloneZoneFeature } from "@/lib/stores/analysis";
import { useWindCycloneUIStore } from "@/lib/stores/analysis";
import "leaflet-velocity/dist/leaflet-velocity.css";

interface WindCycloneTracksProps {
  center: [number, number];
  result: ModuleResult;
  bufferM?: number;
  layers?: {
    tracks: boolean;
    windZones: boolean;
    eyePoints: boolean;
  };
}

async function ensureLeafletVelocity() {
  if (typeof window !== "undefined") {
    (window as any).L = L;
    if (!(L as any).velocityLayer) {
      await import("leaflet-velocity");
    }
  }
}

export function WindCycloneTracks({
  center,
  result,
  bufferM = 100000,
  layers = { tracks: true, windZones: true, eyePoints: true },
}: WindCycloneTracksProps) {
  const map = useMap();
  const data = result.windCyclone;
  const [staticWindZones, setStaticWindZones] = useState<WindCycloneZoneFeature[]>([]);

  // Connect to global wind cyclone UI store
  const {
    windZoneMode,
    setSelectedStorm,
    setActiveStormSid: setStoreActiveStormSid,
    setLoadingSid: setStoreLoadingSid,
    setFetchError: setStoreFetchError,
  } = useWindCycloneUIStore();

  // Native Leaflet Velocity layer state and ref
  const velocityLayerRef = useRef<any>(null);
  const animationTimerRef = useRef<any>(null);
  const animationFrameRef = useRef<number | null>(null);
  const [activeStormSid, setActiveStormSid] = useState<string | null>(null);
  const [loadingSid, setLoadingSid] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [fetchErrorSid, setFetchErrorSid] = useState<string | null>(null);

  const setIsAnimating = (animating: boolean) => {
    if (!animating) {
      handleStopAnimation();
    }
  };

  const handleAnimateStorm = async (sid: string, name: string) => {
    setLoadingSid(sid);
    setStoreLoadingSid(sid);
    setFetchError(null);
    setStoreFetchError(null);
    setFetchErrorSid(null);

    try {
      // 1. If a velocity layer is already active, remove it cleanly
      if (velocityLayerRef.current) {
        map.removeLayer(velocityLayerRef.current);
        velocityLayerRef.current = null;
      }
      if (animationTimerRef.current) {
        clearTimeout(animationTimerRef.current);
        clearInterval(animationTimerRef.current);
        animationTimerRef.current = null;
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }

      // 2. Fetch pre-cached wind grid from MinIO
      const res = await fetch(`http://localhost:9000/cyclone-wind-grids/${sid}.json`);
      if (!res.ok) {
        throw new Error(
          `Pre-cached grid not found (HTTP ${res.status}). Run: python scripts/fetch_era5_storm_grids.py --storm-id ${sid}`
        );
      }
      const fetchedData = await res.json();
      if (!Array.isArray(fetchedData) || fetchedData.length < 2 || !fetchedData[0]?.header || !fetchedData[0]?.data) {
        throw new Error("Invalid wind-js format returned from MinIO server.");
      }

      // 3. Ensure native leaflet-velocity is initialized on L
      await ensureLeafletVelocity();

      if (!(L as any).velocityLayer) {
        throw new Error("leaflet-velocity plugin could not be initialized.");
      }

      // 4. Instantiate native Leaflet Velocity layer and add to map
      const layer = (L as any).velocityLayer({
        paneName: "overlayPane",
        displayValues: true,
        displayOptions: {
          velocityType: `${name} Wind`,
          position: "bottomleft",
          emptyString: "No wind data",
          angleConvention: "bearingCW",
          showCardinal: true,
          speedUnit: "m/s",
        },
        data: fetchedData,
        maxVelocity: 50,
        velocityScale: 0.005,
        particleMultiplier: 1 / 300,
        lineWidth: 1.5,
        frameRate: 20,
        colorScale: [
          "rgb(96, 165, 250)",
          "rgb(52, 211, 153)",
          "rgb(251, 191, 36)",
          "rgb(249, 115, 22)",
          "rgb(239, 68, 68)",
          "rgb(168, 85, 247)",
        ],
      });

      layer.addTo(map);
      velocityLayerRef.current = layer;
      setActiveStormSid(sid);
      setStoreActiveStormSid(sid);

      // 5. Target the canvas & strip hardware-acceleration animation classes immediately
      const velocityCanvas = document.querySelector(".leaflet-overlay-pane canvas") as HTMLCanvasElement | null;
      if (velocityCanvas) {
        // Prevent Leaflet from hardware-stretching the canvas
        velocityCanvas.classList.remove("leaflet-zoom-animated");
        // Ensure transitions don't delay the hide effect
        velocityCanvas.style.transition = "opacity 0.1s ease-out";
      }

      // 6. Animation loop & auto-reset when reaching the final frame of the storm data array
      const stormDataArray: any[] = Array.isArray(fetchedData[0])
        ? fetchedData
        : Array.isArray(fetchedData) && fetchedData.length > 2
        ? fetchedData
        : [fetchedData];

      let currentFrameIndex = 0;
      const totalFrames = stormDataArray.length;

      const runAnimationLoop = () => {
        // Boundary check: when the animation reaches the final frame of the storm data array, automatically reset state
        if (currentFrameIndex >= totalFrames - 1) {
          setIsAnimating(false);
          return;
        }

        currentFrameIndex++;

        // Update layer data if multi-frame wind dataset
        if (velocityLayerRef.current && stormDataArray[currentFrameIndex]) {
          if (typeof velocityLayerRef.current.setData === "function") {
            velocityLayerRef.current.setData(stormDataArray[currentFrameIndex]);
          }
        }

        animationTimerRef.current = setTimeout(runAnimationLoop, 1000);
      };

      if (totalFrames > 1) {
        animationTimerRef.current = setTimeout(runAnimationLoop, 1000);
      } else {
        // For static single-peak storm grid playback, auto-reset when natural playback concludes (8s duration)
        animationTimerRef.current = setTimeout(() => {
          setIsAnimating(false);
        }, 8000);
      }
    } catch (err: any) {
      const errMsg = err?.message || "Failed to fetch storm wind grid from MinIO";
      setFetchError(errMsg);
      setStoreFetchError(errMsg);
      setFetchErrorSid(sid);
    } finally {
      setLoadingSid(null);
      setStoreLoadingSid(null);
    }
  };

  const handleStopAnimation = () => {
    if (animationTimerRef.current) {
      clearTimeout(animationTimerRef.current);
      clearInterval(animationTimerRef.current);
      animationTimerRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (velocityLayerRef.current) {
      map.removeLayer(velocityLayerRef.current);
      velocityLayerRef.current = null;
    }
    setActiveStormSid(null);
    setStoreActiveStormSid(null);
    setFetchError(null);
    setStoreFetchError(null);
    setFetchErrorSid(null);
  };

  // Listen to custom window events from docked widget
  useEffect(() => {
    const handleCustomAnimate = (e: Event) => {
      const detail = (e as CustomEvent).detail;
      if (detail?.sid) {
        handleAnimateStorm(detail.sid, detail.name || "Storm");
      }
    };
    const handleCustomStop = () => {
      handleStopAnimation();
    };

    window.addEventListener("sat:animate-storm", handleCustomAnimate);
    window.addEventListener("sat:stop-animation", handleCustomStop);

    return () => {
      window.removeEventListener("sat:animate-storm", handleCustomAnimate);
      window.removeEventListener("sat:stop-animation", handleCustomStop);
    };
  }, [map]);


  // Raw DOM listeners for zero-latency hiding on physical hardware interaction
  useEffect(() => {
    if (!activeStormSid) return;

    const mapContainer = map.getContainer();
    const getCanvas = (): HTMLCanvasElement | null => {
      return (
        velocityLayerRef.current?._canvasLayer?._canvas ||
        (document.querySelector(".leaflet-overlay-pane canvas") as HTMLCanvasElement | null)
      );
    };

    const hideWind = () => {
      const velocityCanvas = getCanvas();
      if (velocityCanvas) {
        velocityCanvas.classList.remove("leaflet-zoom-animated");
        velocityCanvas.style.opacity = "0";
      }
    };

    const showWind = () => {
      const velocityCanvas = getCanvas();
      if (velocityCanvas) {
        velocityCanvas.classList.remove("leaflet-zoom-animated");
        velocityCanvas.style.opacity = "1";
      }
    };

    const handleMouseUp = () => {
      // Restore on mouseup after short delay if no drag movement triggered moveend
      setTimeout(showWind, 60);
    };

    // Trigger instantly on physical hardware interaction
    mapContainer.addEventListener("mousedown", hideWind);
    mapContainer.addEventListener("wheel", hideWind, { passive: true });
    mapContainer.addEventListener("touchstart", hideWind, { passive: true });
    window.addEventListener("mouseup", handleMouseUp);
    window.addEventListener("touchend", handleMouseUp);

    // Restore only when the map has completely stopped moving and vectors recalculated
    map.on("moveend", showWind);
    map.on("zoomend", showWind);

    return () => {
      mapContainer.removeEventListener("mousedown", hideWind);
      mapContainer.removeEventListener("wheel", hideWind);
      mapContainer.removeEventListener("touchstart", hideWind);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchend", handleMouseUp);
      map.off("moveend", showWind);
      map.off("zoomend", showWind);
    };
  }, [map, activeStormSid]);

  // Clean up velocity layer on unmount to free browser memory
  useEffect(() => {
    return () => {
      if (velocityLayerRef.current) {
        map.removeLayer(velocityLayerRef.current);
        velocityLayerRef.current = null;
      }
    };
  }, [map]);

  // Always fetch /data/is875_wind_zones.geojson on mount so national zones are available
  useEffect(() => {
    if (staticWindZones.length === 0) {
      fetch("/data/is875_wind_zones.geojson")
        .then((res) => res.json())
        .then((json) => {
          if (json?.features) setStaticWindZones(json.features);
        })
        .catch(() => {});
    }
  }, [staticWindZones.length]);

  const showTracks = layers.tracks ?? true;
  const showWindZones = layers.windZones ?? false;
  const showEyePoints = layers.eyePoints ?? false;

  const getZoneColors = (speed: number) => {
    const strokeColor =
      speed === 55 ? "#7E22CE" :
      speed === 50 ? "#EF4444" :
      speed === 47 ? "#F97316" :
      speed === 44 ? "#FBBF24" :
      speed === 39 ? "#059669" :
      speed === 33 ? "#0284C7" : "#475569";

    const fillColor =
      speed === 55 ? "#7E22CE" :
      speed === 50 ? "#EF4444" :
      speed === 47 ? "#F97316" :
      speed === 44 ? "#FBBF24" :
      speed === 39 ? "#34D399" :
      speed === 33 ? "#60A5FA" : "#CBD5E1";

    return { strokeColor, fillColor };
  };

  // Strict Point-in-Polygon containment: ensure rendered polygon strictly contains site coordinates
  const pointInPolygon = (lat: number, lon: number, ring: [number, number][]) => {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const xi = ring[i][0], yi = ring[i][1];
      const xj = ring[j][0], yj = ring[j][1];
      const intersect = ((yi > lat) !== (yj > lat)) &&
        (lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  };

  // Scoped regional wind zone matching the site
  const scopedWindZoneFeatures = useMemo(() => {
    if ((data?.wind_zones?.features?.length ?? 0) > 0) {
      return data!.wind_zones!.features;
    }
    return staticWindZones.filter((zone) =>
      zone.geometry.coordinates.some((ring) => pointInPolygon(center[0], center[1], ring as [number, number][]))
    );
  }, [data?.wind_zones, staticWindZones, center]);

  // National wind zone features across India
  const nationalWindZoneFeatures = useMemo(() => {
    return staticWindZones.length > 0 ? staticWindZones : scopedWindZoneFeatures;
  }, [staticWindZones, scopedWindZoneFeatures]);

  // Calculate Buffer Focus zone intersections (strictly clipped to circular buffer)
  const bufferFocusedPolygons = useMemo(() => {
    if (!showWindZones || windZoneMode !== "buffer" || !data) return [];

    const bufferKm = bufferM / 1000;
    const bufferCenterPoint = turf.point([center[1], center[0]]);
    const bufferCircle = turf.circle(bufferCenterPoint, bufferKm, { steps: 64, units: "kilometers" });

    const polygons: Array<{
      positions: [number, number][][];
      color: string;
      fillColor: string;
      name: string;
      speed: number;
      zoneId: string;
    }> = [];

    scopedWindZoneFeatures.forEach((zone, idx) => {
      const props = zone.properties;
      const speed = props.zone_speed || props.v_b_ms || 39;
      const { strokeColor, fillColor } = getZoneColors(speed);

      try {
        const zonePoly = turf.polygon(zone.geometry.coordinates as any);
        const intersected = turf.intersect(turf.featureCollection([bufferCircle, zonePoly]));
        if (intersected && intersected.geometry) {
          if (intersected.geometry.type === "Polygon") {
            const positions: [number, number][][] = (intersected.geometry.coordinates as [number, number][][]).map(
              (ring) => ring.map(([lon, lat]) => [lat, lon])
            );
            polygons.push({
              positions,
              color: strokeColor,
              fillColor,
              name: props.name,
              speed,
              zoneId: `${props.zone_id}-${idx}`,
            });
          } else if (intersected.geometry.type === "MultiPolygon") {
            (intersected.geometry.coordinates as [number, number][][][]).forEach((polyRings, pIdx) => {
              const positions = polyRings.map((ring) => ring.map(([lon, lat]) => [lat, lon] as [number, number]));
              polygons.push({
                positions,
                color: strokeColor,
                fillColor,
                name: props.name,
                speed,
                zoneId: `${props.zone_id}-${idx}-${pIdx}`,
              });
            });
          }
        }
      } catch {
        // Graceful handling of geometry intersection edge cases
      }
    });

    // Fallback if direct polygon intersection returns empty: fill buffer with statutory rating
    if (polygons.length === 0) {
      const speed = data.statutory_v_b_ms || 39;
      const { strokeColor, fillColor } = getZoneColors(speed);
      const circlePositions = (bufferCircle.geometry.coordinates[0] as [number, number][]).map(([lon, lat]) => [lat, lon] as [number, number]);
      polygons.push({
        positions: [circlePositions],
        color: strokeColor,
        fillColor,
        name: data.damage_risk_category || "Statutory Site Zone",
        speed,
        zoneId: "statutory-fallback",
      });
    }

    return polygons;
  }, [showWindZones, windZoneMode, bufferM, center, scopedWindZoneFeatures, data]);

  const handleSelectTrack = (props: any) => {
    setSelectedStorm({
      sid: props.sid,
      name: props.name,
      season: Number(props.season) || 2020,
      category: props.category,
      max_wind_ms: Number(props.max_wind_ms) || 0,
      max_wind_kmh: Number(props.max_wind_kmh) || Math.round((Number(props.max_wind_ms) || 0) * 3.6),
      min_pressure_hpa: Number(props.min_pressure_hpa) || 1000,
      closest_distance_km: Number(props.closest_distance_km) || 0,
    });
  };

  // Chunked progressive rendering when tracks count > 50 to prevent freezing browser main thread
  const allTracks = useMemo(() => data?.tracks?.features ?? [], [data?.tracks?.features]);
  const [renderedTrackCount, setRenderedTrackCount] = useState<number>(() =>
    allTracks.length > 50 ? 30 : allTracks.length
  );

  useEffect(() => {
    if (allTracks.length <= 50) {
      setRenderedTrackCount(allTracks.length);
      return;
    }

    setRenderedTrackCount(30);
    let rafId: number;
    const renderNextChunk = () => {
      setRenderedTrackCount((prev) => {
        if (prev >= allTracks.length) return prev;
        const next = Math.min(prev + 25, allTracks.length);
        if (next < allTracks.length) {
          rafId = requestAnimationFrame(renderNextChunk);
        }
        return next;
      });
    };

    rafId = requestAnimationFrame(renderNextChunk);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [allTracks.length]);

  const visibleTracks = useMemo(() => {
    return allTracks.slice(0, renderedTrackCount);
  }, [allTracks, renderedTrackCount]);

  // Derive Storm Eye Points from LineString coordinates (scoped to visible tracks)
  const eyePointFeatures = useMemo(() => {
    if ((data?.eye_points?.features?.length ?? 0) > 0) {
      return data!.eye_points!.features;
    }
    return visibleTracks.flatMap((trackFeature) => {
      if (trackFeature.geometry.type !== "LineString") return [];
      return trackFeature.geometry.coordinates.map((coord, idx) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: coord as [number, number],
        },
        properties: {
          ...trackFeature.properties,
          wind_ms: trackFeature.properties.max_wind_ms,
          point_index: idx,
        },
      }));
    });
  }, [data?.eye_points, visibleTracks]);

  if (!data) return null;

  return (
    <>
      {/* Site Search Buffer Circle */}
      <Circle
        center={center}
        radius={bufferM}
        pathOptions={{
          color: "#0284C7",
          fillColor: "#0284C7",
          fillOpacity: 0.08,
          weight: 1.5,
          dashArray: "5, 5",
        }}
      />

      {/* IS 875 Statutory Wind Zone Polygons Layer (3-Way: Buffer Focus | Regional | All Zones) */}
      {showWindZones && (
        windZoneMode === "buffer" ? (
          // BUFFER FOCUS: fill strictly restricted to circular buffer, clean solid borders (no dotted lines)
          bufferFocusedPolygons.map((zone, idx) => (
            <Polygon
              key={`buffer-zone-${zone.zoneId}-${idx}`}
              positions={zone.positions}
              pathOptions={{
                color: zone.color,
                fillColor: zone.fillColor,
                fillOpacity: 0.28,
                weight: 1.5,
              }}
            >
              <Popup>
                <div className="p-1 font-sans space-y-1 text-xs">
                  <div className="flex items-center gap-1.5 border-b border-neutral-200 pb-1">
                    <span className="font-bold text-neutral-900">{zone.name}</span>
                    <span className="text-[9px] font-semibold text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-200">
                      Buffer Focus
                    </span>
                  </div>
                  <div className="text-sky-700 font-semibold">
                    Basic Design Wind Speed Vb: {zone.speed} m/s
                  </div>
                  <div className="text-[10px] text-neutral-500">
                    Bureau of Indian Standards · IS 875 (Part 3): 2015
                  </div>
                </div>
              </Popup>
            </Polygon>
          ))
        ) : windZoneMode === "regional" ? (
          // REGIONAL: render zone containing the site with clean solid borders (no dotted lines)
          scopedWindZoneFeatures.map((zone, idx) => {
            const props = zone.properties;
            const speed = props.zone_speed || props.v_b_ms || 39;
            const { strokeColor, fillColor } = getZoneColors(speed);
            const rawRings = zone.geometry.coordinates;
            const positions: [number, number][][] = rawRings.map((ring) =>
              ring.map(([lon, lat]) => [lat, lon] as [number, number])
            );

            return (
              <Polygon
                key={`windzone-regional-${props.zone_id}-${idx}`}
                positions={positions}
                pathOptions={{
                  color: strokeColor,
                  fillColor: fillColor,
                  fillOpacity: 0.20,
                  weight: 1.5,
                }}
              >
                <Popup>
                  <div className="p-1 font-sans space-y-1 text-xs">
                    <div className="flex items-center gap-1.5 border-b border-neutral-200 pb-1">
                      <span className="font-bold text-neutral-900">{props.name}</span>
                      <span className="text-[9px] font-semibold text-neutral-600 bg-neutral-100 px-1.5 py-0.5 rounded border border-neutral-200">
                        Regional
                      </span>
                    </div>
                    <div className="text-sky-700 font-semibold">
                      Basic Design Wind Speed Vb: {speed} m/s
                    </div>
                    <div className="text-[10px] text-neutral-500">
                      Bureau of Indian Standards · IS 875 (Part 3): 2015
                    </div>
                  </div>
                </Popup>
              </Polygon>
            );
          })
        ) : (
          // ALL ZONES: render complete national unclipped wind zone dataset across the entire country
          nationalWindZoneFeatures.map((zone, idx) => {
            const props = zone.properties;
            const speed = props.zone_speed || props.v_b_ms || 39;
            const { strokeColor, fillColor } = getZoneColors(speed);
            const rawRings = zone.geometry.coordinates;
            const positions: [number, number][][] = rawRings.map((ring) =>
              ring.map(([lon, lat]) => [lat, lon] as [number, number])
            );

            return (
              <Polygon
                key={`windzone-all-${props.zone_id}-${idx}`}
                positions={positions}
                pathOptions={{
                  color: strokeColor,
                  fillColor: fillColor,
                  fillOpacity: 0.20,
                  weight: 1.5,
                }}
              >
                <Popup>
                  <div className="p-1 font-sans space-y-1 text-xs">
                    <div className="flex items-center gap-1.5 border-b border-neutral-200 pb-1">
                      <span className="font-bold text-neutral-900">{props.name}</span>
                      <span className="text-[9px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200">
                        All Zones (National)
                      </span>
                    </div>
                    <div className="text-sky-700 font-semibold">
                      Basic Design Wind Speed Vb: {speed} m/s
                    </div>
                    <div className="text-[10px] text-neutral-500">
                      Bureau of Indian Standards · IS 875 (Part 3): 2015
                    </div>
                  </div>
                </Popup>
              </Polygon>
            );
          })
        )
      )}

      {/* Historical Cyclone LineString Track Paths (Progressively Chunked) */}
      {showTracks &&
        visibleTracks.map((feature) => {
          const props = feature.properties;
          const rawCoords = feature.geometry.coordinates;

          // GeoJSON standard coordinates are [longitude, latitude].
          // React-Leaflet Polyline expects [latitude, longitude] positions.
          const positions: [number, number][] = rawCoords.map(([lon, lat]) => [lat, lon]);

          const strokeColor = props.stroke || "#0284C7";
          const strokeWidth = props.stroke_width || 3.0;

          return (
            <React.Fragment key={props.sid}>
              {/* Invisible 18px wide hover/click target buffer beneath visible track */}
              <Polyline
                positions={positions}
                pathOptions={{
                  color: strokeColor,
                  weight: 18,
                  opacity: 0.001,
                  lineCap: "round",
                  lineJoin: "round",
                  interactive: true,
                }}
                eventHandlers={{
                  click: () => handleSelectTrack(props),
                }}
              >
                <Popup>
                  <div className="p-1 min-w-[200px] space-y-1.5 font-sans">
                    <div className="flex items-center justify-between border-b border-neutral-200 pb-1">
                      <span className="font-bold text-xs text-neutral-900">{props.name}</span>
                      <span className="text-[10px] font-semibold text-neutral-500 bg-neutral-100 px-1.5 py-0.5 rounded">
                        {props.season}
                      </span>
                    </div>
                    <div className="space-y-1 text-[11px] text-neutral-700">
                      <div className="flex justify-between">
                        <span className="text-neutral-500">IMD Category:</span>
                        <span className="font-semibold text-sky-700">
                          {props.category ? props.category.split(" (")[0] : "Cyclone"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Max Wind Speed:</span>
                        <span className="font-semibold text-rose-600">
                          {props.max_wind_ms} m/s ({props.max_wind_kmh} km/h)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Min Barometric Pressure:</span>
                        <span className="font-medium text-neutral-800">{props.min_pressure_hpa} hPa</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-500">Distance to Site:</span>
                        <span className="font-semibold text-neutral-900">{props.closest_distance_km} km</span>
                      </div>
                    </div>

                    {/* Animate Storm Peak Action Button */}
                    <div className="pt-2 border-t border-neutral-200">
                      {activeStormSid === props.sid ? (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStopAnimation();
                          }}
                          className="w-full py-1.5 px-2 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                        >
                          <Square size={12} className="fill-current" />
                          <span>Stop Wind Animation</span>
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAnimateStorm(props.sid, props.name);
                          }}
                          disabled={loadingSid === props.sid}
                          className="w-full py-1.5 px-2 bg-sky-600 hover:bg-sky-700 disabled:bg-neutral-300 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                        >
                          {loadingSid === props.sid ? (
                            <>
                              <span className="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full" />
                              <span>Loading Grid...</span>
                            </>
                          ) : (
                            <>
                              <Play size={12} className="fill-current" />
                              <span>▶ Animate Storm Peak</span>
                            </>
                          )}
                        </button>
                      )}
                      {fetchError && fetchErrorSid === props.sid && (
                        <div className="mt-1.5 text-[10px] text-rose-700 bg-rose-50 p-1.5 rounded border border-rose-200 leading-tight">
                          {fetchError}
                        </div>
                      )}
                    </div>
                  </div>
                </Popup>
              </Polyline>

              {/* Visible thin crisp track path on top */}
              <Polyline
                positions={positions}
                pathOptions={{
                  color: strokeColor,
                  weight: strokeWidth,
                  opacity: 0.85,
                  lineCap: "round",
                  lineJoin: "round",
                  interactive: true,
                }}
                eventHandlers={{
                  click: () => handleSelectTrack(props),
                }}
              />
            </React.Fragment>
          );
        })}

      {/* Intermediate Storm Eye Points (CircleMarker Layer) */}
      {showEyePoints &&
        eyePointFeatures.map((pt, idx) => {
          const [lon, lat] = pt.geometry.coordinates;
          const props = pt.properties;

          return (
            <CircleMarker
              key={`eyept-${props.sid}-${idx}`}
              center={[lat, lon]}
              radius={5.5}
              pathOptions={{
                color: "#ffffff",
                weight: 1.5,
                fillColor: ("stroke" in props && props.stroke) ? props.stroke : "#0284C7",
                fillOpacity: 0.95,
              }}
              eventHandlers={{
                click: () => handleSelectTrack(props),
              }}
            >
              <Popup>
                <div className="p-1 font-sans space-y-1 text-xs min-w-[190px]">
                  <div className="font-bold text-neutral-900">{props.name} ({props.season})</div>
                  <div className="text-[10px] text-neutral-500">Eye Observation Point #{props.point_index + 1}</div>
                  {props.category && (
                    <div className="text-sky-700 font-semibold">{props.category.split(" (")[0]}</div>
                  )}
                  {props.wind_ms && (
                    <div className="text-rose-600 font-medium">
                      Wind: {props.wind_ms} m/s ({Math.round(props.wind_ms * 3.6)} km/h)
                    </div>
                  )}

                  {/* Animate Storm Peak Action Button on Eye Point */}
                  <div className="pt-2 border-t border-neutral-200 mt-1">
                    {activeStormSid === props.sid ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStopAnimation();
                        }}
                        className="w-full py-1 px-2 bg-rose-600 hover:bg-rose-700 text-white rounded text-[11px] font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                      >
                        <Square size={11} className="fill-current" />
                        <span>Stop Wind Animation</span>
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAnimateStorm(props.sid, props.name);
                        }}
                        disabled={loadingSid === props.sid}
                        className="w-full py-1 px-2 bg-sky-600 hover:bg-sky-700 disabled:bg-neutral-300 text-white rounded text-[11px] font-semibold flex items-center justify-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                      >
                        {loadingSid === props.sid ? (
                          <>
                            <span className="animate-spin inline-block w-2.5 h-2.5 border-2 border-white border-t-transparent rounded-full" />
                            <span>Loading Grid...</span>
                          </>
                        ) : (
                          <>
                            <Play size={11} className="fill-current" />
                            <span>▶ Animate Storm Peak</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}


      {/* Floating Stop Animation control when velocity layer is active */}
      {activeStormSid && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 1000,
            pointerEvents: "auto",
          }}
        >
          <button
            type="button"
            onClick={handleStopAnimation}
            className="flex items-center gap-2 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-full text-xs font-semibold shadow-lg transition-all cursor-pointer"
          >
            <Square size={13} className="fill-current" />
            <span>Stop Wind Animation</span>
          </button>
        </div>
      )}
    </>
  );
}

export default WindCycloneTracks;
