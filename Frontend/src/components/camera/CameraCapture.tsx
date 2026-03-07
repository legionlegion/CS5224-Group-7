"use client";

import { useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
  onCapture: (file: File) => void;
}

export function CameraCapture({ onCapture }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" }
          },
          audio: false
        });

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (cameraError) {
        setError("Camera access is required to log recycling activity.");
      }
    };

    startCamera();

    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const captureImage = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) {
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    if (!context) {
      setError("Unable to capture the camera frame.");
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.92)
    );

    if (!blob) {
      setError("Capture failed. Please try again.");
      return;
    }

    const file = new File([blob], `recycling-${Date.now()}.jpg`, { type: "image/jpeg" });
    setPreviewUrl(URL.createObjectURL(file));
    onCapture(file);
  };

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-ink shadow-card">
        {previewUrl ? (
          <img src={previewUrl} alt="Captured recycling" className="h-[360px] w-full object-cover" />
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="h-[360px] w-full object-cover"
          />
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" />
      {error ? <p className="text-sm text-clay">{error}</p> : null}
      <button
        type="button"
        onClick={captureImage}
        className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white"
      >
        {previewUrl ? "Retake Photo" : "Capture Photo"}
      </button>
    </div>
  );
}
