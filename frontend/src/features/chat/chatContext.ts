import { useOutletContext } from "react-router";
import type { ChatStream } from "./useChatStream";

/**
 * The chat stream owned by `ChatLayout`, shared with the chat pages through the outlet context.
 *
 * @returns The stream and its controls.
 */
export function useChatContext(): ChatStream {
  return useOutletContext<ChatStream>();
}
