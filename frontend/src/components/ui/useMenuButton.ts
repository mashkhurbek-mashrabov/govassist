/**
 * The menu-button pattern shared by the language and account menus (components.md → LanguageMenu → Keyboard
 * and ARIA): open state, roving focus over the items, ↑ / ↓ / Home / End, Esc / Tab / an outside press close,
 * focus back to the button, and whether the viewport is phone-sized (the list is then a bottom sheet).
 */
import {
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject,
} from "react";

/** Below this width the list is a bottom sheet (components.md → LanguageMenu → Phone). */
const PHONE_QUERY = "(max-width: 767px)";

/**
 * Subscribe to the phone media query.
 *
 * @param onChange Called when it starts or stops matching.
 * @returns Unsubscribe.
 */
function subscribePhone(onChange: () => void): () => void {
  if (typeof window.matchMedia !== "function") return () => undefined;
  const query = window.matchMedia(PHONE_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/**
 * Whether the viewport is phone-sized (false where `matchMedia` is missing, e.g. tests).
 *
 * @returns `true` below 768 px.
 */
function isPhone(): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia(PHONE_QUERY).matches;
}

/** What a menu button component needs from {@link useMenuButton}. */
export interface MenuButton {
  open: boolean;
  /** Index of the item holding the roving `tabIndex={0}`. */
  focusIndex: number;
  /** Phone-sized viewport: render the open list as a bottom sheet in a portal. */
  phone: boolean;
  rootRef: RefObject<HTMLDivElement | null>;
  panelRef: RefObject<HTMLDivElement | null>;
  buttonRef: RefObject<HTMLButtonElement | null>;
  /** Ref callback for item `index`. */
  itemRef: (index: number) => (element: HTMLElement | null) => void;
  /** Open with item `index` focused. */
  openAt: (index: number) => void;
  /** Close; `refocus` gives focus back to the button (keyboard and choosing, not an outside press). */
  close: (refocus: boolean) => void;
  /** Button keys: ↓ / ↑ open at `index` (Enter and Space open through the click). */
  onButtonKeyDown: (event: ReactKeyboardEvent, index: number) => void;
  /** List keys: move, Esc / Tab close. */
  onPanelKeyDown: (event: ReactKeyboardEvent) => void;
}

/**
 * State and handlers for a menu button with `itemCount` focusable items.
 *
 * @param itemCount Number of focusable items in the list.
 * @returns The menu state, refs and handlers.
 */
export function useMenuButton(itemCount: number): MenuButton {
  const [open, setOpen] = useState(false);
  const [focusIndex, setFocusIndex] = useState(0);
  const phone = useSyncExternalStore(subscribePhone, isPhone, () => false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const items = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    if (open) items.current[focusIndex]?.focus();
  }, [open, focusIndex]);

  useEffect(() => {
    if (!open) return;
    /**
     * Close on a press outside the button and the list.
     *
     * @param event Pointer event.
     */
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (rootRef.current?.contains(target) || panelRef.current?.contains(target)) return;
      setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  /**
   * Open with an item focused.
   *
   * @param index Item to focus (clamped to the list).
   */
  const openAt = (index: number) => {
    setFocusIndex(Math.max(0, Math.min(index, itemCount - 1)));
    setOpen(true);
  };

  /**
   * Close the list.
   *
   * @param refocus Give focus back to the button.
   */
  const close = (refocus: boolean) => {
    setOpen(false);
    if (refocus) buttonRef.current?.focus();
  };

  /**
   * Button keys: ↓ / ↑ open (Enter and Space open through the click).
   *
   * @param event Key event.
   * @param index Item to focus when opening.
   */
  const onButtonKeyDown = (event: ReactKeyboardEvent, index: number) => {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    event.preventDefault();
    openAt(index);
  };

  /**
   * List keys: move, Esc / Tab close.
   *
   * @param event Key event.
   */
  const onPanelKeyDown = (event: ReactKeyboardEvent) => {
    const last = itemCount - 1;
    const moves: Record<string, number> = {
      ArrowDown: focusIndex === last ? 0 : focusIndex + 1,
      ArrowUp: focusIndex === 0 ? last : focusIndex - 1,
      Home: 0,
      End: last,
    };
    const next = moves[event.key];
    if (next !== undefined) {
      event.preventDefault();
      setFocusIndex(next);
      return;
    }
    if (event.key === "Escape" || event.key === "Tab") {
      event.preventDefault();
      close(true);
    }
  };

  /**
   * Ref callback for an item.
   *
   * @param index The item's position.
   * @returns The callback.
   */
  const itemRef = (index: number) => (element: HTMLElement | null) => {
    items.current[index] = element;
  };

  return {
    open,
    focusIndex,
    phone,
    rootRef,
    panelRef,
    buttonRef,
    itemRef,
    openAt,
    close,
    onButtonKeyDown,
    onPanelKeyDown,
  };
}
