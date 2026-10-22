/** Live chat turn state: drives `streamChat`, parses partial answers once per frame, supports stop/retry. */
import { useQueryClient } from "@tanstack/react-query";
import { Allow, parse } from "partial-json";
import { useCallback, useEffect, useLayoutEffect, useReducer, useRef } from "react";
import { streamChat } from "../../api/chatStream";
import { ApiError } from "../../api/http";
import { invalidateAfterAnswer } from "../../api/queries";
import type { PartialAnswer } from "../answer/answerTypes";
import type {
  AssistantMessage,
  ChatRequest,
  ChatEvent,
  MetaEventData,
  OfficeMatch,
  QuotaScope,
  Stage,
  StreamErrorCode,
} from "../../api/types";

/** Why a turn did not finish. */
export type TurnFailure =
  /** The user pressed Stop. */
  | { kind: "stopped" }
  /** The server sent an `error` event. */
  | { kind: "stream"; code: StreamErrorCode; scope: QuotaScope | null }
  /** The server rejected the request before streaming (problem+json). */
  | { kind: "request"; code: string | null; retryAfter: number | null; scope: QuotaScope | null }
  /** The connection broke or the stream ended without `final`. */
  | { kind: "network" };

/** The question being answered right now (or just answered). */
export interface LiveTurn {
  text: string;
  conversationId: string | null;
  userMessageId: string | null;
  assistantMessageId: string | null;
  stage: Stage | null;
  sourceCount: number | null;
  office: OfficeMatch | null;
  partialAnswer: PartialAnswer | null;
  finalMessage: AssistantMessage | null;
  failure: TurnFailure | null;
  /** Epoch ms of the failure, for limits that block the input until `retry_after` passes. */
  failedAt: number | null;
  isStreaming: boolean;
}

/** Reducer actions. */
type Action =
  | { type: "start"; text: string; conversationId: string | null }
  | { type: "meta"; data: MetaEventData }
  | { type: "status"; stage: Stage; sourceCount: number | null }
  | { type: "office"; office: OfficeMatch }
  | { type: "partial"; answer: PartialAnswer }
  | { type: "final"; message: AssistantMessage }
  | { type: "fail"; failure: TurnFailure; at: number }
  | { type: "end" }
  | { type: "reset" };

/**
 * Pure state transitions of a live turn.
 *
 * @param turn Current turn, or `null` when idle.
 * @param action What happened.
 * @returns The next turn.
 */
export function turnReducer(turn: LiveTurn | null, action: Action): LiveTurn | null {
  if (action.type === "start") {
    return {
      text: action.text,
      conversationId: action.conversationId,
      userMessageId: null,
      assistantMessageId: null,
      stage: null,
      sourceCount: null,
      office: null,
      partialAnswer: null,
      finalMessage: null,
      failure: null,
      failedAt: null,
      isStreaming: true,
    };
  }
  if (action.type === "reset" || !turn) return null;
  switch (action.type) {
    case "meta":
      return {
        ...turn,
        conversationId: action.data.conversation_id,
        userMessageId: action.data.user_message_id,
        assistantMessageId: action.data.assistant_message_id,
      };
    case "status":
      return { ...turn, stage: action.stage, sourceCount: action.sourceCount ?? turn.sourceCount };
    case "office":
      return { ...turn, office: action.office };
    case "partial":
      return { ...turn, partialAnswer: action.answer };
    case "final":
      return { ...turn, finalMessage: action.message, office: action.message.office };
    case "fail":
      return { ...turn, failure: action.failure, failedAt: action.at, isStreaming: false };
    case "end":
      return {
        ...turn,
        isStreaming: false,
        failure: turn.failure ?? (turn.finalMessage ? null : { kind: "network" }),
      };
  }
}

/**
 * Parse the growing Answer JSON. Mid-stream fragments may not parse yet; then the previous partial stays.
 *
 * @param buffer All `delta` text so far.
 * @returns The partial answer, or `null` when the buffer cannot be parsed yet.
 */
