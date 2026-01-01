// OISP Model Registry Types
// Auto-generated from models.dev - DO NOT EDIT MANUALLY
// Source: https://models.dev/api.json
// Generated: 2025-12-29T20:31:51.575309+00:00

export type AIProvider =
  | 'aihubmix'
  | 'alibaba'
  | 'alibaba_cn'
  | 'anthropic'
  | 'aws_bedrock'
  | 'azure_cognitive_services'
  | 'azure_openai'
  | 'bailing'
  | 'baseten'
  | 'cerebras'
  | 'chutes'
  | 'cloudflare_ai_gateway'
  | 'cloudflare_workers_ai'
  | 'cohere'
  | 'cortecs'
  | 'deepinfra'
  | 'deepseek'
  | 'fastrouter'
  | 'fireworks'
  | 'friendli'
  | string;

export type ModelMode =
  | 'chat'
  | 'completion'
  | 'embedding'
  | 'image'
  | 'audio_transcription'
  | 'audio_speech'
  | 'moderation'
  | 'rerank';

export type ModelCapability =
  | 'vision'
  | 'function_calling'
  | 'json_mode'
  | 'reasoning'
  | 'temperature'
  | 'audio_input'
  | 'audio_output'
  | 'video_input'
  | 'image_output'
  | 'pdf_input';

export interface ModelInfo {
  id: string;
  provider: AIProvider;
  name?: string;
  family?: string;
  mode: ModelMode;
  max_input_tokens?: number;
  max_output_tokens?: number;
  input_cost_per_1k?: number;
  output_cost_per_1k?: number;
  cache_read_cost_per_1k?: number;
  cache_write_cost_per_1k?: number;
  reasoning_cost_per_1k?: number;
  capabilities?: ModelCapability[];
  knowledge_cutoff?: string;
  release_date?: string;
  open_weights?: boolean;
  deprecated?: boolean;
}

export interface ProviderInfo {
  name: string;
  api_endpoint?: string;
  documentation?: string;
  env_vars: string[];
  logo_url?: string;
  model_count: number;
  models: string[];
}

export interface ModelRegistry {
  version: string;
  generated_at: string;
  source: string;
  source_url: string;
  logos_url: string;
  stats: {
    total_models: number;
    providers: number;
  };
  providers: Record<AIProvider, ProviderInfo>;
  models: Record<string, ModelInfo>;
}

/**
 * Lookup a model by provider and model ID.
 */
export function lookupModel(
  registry: ModelRegistry,
  provider: AIProvider,
  modelId: string
): ModelInfo | undefined {
  return registry.models[`${provider}/${modelId}`];
}

/**
 * Get provider info including API endpoint for detection.
 */
export function getProvider(
  registry: ModelRegistry,
  providerId: AIProvider
): ProviderInfo | undefined {
  return registry.providers[providerId];
}

/**
 * Find provider by API endpoint URL.
 * Useful for detecting which provider a request is going to.
 */
export function findProviderByEndpoint(
  registry: ModelRegistry,
  url: string
): { providerId: AIProvider; provider: ProviderInfo } | undefined {
  for (const [providerId, provider] of Object.entries(registry.providers)) {
    if (provider.api_endpoint && url.includes(new URL(provider.api_endpoint).hostname)) {
      return { providerId: providerId as AIProvider, provider };
    }
  }
  return undefined;
}

/**
 * Estimate the cost of an API call.
 */
export function estimateCost(
  model: ModelInfo,
  inputTokens: number,
  outputTokens: number,
  options?: {
    cachedInputTokens?: number;
    reasoningTokens?: number;
  }
): { input: number; output: number; cached?: number; reasoning?: number; total: number } | undefined {
  if (!model.input_cost_per_1k && !model.output_cost_per_1k) {
    return undefined;
  }

  const input = model.input_cost_per_1k
    ? (inputTokens / 1000) * model.input_cost_per_1k
    : 0;
  const output = model.output_cost_per_1k
    ? (outputTokens / 1000) * model.output_cost_per_1k
    : 0;

  let cached = 0;
  if (options?.cachedInputTokens && model.cache_read_cost_per_1k) {
    cached = (options.cachedInputTokens / 1000) * model.cache_read_cost_per_1k;
  }

  let reasoning = 0;
  if (options?.reasoningTokens && model.reasoning_cost_per_1k) {
    reasoning = (options.reasoningTokens / 1000) * model.reasoning_cost_per_1k;
  }

  const total = input + output + cached + reasoning;

  const result: any = {
    input: Math.round(input * 1000000) / 1000000,
    output: Math.round(output * 1000000) / 1000000,
    total: Math.round(total * 1000000) / 1000000,
  };

  if (cached > 0) result.cached = Math.round(cached * 1000000) / 1000000;
  if (reasoning > 0) result.reasoning = Math.round(reasoning * 1000000) / 1000000;

  return result;
}

/**
 * Get the logo URL for a provider.
 */
export function getProviderLogoUrl(providerId: string): string {
  return `https://models.dev/logos/${providerId}.svg`;
}
