import { useEffect, useId, useRef } from "react";
import { useTranslation } from "react-i18next";

/** Props of {@link ConfirmDialog}. */
interface ConfirmDialogProps {
  open: boolean;
  title: string;
  body: string;
  confirmLabel: string;
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Modal confirmation on the native `<dialog>` (focus trap and Esc come from the browser).
 *
 * @param props Open state, texts and callbacks.
 * @returns The dialog.
 */
export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  pending,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={ref} aria-labelledby={titleId} onCancel={onCancel} className="m-auto border p-4">
      <h2 id={titleId}>{title}</h2>
      <p>{body}</p>
      <div className="mt-4 flex gap-2">
        <button type="button" className="min-h-11 px-3" onClick={onCancel}>
          {t("common.cancel")}
        </button>
        <button type="button" className="min-h-11 px-3" onClick={onConfirm} disabled={pending}>
          {confirmLabel}
        </button>
      </div>
    </dialog>
  );
}
