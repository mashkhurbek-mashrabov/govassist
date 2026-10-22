import { Outlet } from "react-router";
import { ToastProvider } from "../../components/ui/ToastProvider";
import { BackOnlineToast } from "./BackOnlineToast";

/**
 * Top-level layout: the toast region and connectivity notices around every page.
 *
 * @returns The layout.
 */
export function RootLayout() {
  return (
    <ToastProvider>
      <BackOnlineToast />
      <Outlet />
    </ToastProvider>
  );
}
