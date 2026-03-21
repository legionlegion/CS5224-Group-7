"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
  onCapture: (file: File) => void;
}

export function CameraCapture({ onCapture }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [cameraPermissionDenied, setCameraPermissionDenied] = useState(false);
  const [requestingCamera, setRequestingCamera] = useState(false);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const startCamera = useCallback(
    async (requestedByUser: boolean) => {
      setError(null);
      setRequestingCamera(requestedByUser);

      try {
        stopCamera();
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" }
          },
          audio: false
        });

        setCameraPermissionDenied(false);
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (cameraError) {
        const errorName = (cameraError as DOMException | undefined)?.name ?? "";
        if (errorName === "NotAllowedError" || errorName === "PermissionDeniedError") {
          setCameraPermissionDenied(true);
          setError("Camera access is blocked. Allow access to continue.");
        } else {
          setError("Camera access is required to log recycling activity.");
        }
      } finally {
        setRequestingCamera(false);
      }
    },
    [stopCamera]
  );

  useEffect(() => {
    let permissionStatus: PermissionStatus | null = null;

    const watchCameraPermission = async () => {
      if (!navigator.permissions?.query) {
        return;
      }

      try {
        permissionStatus = await navigator.permissions.query({
          name: "camera" as PermissionName
        });
        const syncPermission = () => {
          setCameraPermissionDenied(permissionStatus?.state === "denied");
        };
        syncPermission();
        permissionStatus.onchange = syncPermission;
      } catch {
        return;
      }
    };

    void watchCameraPermission();
    void startCamera(false);

    return () => {
      if (permissionStatus) {
        permissionStatus.onchange = null;
      }
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const captureImage = async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) {
      return;
    }
    if (!video.videoWidth || !video.videoHeight) {
      setError("Camera is still starting. Please try again.");
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
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
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
      {cameraPermissionDenied ? (
        <button
          type="button"
          onClick={() => void startCamera(true)}
          disabled={requestingCamera}
          className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white disabled:opacity-70"
        >
          {requestingCamera ? "Requesting camera..." : "Grant Camera Access"}
        </button>
      ) : (
        <button
          type="button"
          onClick={captureImage}
          className="w-full rounded-2xl bg-moss px-4 py-3 font-semibold text-white"
        >
          {previewUrl ? "Retake Photo" : "Capture Photo"}
        </button>
      )}
    </div>
  );
}
