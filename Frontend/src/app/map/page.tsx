"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { getNearbyBins } from "@/lib/api";
import { getCurrentPosition } from "@/lib/geolocation";
import { BinFeatureCollection, NearbyBin } from "@/lib/types";

const DynamicBinMap = dynamic(
  () => import("@/components/map/BinMap").then((mod) => mod.BinMap),
  { ssr: false }
);

export default function MapPage() {
  const [geoJson, setGeoJson] = useState<BinFeatureCollection | null>(null);
  const [nearbyBins, setNearbyBins] = useState<NearbyBin[]>([]);
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadMapData = async () => {
      try {
        const response = await fetch("/bins.geojson");
        const data = (await response.json()) as BinFeatureCollection;
        setGeoJson(data);
      } catch {
        setError("Unable to load the recycling bin dataset.");
      }
    };

    const loadLocation = async () => {
      try {
        const coords = await getCurrentPosition();
        setLocation(coords);
        const nearby = await getNearbyBins(coords.lat, coords.lng, 500);
        setNearbyBins(nearby);
      } catch {
        return;
      }
    };

    loadMapData();
    loadLocation();
  }, []);

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
        </div>

        {error ? <ErrorState message={error} /> : null}

        {!geoJson ? (
          <LoadingState label="Loading recycling bins..." />
        ) : (
          <DynamicBinMap
            bins={geoJson.features}
            nearbyBins={nearbyBins}
            userLocation={location}
          />
        )}
      </section>
    </AuthGuard>
  );
}
