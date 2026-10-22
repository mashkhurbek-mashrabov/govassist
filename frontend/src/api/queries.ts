/** TanStack Query keys, query options and mutation hooks. The single place for server state. */
import {
  queryOptions,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import * as auth from "./auth";
import * as api from "./endpoints";
import type { Conversation, Feedback, Lang, Me, MeUpdate } from "./types";

/** Who is using the app: the allauth session plus `/me` when signed in. */
export type Viewer =
  { state: "anonymous" } | { state: "pending_verification" } | { state: "authenticated"; me: Me };

/** Every query key, defined once. */
export const queryKeys = {
  viewer: ["viewer"] as const,
  providers: ["auth", "providers"] as const,
  regions: (lang: Lang) => ["geo", "regions", lang] as const,
  districts: (regionId: number, lang: Lang) => ["geo", "districts", regionId, lang] as const,
  suggestions: (lang: Lang) => ["suggestions", lang] as const,
  sources: ["sources"] as const,
  conversations: ["conversations"] as const,
  conversation: (id: string) => ["conversation", id] as const,
};

/**
 * Load the session, then `/me` when authenticated.
 *
 * @returns The current viewer.
 */
async function fetchViewer(): Promise<Viewer> {
  const state = await auth.getSession();
  if (state !== "authenticated") return { state };
  return { state, me: await api.getMe() };
}

/** Viewer query; refreshed explicitly after every auth change. */
export const viewerQuery = queryOptions({
  queryKey: queryKeys.viewer,
  queryFn: fetchViewer,
  staleTime: Infinity,
});

/**
 * Re-read the session after login, signup, verification or a password reset.
 *
 * @param client The query client.
 * @returns The fresh viewer.
 */
export function refreshViewer(client: QueryClient): Promise<Viewer> {
  return client.query({ ...viewerQuery, staleTime: 0 });
}

/**
 * Drop every cached user query and mark the viewer anonymous (logout, 401, account deletion).
 *
 * @param client The query client.
 */
export function resetToAnonymous(client: QueryClient): void {
  // Keep the viewer query itself so mounted observers (AppShell) see the change and redirect.
  client.removeQueries({ predicate: (query) => query.queryKey[0] !== queryKeys.viewer[0] });
  client.setQueryData(viewerQuery.queryKey, { state: "anonymous" });
}

/**
 * Current UI language as a contract `Lang`.
 *
 * @returns The active i18next language.
 */
function useLang(): Lang {
  return useTranslation().i18n.language as Lang;
}

/**
 * The current viewer (already loaded by the route guards).
 *
 * @returns The viewer query.
 */
export function useViewer() {
  return useQuery(viewerQuery);
}

/**
 * The signed-in user, or `null` once the session ended (logout, 401, account deletion).
 *
 * @returns `Me` or `null`.
 */
export function useMaybeMe(): Me | null {
  const { data } = useViewer();
  return data?.state === "authenticated" ? data.me : null;
}

/**
 * Enabled social login providers.
 *
 * @returns The providers query.
 */
export function useProviders() {
  return useQuery({ queryKey: queryKeys.providers, queryFn: auth.getProviders, staleTime: Infinity });
}

/**
 * Regions with names in the UI language.
 *
 * @returns The regions query.
 */
export function useRegions() {
  const lang = useLang();
  return useQuery({
    queryKey: queryKeys.regions(lang),
    queryFn: () => api.getRegions(lang),
    staleTime: Infinity,
  });
}

/**
 * Districts of a region; idle until a region is picked.
 *
 * @param regionId Selected region, or `null`.
 * @returns The districts query.
 */
export function useDistricts(regionId: number | null) {
  const lang = useLang();
  return useQuery({
    queryKey: queryKeys.districts(regionId ?? 0, lang),
    queryFn: () => api.getDistricts(regionId ?? 0, lang),
    enabled: regionId !== null,
    staleTime: Infinity,
  });
}

/**
 * Starter questions in the UI language.
 *
 * @returns The suggestions query.
 */
export function useSuggestions() {
  const lang = useLang();
  return useQuery({ queryKey: queryKeys.suggestions(lang), queryFn: api.getSuggestions });
}

/**
 * Reviewed sources for the About page (public).
 *
 * @returns The sources query.
 */
export function useSources() {
  return useQuery({ queryKey: queryKeys.sources, queryFn: api.getSources, staleTime: Infinity });
}

/**
 * Cursor-paginated history.
 *
 * @returns The infinite conversations query.
 */
export function useConversations() {
  return useInfiniteQuery({
    queryKey: queryKeys.conversations,
    queryFn: ({ pageParam }) => api.listConversations(pageParam),
    initialPageParam: null as string | null,
    getNextPageParam: (page) => page.next,
  });
}

/**
 * One conversation; idle for a new chat.
 *
 * @param id Conversation id, or `null` for a new chat.
 * @returns The conversation query.
 */
export function useConversation(id: string | null) {
  return useQuery({
    queryKey: queryKeys.conversation(id ?? ""),
    queryFn: () => api.getConversation(id ?? ""),
    enabled: id !== null,
  });
}

/**
 * Refresh what a finished answer changes: the conversation, the history and the quota.
 *
 * @param client The query client.
 * @param conversationId Conversation that got a new answer.
 */
export async function invalidateAfterAnswer(client: QueryClient, conversationId: string): Promise<void> {
  await Promise.all([
    client.invalidateQueries({ queryKey: queryKeys.conversation(conversationId) }),
    client.invalidateQueries({ queryKey: queryKeys.conversations }),
    refreshViewer(client),
  ]);
}

/**
 * PATCH `/me` and store the result as the viewer.
 *
 * @returns The mutation.
 */
export function useUpdateMe() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (update: MeUpdate) => api.updateMe(update),
    onSuccess: (me) => {
      const viewer: Viewer = { state: "authenticated", me };
      client.setQueryData(viewerQuery.queryKey, viewer);
    },
  });
}

