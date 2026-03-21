"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ErrorState } from "@/components/ui/ErrorState";
import { getNearbyBins } from "@/lib/api";
import { getCurrentPosition } from "@/lib/geolocation";
import { BinFeature, BinFeatureCollection, NearbyBin } from "@/lib/types";

const DynamicBinMap = dynamic(
  () => import("@/components/map/BinMap").then((mod) => mod.BinMap),
  { ssr: false }
);

function extractDescriptionField(description: string, fieldName: string): string | undefined {
  const escapedField = fieldName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`<th>${escapedField}<\\/th>\\s*<td>(.*?)<\\/td>`, "i");
  const match = description.match(pattern);
  if (!match?.[1]) {
    return undefined;
  }
  const stripped = match[1].replace(/<[^>]+>/g, "").trim();
  return stripped || undefined;
}

function normalizeFeature(feature: unknown, index: number): BinFeature | null {
  const raw = feature as {
    type?: string;
    geometry?: { type?: string; coordinates?: unknown[] };
    properties?: Record<string, unknown>;
  };

  if (raw?.type !== "Feature" || raw?.geometry?.type !== "Point") {
    return null;
  }

  const coordinates = raw.geometry.coordinates;
  if (!Array.isArray(coordinates) || coordinates.length < 2) {
    return null;
  }

  const lng = Number(coordinates[0]);
  const lat = Number(coordinates[1]);
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) {
    return null;
  }

  const properties = raw.properties ?? {};
  const description =
    typeof properties.Description === "string" ? properties.Description : "";

  // New schema fields are embedded inside the Description HTML table.
  const block =
    (typeof properties.block === "string" ? properties.block : undefined) ??
    extractDescriptionField(description, "ADDRESSBLOCKHOUSENUMBER");
  const street =
    (typeof properties.street === "string" ? properties.street : undefined) ??
    extractDescriptionField(description, "ADDRESSSTREETNAME");
  const postalCode =
    (typeof properties.postalCode === "string" ? properties.postalCode : undefined) ??
    extractDescriptionField(description, "ADDRESSPOSTALCODE");

  const idCandidate =
    (typeof properties.id === "string" ? properties.id : undefined) ??
    (typeof properties.Name === "string" ? properties.Name : undefined);
  const nameCandidate =
    (typeof properties.name === "string" ? properties.name : undefined) ??
    (typeof properties.ADDRESSBUILDINGNAME === "string"
      ? properties.ADDRESSBUILDINGNAME
      : undefined);

  const derivedName =
    nameCandidate?.trim() ||
    [block, street].filter(Boolean).join(" ").trim() ||
    `Recycling Bin ${index + 1}`;

  return {
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [lng, lat]
    },
    properties: {
      id: idCandidate || `bin-${index + 1}`,
      name: derivedName,
      block,
      street,
      postalCode
    }
  };
}

function normalizeBinCollection(rawData: unknown): BinFeatureCollection {
  const raw = rawData as { type?: string; features?: unknown[] };
  if (raw?.type !== "FeatureCollection" || !Array.isArray(raw.features)) {
    throw new Error("Invalid GeoJSON FeatureCollection");
  }

  const features = raw.features
    .map((feature, index) => normalizeFeature(feature, index))
    .filter((feature): feature is BinFeature => feature !== null);

  return {
    type: "FeatureCollection",
    features
  };
}

