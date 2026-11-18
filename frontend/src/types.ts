export type Telemetry = {
  original_tokens: number;
  compressed_tokens: number;
  prompt_tokens: number;
  compression_ratio: number;
  compression_latency_ms: number;
  input_cost_usd: number;
  estimated_total_cost_usd: number;
  task: string;
};

export type CompressorMetadata = {
  method?: string;
  target_ratio_requested?: number;
  calibrated_rate_used?: number;
  actual_ratio?: number;
  refinements?: number;
  selected_tokens?: number;
  chunks_created?: number;
  chunks_selected?: number;
  chunking?: {
    tokenizer: string;
    chunk_size_tokens: number;
    chunk_overlap_tokens: number;
    chunks_created: number;
    chunks_selected: number;
  };
  [key: string]: unknown;
};

export type CompressionInfo = {
  context: string;
  telemetry: Telemetry;
  compressor_metadata: CompressorMetadata;
};

export type LlmStats = {
  model: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number;
  time_to_first_token_ms: number | null;
};

export type Attachment = {
  id: string;
  name: string;
  kind: "file" | "paste" | "sample";
  text: string;
  tokens: number;
};

export type UserMessage = {
  id: string;
  role: "user";
  content: string;
  createdAt: number;
};

export type AssistantStatus = "compressing" | "generating" | "done" | "error" | "stopped";

export type AssistantMessage = {
  id: string;
  role: "assistant";
  content: string;
  createdAt: number;
  status: AssistantStatus;
  error?: string;
  compression?: CompressionInfo;
  llm?: LlmStats;
  targetRatio: number;
  tokenBudget: number | null;
};

export type Message = UserMessage | AssistantMessage;

export type Task = "unspecified" | "extractive_qa" | "multi_hop_qa" | "summarization";

export type ConvSettings = {
  targetRatio: number;
  tokenBudget: number | null;
  task: Task;
  /** null means "use the global system instruction". */
  systemInstruction: string | null;
};

export type Conversation = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  attachments: Attachment[];
  messages: Message[];
  settings: ConvSettings;
};

export type GlobalSettings = {
  systemInstruction: string;
  temperature: number;
  model: string | null;
  theme: "system" | "light" | "dark";
};

export type Health = {
  status: string;
  llm: {
    base_url: string;
    default_model: string;
    reachable: boolean;
    models: string[];
    error?: string;
  };
  compressor: { model_name: string; use_llmlingua: boolean; loaded: boolean };
  config: {
    target_ratio: number;
    chunk_size_tokens: number;
    chunk_overlap_tokens: number;
    top_k_chunks: number;
    adaptive_control: boolean;
    tolerance: number;
    encoding_name: string;
    ratios: number[];
  };
};

export type Sample = {
  id: string;
  task: Task;
  system_instruction: string;
  question: string;
  context: string;
  reference: string;
};

export type SummaryRow = Record<string, number | string | null>;

export type ChatEvent =
  | { type: "status"; stage: "compressing" | "generating" }
  | ({ type: "compression" } & CompressionInfo)
  | { type: "token"; text: string }
  | { type: "done"; llm: LlmStats }
  | { type: "error"; stage: string; message: string };
