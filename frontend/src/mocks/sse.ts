/** Mock chat stream: emits contract §4 events with the §6 fixture, fragmenting the Answer JSON. */
import { HttpResponse } from "msw";
import type { Answer, AssistantMessage, ChatEventName, MetaEventData, OfficeMatch } from "../api/types";

/** One SSE frame: an event or a keep-alive comment. */
export type SseFrame = { event: ChatEventName; data: unknown } | { comment: string };

/** Characters per `delta` fragment, small enough to cut keys and strings mid-way. */
const DELTA_SIZE = 24;
/** Pause between frames in the browser; tests use no timers at all. */
const FRAME_DELAY_MS = import.meta.env.MODE === "test" ? 0 : 60;

/**
 * Serialize one frame in SSE wire format.
 *
 * @param frame Event or comment.
 * @returns Wire text ending with a blank line.
 */
export function encodeFrame(frame: SseFrame): string {
  if ("comment" in frame) return `: ${frame.comment}\n\n`;
  return `event: ${frame.event}\ndata: ${JSON.stringify(frame.data)}\n\n`;
}

/**
 * Split the Answer JSON into raw fragments, like Gemini's streamed output.
 *
 * @param answer The answer to stream.
 * @returns `delta` frames with a ping in the middle.
 */
function deltaFrames(answer: Answer): SseFrame[] {
  const json = JSON.stringify(answer);
  const frames: SseFrame[] = [];
  for (let start = 0; start < json.length; start += DELTA_SIZE) {
    frames.push({ event: "delta", data: { text: json.slice(start, start + DELTA_SIZE) } });
  }
  frames.splice(Math.floor(frames.length / 2), 0, { comment: "ping" });
  return frames;
}

/**
 * Frames of a successful answer.
 *
 * @param meta Ids for the `meta` event.
 * @param message Final assistant message.
 * @param office Office match to send early, or `null`.
 * @returns The frame list in contract order.
 */
export function successFrames(
  meta: MetaEventData,
  message: AssistantMessage,
  office: OfficeMatch | null,
): SseFrame[] {
  const answer = message.answer;
  if (!answer) throw new Error("successFrames needs a message with an answer");
  return [
    { event: "meta", data: meta },
    { event: "status", data: { stage: "searching" } },
    { event: "status", data: { stage: "found", source_count: message.sources.length } },
    ...(office ? [{ event: "office" as const, data: office }] : []),
    { event: "status", data: { stage: "writing" } },
    ...deltaFrames(answer),
    { event: "final", data: { message } },
    { event: "done", data: {} },
  ];
}

/**
 * Frames of a stream that fails after `meta`.
 *
 * @param meta Ids for the `meta` event.
 * @returns The frame list.
 */
export function errorFrames(meta: MetaEventData): SseFrame[] {
  return [
    { event: "meta", data: meta },
    { event: "status", data: { stage: "searching" } },
    { event: "error", data: { code: "llm_unavailable", message: "SAMPLE: model unavailable" } },
  ];
}

/**
 * The lone frame of a lost lock race (contract v1.6): `error` `stream_in_progress`, no `meta`.
 *
 * @returns The frame.
 */
export function raceFrame(): SseFrame {
  return {
    event: "error",
    data: { code: "stream_in_progress", message: "SAMPLE: another answer is streaming" },
  };
}

/**
 * Wait between frames.
 *
 * @param ms Milliseconds.
 * @returns A promise that resolves after the delay.
 */
function pause(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * An SSE response that writes the frames one by one and stops when the client aborts.
 *
 * @param frames Frames to send.
 * @param hooks `onComplete` after the last frame, `onAbort` when the client disconnects first.
 * @returns The streaming response.
 */
export function sseResponse(
  frames: SseFrame[],
  hooks: { onComplete?: () => void; onAbort?: () => void } = {},
): HttpResponse<ReadableStream> {
  const encoder = new TextEncoder();
  let cancelled = false;
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      for (const frame of frames) {
        if (FRAME_DELAY_MS > 0) await pause(FRAME_DELAY_MS);
        if (cancelled) return;
        controller.enqueue(encoder.encode(encodeFrame(frame)));
      }
      hooks.onComplete?.();
      controller.close();
    },
    cancel() {
      cancelled = true;
      hooks.onAbort?.();
    },
  });
  return new HttpResponse(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache", "X-Accel-Buffering": "no" },
  });
}

/**
 * Frames of an answer that has no streamed text (contract v1.11 `sources`: built without the LLM).
 *
 * @param meta Ids for the `meta` event.
 * @param message Final assistant message.
 * @returns meta → final → done.
 */
export function finalOnlyFrames(meta: MetaEventData, message: AssistantMessage): SseFrame[] {
  return [
    { event: "meta", data: meta },
    { event: "final", data: { message } },
    { event: "done", data: {} },
  ];
}
