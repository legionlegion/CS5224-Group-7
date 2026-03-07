"use client";

import { useEffect, useMemo } from "react";
import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer, Circle } from "react-leaflet";
import { BinFeature, NearbyBin } from "@/lib/types";

const defaultIcon = L.divIcon({
  className: "",
  html: '<div style="height:18px;width:18px;border-radius:9999px;background:#3f7d58;border:4px solid #d5f0dd"></div>',
  iconAnchor: [9, 9]
});

const userIcon = L.divIcon({
  className: "",
  html: '<div style="height:18px;width:18px;border-radius:9999px;background:#102217;border:4px solid #68b684"></div>',
  iconAnchor: [9, 9]
});

type BinMapProps = {
  bins: BinFeature[];
  nearbyBins?: NearbyBin[];
  userLocation?: { lat: number; lng: number } | null;
};

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
      <MapContainer center={defaultCenter} zoom={12} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

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

        {nearbyBins.map((bin) => (
          <Circle
            key={`circle-${bin.id}`}
            center={[bin.lat, bin.lng]}
            radius={45}
            pathOptions={{ color: "#bd6f44", fillColor: "#e7c89b", fillOpacity: 0.4 }}
          />
        ))}

        {userLocation ? (
          <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
            <Popup>Your location</Popup>
          </Marker>
        ) : null}
      </MapContainer>
    </div>
  );
}
