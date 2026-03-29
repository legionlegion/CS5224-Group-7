"use client";

import { useEffect, useMemo } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, Circle, useMap } from "react-leaflet";
import { BinFeature, NearbyBin } from "@/lib/types";

const defaultIcon = L.divIcon({
  className: "",
  html: '<div style="height:18px;width:18px;border-radius:9999px;background:#3f7d58;border:4px solid #d5f0dd"></div>',
  iconAnchor: [9, 9]
});

const userIcon = L.divIcon({
  className: "",
  html: `
    <div style="position:relative;width:18px;height:18px;">
      <div style="position:absolute;left:0;top:0;width:18px;height:18px;background:#dc2626;border:2px solid #fecaca;border-radius:9999px;box-shadow:0 0 0 1px rgba(0,0,0,0.16);"></div>
      <div style="position:absolute;left:6px;top:6px;width:6px;height:6px;background:#ffffff;border-radius:9999px;"></div>
      <div style="position:absolute;left:7px;top:16px;width:0;height:0;border-left:2px solid transparent;border-right:2px solid transparent;border-top:7px solid #dc2626;"></div>
    </div>
  `,
  iconAnchor: [9, 24],
  popupAnchor: [0, -20]
});

type BinMapProps = {
  bins: BinFeature[];
  nearbyBins?: NearbyBin[];
  userLocation?: { lat: number; lng: number } | null;
};

function ViewportController({
  userLocation
}: {
  userLocation?: { lat: number; lng: number } | null;
}) {
  const map = useMap();

  useEffect(() => {
    if (!userLocation) {
      return;
    }
    map.setView([userLocation.lat, userLocation.lng], 18, { animate: true });
  }, [map, userLocation]);

  return null;
}

export function BinMap({ bins, nearbyBins = [], userLocation }: BinMapProps) {
  const nearbyLookup = useMemo(
    () => new Set(nearbyBins.map((bin) => bin.id)),
    [nearbyBins]
  );

  useEffect(() => {
    L.Marker.prototype.options.icon = defaultIcon;
  }, []);

  const defaultCenter: [number, number] = userLocation
    ? [userLocation.lat, userLocation.lng]
    : [1.3521, 103.8198];

  return (
    <div className="h-[58vh] overflow-hidden rounded-[2rem] border border-white/60 shadow-card">
      <MapContainer center={defaultCenter} zoom={userLocation ? 16 : 12} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ViewportController userLocation={userLocation} />

        {bins.map((bin) => {
          const [lng, lat] = bin.geometry.coordinates;
          const highlight = nearbyLookup.has(bin.properties.id);

          return (
            <Marker
              key={bin.properties.id}
              position={[lat, lng]}
              icon={
                highlight
                  ? L.divIcon({
                      className: "",
                      html: '<div style="height:18px;width:18px;border-radius:9999px;background:#bd6f44;border:4px solid #e7c89b"></div>',
                      iconAnchor: [9, 9]
                    })
                  : defaultIcon
              }
            >
              <Popup>
                <div className="space-y-1">
                  <p className="font-semibold">{bin.properties.name}</p>
                  <p className="text-sm">
                    {[bin.properties.block, bin.properties.street]
                      .filter(Boolean)
                      .join(" ")}
                  </p>
                  {bin.properties.postalCode ? (
                    <p className="text-sm">Singapore {bin.properties.postalCode}</p>
                  ) : null}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {userLocation ? (
          <Circle
            center={[userLocation.lat, userLocation.lng]}
            radius={100}
            pathOptions={{ color: "#3f7d58", fillColor: "#68b684", fillOpacity: 0.3 }}
          />
        ) : null}

        {userLocation ? (
          <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
            <Popup>Your location</Popup>
          </Marker>
        ) : null}
      </MapContainer>
    </div>
  );
}
