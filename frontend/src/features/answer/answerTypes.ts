/** Shapes of an answer that is still streaming. */
import type { Answer, Item, LawPoint } from "../../api/types";

/** Recursive partial: any nested field may be missing while the JSON is incomplete. */
export type DeepPartial<T> = T extends (infer U)[]
  ? DeepPartial<U>[]
  : T extends object
    ? { [K in keyof T]?: DeepPartial<T[K]> }
    : T;

/** An answer that is still arriving: any field may be missing or cut short. */
export type PartialAnswer = DeepPartial<Answer>;
/** A cited item that may be cut short. */
export type DeepPartialItem = DeepPartial<Item>;
/** A law point that may be cut short. */
export type DeepPartialLawPoint = DeepPartial<LawPoint>;