export function parsePartialAnswer(buffer: string): PartialAnswer | null {
  try {
    const value: unknown = parse(buffer, Allow.ALL);
    return typeof value === "object" && value !== null ? value : null;
  } catch {
    // Expected while the first fragment is still incomplete; the `final` event carries the validated answer.
    return null;
  }
}

/**
 * Map a thrown value to a turn failure.
 *
 * @param error What `streamChat` threw.
 * @param stopped Whether the user pressed Stop.
 * @returns The failure.
 */
function toFailure(error: unknown, stopped: boolean): TurnFailure {
  if (stopped) return { kind: "stopped" };
  if (error instanceof ApiError) {
    return { kind: "request", code: error.code, retryAfter: error.retryAfter, scope: error.scope };
  }
  return { kind: "network" };
}

/** How long Retry waits before trying again after `409 stream_in_progress` (contract v1.4). */
export const BUSY_RETRY_DELAY_MS = 1000;

/**
 * Wait, unless the signal aborts first.
 *
 * @param ms Milliseconds to wait.
 * @param signal Abort signal (Stop / reset).
 * @returns Resolves after `ms`; rejects with the abort reason when aborted.
 */
function abortableDelay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(signal.reason as Error);
      },
      { once: true },
    );
  });
}

/** Thrown inside {@link streamWithBusyRetry} when the first SSE event says the lock race was lost. */
class LostLockRace extends Error {}

/**
 * Whether a failure means "another answer is still streaming" and a Retry may wait and try again.
 *
 * @param error What the stream threw.
 * @returns `true` for the pre-stream 409 or a lost lock race.
 */
function isBusy(error: unknown): boolean {
  return error instanceof LostLockRace || (error instanceof ApiError && error.code === "stream_in_progress");
}

/**
 * Open the chat stream. With `busyWaitMs`, "another answer is streaming" (pre-stream 409, or an SSE
 * `error` `stream_in_progress` as the first event, contract v1.6) is retried once after that wait.
 *
 * @param body Chat request.
 * @param signal Abort signal.
 * @param busyWaitMs Wait before the single retry, or `null` for no retry.
 * @yields Chat events.
 */
export async function* streamWithBusyRetry(
  body: ChatRequest,
  signal: AbortSignal,
  busyWaitMs: number | null,
): AsyncGenerator<ChatEvent> {
  const canRetry = busyWaitMs !== null;
  try {
    let first = true;
    for await (const event of streamChat(body, signal)) {
      const lostRace = first && event.event === "error" && event.data.code === "stream_in_progress";
      first = false;
      if (lostRace && canRetry) throw new LostLockRace();
      yield event;
    }
  } catch (error) {
    if (!canRetry || !isBusy(error)) throw error;
    await abortableDelay(busyWaitMs, signal);
    yield* streamChat(body, signal);
  }
}

/** Options of {@link useChatStream}. */
export interface ChatStreamOptions {
  /** Called once when the server created a new conversation (on `meta`). */
  onConversationStarted?: (conversationId: string) => void;
  /** Override of {@link BUSY_RETRY_DELAY_MS} (tests). */
  busyRetryDelayMs?: number;
}

/** What {@link useChatStream} returns. */
export interface ChatStream {
  turn: LiveTurn | null;
  send: (text: string, conversationId: string | null) => void;
  /** Resend a question as a Retry (one wait-and-retry on `409 stream_in_progress`). */
  resend: (text: string, conversationId: string | null) => void;
  stop: () => void;
  retry: () => void;
  reset: () => void;
}

/**
 * Stream one question at a time into a live turn.
 *
 * @param options Callbacks.
 * @returns The live turn and its controls.
 */