/**
 * Delete a conversation and refresh the history.
 *
 * @returns The mutation.
 */
export function useDeleteConversation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: async (_result, id) => {
      client.removeQueries({ queryKey: queryKeys.conversation(id) });
      await client.invalidateQueries({ queryKey: queryKeys.conversations });
    },
  });
}

/** Variables of {@link useSendFeedback}. */
interface FeedbackVariables {
  conversationId: string;
  messageId: string;
  feedback: Feedback;
}

/**
 * Upsert feedback and write it into the cached conversation.
 *
 * @returns The mutation.
 */
export function useSendFeedback() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ messageId, feedback }: FeedbackVariables) => api.sendFeedback(messageId, feedback),
    onSuccess: (saved, { conversationId, messageId }) => {
      client.setQueryData<Conversation>(queryKeys.conversation(conversationId), (conversation) =>
        conversation
          ? {
              ...conversation,
              messages: conversation.messages.map((message) =>
                message.id === messageId && message.role === "assistant"
                  ? { ...message, feedback: saved }
                  : message,
              ),
            }
          : conversation,
      );
    },
  });
}

/**
 * Delete the account, then forget every cached query.
 *
 * @returns The mutation.
 */
export function useDeleteAccount() {
  const client = useQueryClient();
  return useMutation({ mutationFn: api.deleteMe, onSuccess: () => resetToAnonymous(client) });
}

/**
 * Log out and forget every cached query.
 *
 * @returns The mutation.
 */
export function useLogout() {
  const client = useQueryClient();
  return useMutation({ mutationFn: auth.logout, onSuccess: () => resetToAnonymous(client) });
}

/**
 * Wrap an allauth call that changes the session so the viewer is re-read afterwards.
 *
 * @param call The allauth call.
 * @returns A mutation resolving to the fresh viewer.
 */
export function useAuthMutation<TInput>(call: (input: TInput) => Promise<auth.AuthState>) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (input: TInput) => {
      await call(input);
      return refreshViewer(client);
    },
  });
}
