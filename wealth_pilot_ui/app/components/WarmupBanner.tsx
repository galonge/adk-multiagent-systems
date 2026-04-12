"use client";

interface WarmupBannerProps {
  modelName: string;
  onSwitchToGemini: () => void;
  onDismiss: () => void;
}

export function WarmupBanner({
  modelName,
  onSwitchToGemini,
  onDismiss,
}: WarmupBannerProps) {
  return (
    <div className="warmup-banner" id="warmup-banner">
      <div className="warmup-content">
        <span className="warmup-icon">⏳</span>
        <span className="warmup-text">
          <strong>{modelName}</strong> is warming up (~5 min)
        </span>
        <button
          className="warmup-switch"
          onClick={onSwitchToGemini}
          type="button"
        >
          Switch to Gemini →
        </button>
      </div>
      <button
        className="warmup-dismiss"
        onClick={onDismiss}
        type="button"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  );
}