export function useChatStream(options: ChatStreamOptions = {}): ChatStream {
  const client = useQueryClient();
  const [turn, dispatch] = useReducer(turnReducer, null);
  const optionsRef = useRef(options);
  useLayoutEffect(() => {
    optionsRef.current = options;
  });
  const controllerRef = useRef<AbortController | null>(null);
  const frameRef = useRef<number | null>(null);
  const bufferRef = useRef("");

  /** Cancel any pending partial-JSON parse. */
  const cancelFrame = useCallback(() => {
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
  }, []);

  /** Append a fragment and parse at most once per animation frame. */
  const onDelta = useCallback((text: string) => {
    bufferRef.current += text;
    if (frameRef.current !== null) return;
    frameRef.current = requestAnimationFrame(() => {
      frameRef.current = null;
      const answer = parsePartialAnswer(bufferRef.current);
      if (answer) dispatch({ type: "partial", answer });
    });
  }, []);

  /** Apply one stream event. */
  const onEvent = useCallback(
    (event: ChatEvent, isNewChat: boolean) => {
      switch (event.event) {
        case "meta":
          dispatch({ type: "meta", data: event.data });
          if (isNewChat) optionsRef.current.onConversationStarted?.(event.data.conversation_id);
          return;
        case "status":
          dispatch({ type: "status", stage: event.data.stage, sourceCount: event.data.source_count ?? null });
          return;
        case "office":
          dispatch({ type: "office", office: event.data });
          return;
        case "delta":
          onDelta(event.data.text);
          return;
        case "final":
          cancelFrame();
          dispatch({ type: "final", message: event.data.message });
          return;
        case "error":
          cancelFrame();
          dispatch({
            type: "fail",
            failure: { kind: "stream", code: event.data.code, scope: event.data.scope ?? null },
            at: Date.now(),
          });
          return;
        case "done":
          return;
      }
    },
    [cancelFrame, onDelta],
  );

  /** Start a stream; `busyWaitMs` enables the one-time 409 retry (used by Retry). */
  const start = useCallback(
    (text: string, conversationId: string | null, busyWaitMs: number | null) => {
      if (controllerRef.current) return;
      const controller = new AbortController();
      controllerRef.current = controller;
      bufferRef.current = "";
      dispatch({ type: "start", text, conversationId });
      /** False once this stream was stopped by `reset` or replaced, so late results are ignored. */
      const isActive = () => controllerRef.current === controller;
      void (async () => {
        let answeredIn: string | null = conversationId;
        try {
          for await (const event of streamWithBusyRetry(
            { conversation_id: conversationId, text },
            controller.signal,
            busyWaitMs,
          )) {
            if (!isActive()) break;
            if (event.event === "meta") answeredIn = event.data.conversation_id;
            onEvent(event, conversationId === null);
          }
          if (isActive()) dispatch({ type: "end" });
        } catch (error) {
          cancelFrame();
          if (isActive()) {
            dispatch({ type: "fail", failure: toFailure(error, controller.signal.aborted), at: Date.now() });
          }
        } finally {
          if (isActive()) controllerRef.current = null;
        }
        if (answeredIn) {
          await invalidateAfterAnswer(client, answeredIn).catch((error: unknown) => console.error(error));
        }
      })();
    },
    [cancelFrame, client, onEvent],
  );

  /** Ask a new question. */
  const send = useCallback(
    (text: string, conversationId: string | null) => start(text, conversationId, null),
    [start],
  );

  /** Abort the running stream (the Stop button). */
  const stop = useCallback(() => controllerRef.current?.abort(), []);

  /** Retry a question (live or stored) with the one-time 409 wait. */
  const resend = useCallback(
    (text: string, conversationId: string | null) =>
      start(text, conversationId, optionsRef.current.busyRetryDelayMs ?? BUSY_RETRY_DELAY_MS),
    [start],
  );

  /** Resend the live turn's question into the same conversation. */
  const retry = useCallback(() => {
    if (turn && !turn.isStreaming) resend(turn.text, turn.conversationId);
  }, [resend, turn]);

  /** Abort and forget the live turn (new chat, another conversation). */
  const reset = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    cancelFrame();
    dispatch({ type: "reset" });
  }, [cancelFrame]);

  useEffect(() => () => controllerRef.current?.abort(), []);

  return { turn, send, resend, stop, retry, reset };
}
