import { invokeLLM } from "./_core/llm";

export interface AiSuggestionRequest {
  contentId: number;
  title: string;
  body: string;
  metaDescription?: string;
  metaKeywords?: string;
  suggestionType: "title" | "description" | "cta" | "content" | "keyword";
}

export interface AiSuggestionResponse {
  originalText: string;
  suggestedText: string;
  reasoning: string;
  creditsUsed: number;
}

/**
 * Generates AI-powered title suggestions
 */
export async function generateTitleSuggestions(title: string, body: string): Promise<AiSuggestionResponse> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are an SEO expert specializing in creating compelling, keyword-rich titles that improve click-through rates and search rankings.",
      },
      {
        role: "user",
        content: `Current title: "${title}"\n\nContent preview: ${body.substring(0, 500)}...\n\nProvide an improved SEO-optimized title (max 60 characters) that:\n1. Includes primary keywords\n2. Is compelling and encourages clicks\n3. Accurately represents the content\n\nRespond with ONLY the new title, no explanation.`,
      },
    ],
  });

  const content = response.choices[0]?.message.content;
  const suggestedTitle = (typeof content === 'string' ? content : '')?.trim() || title;

  return {
    originalText: title,
    suggestedText: suggestedTitle,
    reasoning: "This title is optimized for search engines and user engagement with better keyword placement and clarity.",
    creditsUsed: 1,
  };
}

/**
 * Generates AI-powered meta description suggestions
 */
export async function generateDescriptionSuggestions(
  metaDescription: string,
  title: string,
  body: string
): Promise<AiSuggestionResponse> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are an SEO expert specializing in creating compelling meta descriptions that improve click-through rates from search results.",
      },
      {
        role: "user",
        content: `Title: "${title}"\nCurrent meta description: "${metaDescription}"\n\nContent preview: ${body.substring(0, 300)}...\n\nProvide an improved meta description (120-160 characters) that:\n1. Includes relevant keywords\n2. Is compelling and encourages clicks\n3. Accurately summarizes the content\n4. Includes a call-to-action if appropriate\n\nRespond with ONLY the new meta description, no explanation.`,
      },
    ],
  });

  const content = response.choices[0]?.message.content;
  const suggestedDescription = (typeof content === 'string' ? content : '')?.trim() || metaDescription;

  return {
    originalText: metaDescription || "",
    suggestedText: suggestedDescription,
    reasoning: "This meta description is optimized for search results and encourages higher click-through rates.",
    creditsUsed: 1,
  };
}

/**
 * Generates AI-powered CTA suggestions
 */
export async function generateCtaSuggestions(body: string, title: string): Promise<AiSuggestionResponse> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are a conversion optimization expert specializing in creating compelling calls-to-action.",
      },
      {
        role: "user",
        content: `Title: "${title}"\n\nContent: ${body.substring(0, 500)}...\n\nProvide 3 compelling call-to-action (CTA) options for this content. Each should:\n1. Be action-oriented and specific\n2. Create urgency or curiosity\n3. Be appropriate for the content topic\n\nFormat as: CTA 1 | CTA 2 | CTA 3`,
      },
    ],
  });

  const content = response.choices[0]?.message.content;
  const suggestedCtas = (typeof content === 'string' ? content : '')?.trim() || "Learn More | Get Started | Explore Now";

  return {
    originalText: "Current CTA",
    suggestedText: suggestedCtas,
    reasoning: "These CTAs are optimized to drive conversions and user engagement.",
    creditsUsed: 2,
  };
}

/**
 * Generates AI-powered content improvement suggestions
 */
export async function generateContentSuggestions(body: string, title: string): Promise<AiSuggestionResponse> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are an expert content strategist and SEO specialist. Provide actionable suggestions to improve content quality, engagement, and SEO performance.",
      },
      {
        role: "user",
        content: `Title: "${title}"\n\nContent: ${body}\n\nProvide 5 specific, actionable suggestions to improve this content for:\n1. SEO performance\n2. User engagement\n3. Readability\n4. Keyword optimization\n5. Content structure\n\nBe specific and practical.`,
      },
    ],
  });

  const content = response.choices[0]?.message.content;
  const suggestions = (typeof content === 'string' ? content : '')?.trim() || "";

  return {
    originalText: "Content",
    suggestedText: suggestions,
    reasoning: "These suggestions are based on SEO best practices and content strategy principles.",
    creditsUsed: 3,
  };
}

/**
 * Generates AI-powered keyword suggestions
 */
export async function generateKeywordSuggestions(title: string, body: string, currentKeywords?: string): Promise<AiSuggestionResponse> {
  const response = await invokeLLM({
    messages: [
      {
        role: "system",
        content: "You are an SEO keyword research expert. Suggest relevant, high-intent keywords that will improve search visibility.",
      },
      {
        role: "user",
        content: `Title: "${title}"\n\nContent: ${body.substring(0, 500)}...\n\nCurrent keywords: ${currentKeywords || "None"}\n\nSuggest 10 relevant keywords/phrases that:\n1. Match the content topic\n2. Have good search volume\n3. Are moderately competitive\n4. Include both short-tail and long-tail keywords\n\nFormat as comma-separated list.`,
      },
    ],
  });

  const content = response.choices[0]?.message.content;
  const suggestedKeywords = (typeof content === 'string' ? content : '')?.trim() || "";

  return {
    originalText: currentKeywords || "No keywords",
    suggestedText: suggestedKeywords,
    reasoning: "These keywords are selected based on search volume, relevance, and competition analysis.",
    creditsUsed: 1,
  };
}

/**
 * Generates all types of suggestions at once
 */
export async function generateAllSuggestions(
  title: string,
  body: string,
  metaDescription?: string,
  metaKeywords?: string
): Promise<{
  title: AiSuggestionResponse;
  description: AiSuggestionResponse;
  cta: AiSuggestionResponse;
  content: AiSuggestionResponse;
  keywords: AiSuggestionResponse;
  totalCreditsUsed: number;
}> {
  const [titleSuggestion, descriptionSuggestion, ctaSuggestion, contentSuggestion, keywordSuggestion] = await Promise.all([
    generateTitleSuggestions(title, body),
    generateDescriptionSuggestions(metaDescription || "", title, body),
    generateCtaSuggestions(body, title),
    generateContentSuggestions(body, title),
    generateKeywordSuggestions(title, body, metaKeywords),
  ]);

  const totalCreditsUsed =
    titleSuggestion.creditsUsed +
    descriptionSuggestion.creditsUsed +
    ctaSuggestion.creditsUsed +
    contentSuggestion.creditsUsed +
    keywordSuggestion.creditsUsed;

  return {
    title: titleSuggestion,
    description: descriptionSuggestion,
    cta: ctaSuggestion,
    content: contentSuggestion,
    keywords: keywordSuggestion,
    totalCreditsUsed,
  };
}
