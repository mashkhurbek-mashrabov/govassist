import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useToast } from "../../components/ui/toastContext";
import { useOnline } from "./useOnline";

/**
 * Shows "back online" once the connection returns after being lost.
 *
 * @returns Nothing visible itself.
 */
export function BackOnlineToast() {
  const { t } = useTranslation();
  const online = useOnline();
  const showToast = useToast();
  const wasOffline = useRef(!online);

  useEffect(() => {
    if (!online) wasOffline.current = true;
    else if (wasOffline.current) {
      wasOffline.current = false;
      showToast(t("chat_error.back_online"));
    }
  }, [online, showToast, t]);

  return null;
}