function haversineMeters(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371000;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export default function MapPage() {
  const [geoJson, setGeoJson] = useState<BinFeatureCollection | null>(null);
  const [nearbyBins, setNearbyBins] = useState<NearbyBin[]>([]);
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [error, setError] = useState("");
  const [locationError, setLocationError] = useState("");
  const [locationPermissionDenied, setLocationPermissionDenied] = useState(false);
  const [requestingLocation, setRequestingLocation] = useState(false);
  const [mapLoadProgress, setMapLoadProgress] = useState(0);
  const [mapLoadLabel, setMapLoadLabel] = useState("Loading recycling bins...");

  const loadLocation = useCallback(async (surfaceError: boolean) => {
    if (surfaceError) {
      setLocationError("");
    }
    setRequestingLocation(true);

    try {
      const coords = await getCurrentPosition();
      setLocation(coords);
      setLocationPermissionDenied(false);
      const nearby = await getNearbyBins(coords.lat, coords.lng, 500);
      setNearbyBins(nearby);
    } catch (locationIssue) {
      const message =
        locationIssue instanceof Error ? locationIssue.message : "Unable to retrieve location.";
      if (/denied|permission/i.test(message)) {
        setLocationPermissionDenied(true);
      }
      if (surfaceError) {
        setLocationError(message);
      }
    } finally {
      setRequestingLocation(false);
    }
  }, []);

  useEffect(() => {
    const startedAt = Date.now();
    let permissionStatus: PermissionStatus | null = null;

    const loadMapData = async () => {
      try {
        setMapLoadProgress(5);
        setMapLoadLabel("Downloading map data...");
        const response = await fetch("/bins.geojson");
        if (!response.ok) {
          throw new Error("Failed to load map dataset");
        }

        let rawData: unknown;
        const contentLength = Number(response.headers.get("Content-Length") || 0);
        const stream = response.body;

        if (stream) {
          const reader = stream.getReader();
          const decoder = new TextDecoder();
          let receivedLength = 0;
          let text = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }
            if (value) {
              receivedLength += value.length;
              text += decoder.decode(value, { stream: true });
            }

            if (contentLength > 0) {
              const pct = Math.min(88, 5 + Math.round((receivedLength / contentLength) * 80));
              setMapLoadProgress(pct);
            } else {
              setMapLoadProgress((prev) => Math.min(88, prev + 3));
            }
          }

          text += decoder.decode();
          setMapLoadLabel("Parsing map data...");
          setMapLoadProgress(92);
          rawData = JSON.parse(text);
        } else {
          const text = await response.text();
          setMapLoadLabel("Parsing map data...");
          setMapLoadProgress(92);
          rawData = JSON.parse(text);
        }

        const data = normalizeBinCollection(rawData);
        setMapLoadProgress(100);
        setMapLoadLabel("Rendering map...");
        const elapsed = Date.now() - startedAt;
        if (elapsed < 700) {
          await new Promise((resolve) => setTimeout(resolve, 700 - elapsed));
        }
        setGeoJson(data);
      } catch {
        setError("Unable to load the recycling bin dataset.");
      }
    };

    const watchLocationPermission = async () => {
      if (!navigator.permissions?.query) {
        return;
      }

      try {
        permissionStatus = await navigator.permissions.query({ name: "geolocation" });
        const syncPermission = () => {
          setLocationPermissionDenied(permissionStatus?.state === "denied");
        };

        syncPermission();
        permissionStatus.onchange = syncPermission;
      } catch {
        return;
      }
    };

    loadMapData();
    void watchLocationPermission();
    void loadLocation(false);

    return () => {
      if (permissionStatus) {
        permissionStatus.onchange = null;
      }
    };
  }, [loadLocation]);

  useEffect(() => {
    if (geoJson || error) {
      return;
    }
    const timer = setInterval(() => {
      setMapLoadProgress((prev) => Math.min(88, prev + 2));
    }, 120);
    return () => clearInterval(timer);
  }, [geoJson, error]);

  const visibleBins = useMemo(() => {
    if (!geoJson || !location) {
      return [];
    }
    return geoJson.features.filter((bin) => {
      const [lng, lat] = bin.geometry.coordinates;
      return haversineMeters(location.lat, location.lng, lat, lng) <= 500;
    });
  }, [geoJson, location]);

  return (
    <AuthGuard>
      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white/75 p-4 shadow-card">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm uppercase tracking-[0.2em] text-moss/70">Recycling Map</p>
              <h2 className="text-2xl font-semibold">Find your nearest bin</h2>
            </div>
            <Link
              href="/log"
              className="rounded-full bg-moss px-4 py-2 text-sm font-semibold text-white"
            >
              Log Recycling
            </Link>
          </div>
          <p className="mt-2 text-sm text-ink/70">
            Explore NEA recycling bins across Singapore. Nearby bins are highlighted when location access is available.
          </p>
          {location && geoJson ? (
            <p className="mt-2 text-xs text-ink/60">
              Showing {visibleBins.length} bins within 500m of your location. <br></br>
              Green circle indicates 100m radius. <br></br>
              Red dot is your location.
            </p>
          ) : null}
        </div>

        {error ? <ErrorState message={error} /> : null}
        {locationError ? <ErrorState title="Location unavailable" message={locationError} /> : null}
        {locationPermissionDenied ? (
          <div className="rounded-[2rem] border border-white/60 bg-white/80 p-4 shadow-card">
            <p className="text-sm text-ink/80">
              Location access is currently blocked. Enable it to highlight bins around you.
            </p>
            <button
              type="button"
              onClick={() => void loadLocation(true)}
              disabled={requestingLocation}
              className="mt-3 rounded-full bg-moss px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            >
              {requestingLocation ? "Requesting location..." : "Grant Location Access"}
            </button>
          </div>
        ) : null}

        {!geoJson ? (
          <div className="rounded-[2rem] border border-white/60 bg-white/80 p-5 shadow-card">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-semibold text-ink/80">{mapLoadLabel}</p>
              <p className="text-sm text-ink/60">{mapLoadProgress}%</p>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-canvas">
              <div
                className="h-full rounded-full bg-moss transition-all duration-200 ease-out"
                style={{ width: `${Math.max(8, mapLoadProgress)}%` }}
              />
            </div>
          </div>
        ) : (
          <DynamicBinMap
            bins={visibleBins}
            nearbyBins={nearbyBins}
            userLocation={location}
          />
        )}
      </section>
    </AuthGuard>
  );
}
