import { Trash2 } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "./Button";

/** Props of {@link ConfirmDialog}. */
interface ConfirmDialogProps {
  open: boolean;
  title: string;
  body: string;
  confirmLabel: string;
  busy?: boolean;
  busyLabel?: string;
  /** When set, a checkbox with this label must be ticked before the destructive button works. */
  confirmCheck?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Destructive confirmation (components.md → Dialog) on the native modal `<dialog>`: focus trap,
 * Esc and focus return come from the browser. Focus starts on Cancel, which is first in the DOM.
 *
 * @param props Open state, texts, optional confirm checkbox and callbacks.
 * @returns The dialog.
 */
export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  busy,
  busyLabel,
  confirmCheck,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const { t } = useTranslation();
  const ref = useRef<HTMLDialogElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const bodyId = useId();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      cancelRef.current?.focus();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions -- backdrop click; Esc comes from the native dialog (onCancel)
    <dialog
      ref={ref}
      className="dialog"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={bodyId}
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      onClick={(event) => {
        if (event.target === ref.current) onCancel();
      }}
      onClose={() => setChecked(false)}
    >
      <h2 id={titleId}>{title}</h2>
      <p id={bodyId}>{body}</p>
      {confirmCheck && (
        <label className="check">
          <input type="checkbox" checked={checked} onChange={(event) => setChecked(event.target.checked)} />
          <span>{confirmCheck}</span>
        </label>
      )}
      <div className="dialog__actions">
        <button ref={cancelRef} type="button" className="btn btn--secondary" onClick={onCancel}>
          <span>{t("common.cancel")}</span>
        </button>
        <Button
          variant="danger"
          icon={<Trash2 className="icon" aria-hidden="true" />}
          busy={busy}
          busyLabel={busyLabel}
          disabled={confirmCheck !== undefined && !checked}
          onClick={onConfirm}
        >
          {confirmLabel}
        </Button>
      </div>
    </dialog>
  );
}
