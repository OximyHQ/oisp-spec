// OISP Model Registry Types
// Auto-generated - DO NOT EDIT MANUALLY

export type AIProvider =
  | 'openai'
  | 'anthropic'
  | 'google'
  | 'azure_openai'
  | 'aws_bedrock'
  | 'cohere'
  | 'mistral'
  | 'groq'
  | 'together'
  | 'fireworks'
  | 'replicate'
  | 'huggingface'
  | 'ollama'
  | 'lmstudio'
  | 'vllm'
  | 'deepseek'
  | 'perplexity'
  | 'openrouter'
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
  | 'parallel_function_calling'
  | 'system_messages'
  | 'json_mode'
  | 'prompt_caching'
  | 'reasoning'
  | 'web_search'
  | 'audio_input'
  | 'audio_output';

export interface ModelInfo {
  id: string;
  litellm_id?: string;
  provider: AIProvider;
  mode: ModelMode;
  max_input_tokens?: number;
  max_output_tokens?: number;
  input_cost_per_1k?: number;
  output_cost_per_1k?: number;
  capabilities?: ModelCapability[];
  deprecated?: boolean;
  deprecation_date?: string;
}

export interface ModelRegistry {
  version: string;
  generated_at: string;
  source: string;
  source_url: string;
  stats: {
    total_models: number;
    providers: number;
  };
  providers: Record<AIProvider, {
    model_count: number;
    models: string[];
  }>;
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
 * Estimate the cost of an API call.
 */
export function estimateCost(
  model: ModelInfo,
  inputTokens: number,
  outputTokens: number
): { input: number; output: number; total: number } | undefined {
  if (!model.input_cost_per_1k || !model.output_cost_per_1k) {
    return undefined;
  }
  
  const input = (inputTokens / 1000) * model.input_cost_per_1k;
  const output = (outputTokens / 1000) * model.output_cost_per_1k;
  
  return {
    input: Math.round(input * 1000000) / 1000000,
    output: Math.round(output * 1000000) / 1000000,
    total: Math.round((input + output) * 1000000) / 1000000,
  };
}
