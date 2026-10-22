import { Outlet } from "react-router";
import { OfflineBanner } from "./OfflineBanner";

/**
 * Top-level layout: global banners above every page.
 *
 * @returns The layout.
 */
export function RootLayout() {
  return (
    <>
      <OfflineBanner />
      <Outlet />
    </>
  );
}
