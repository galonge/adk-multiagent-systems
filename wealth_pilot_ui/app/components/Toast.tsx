"use client";

import { useEffect, useState } from "react";

interface ToastProps {
  message: string;
  visible: boolean;
  onDismiss: () => void;
}

export function Toast({ message, visible, onDismiss }: ToastProps) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (visible) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShow(true); // intentional: sync animation state with visibility prop
      const timer = setTimeout(() => {
        setShow(false);
        setTimeout(onDismiss, 300); // wait for animation
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [visible, onDismiss]);

  if (!visible && !show) return null;

  return (
    <div className={`toast ${show ? "toast-in" : "toast-out"}`} id="toast">
      <span className="toast-icon">✓</span>
      <span className="toast-text">{message}</span>
      <button
        className="toast-dismiss"
        onClick={() => {
          setShow(false);
          setTimeout(onDismiss, 300);
        }}
        type="button"
      >
        ×
      </button>
    </div>
  );
}
