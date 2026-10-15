/**
 * SEO Analysis Engine
 * Provides real-time SEO metrics and recommendations
 */

export interface SeoAnalysisResult {
  seoScore: number; // 0-100
  readabilityScore: number; // 0-100
  keywordDensity: { keyword: string; density: number }[];
  headingStructure: { level: number; text: string }[];
  contentLength: number;
  wordCount: number;
  keywordCount: number;
  internalLinks: number;
  externalLinks: number;
  imageCount: number;
  metaTagsValid: boolean;
  issues: SeoIssue[];
  recommendations: string[];
}

export interface SeoIssue {
  type: "error" | "warning" | "info";
  message: string;
  severity: number; // 1-10
}

/**
 * Analyzes content for SEO metrics
 */
export function analyzeSeo(title: string, body: string, metaDescription?: string, metaKeywords?: string): SeoAnalysisResult {
  const issues: SeoIssue[] = [];
  const recommendations: string[] = [];
  let seoScore = 50; // Start with base score

  // Title analysis
  if (!title || title.length === 0) {
    issues.push({ type: "error", message: "Title is missing", severity: 10 });
  } else if (title.length < 30) {
    issues.push({ type: "warning", message: "Title is too short (less than 30 characters)", severity: 6 });
    recommendations.push("Expand your title to at least 30 characters for better SEO");
  } else if (title.length > 60) {
    issues.push({ type: "warning", message: "Title is too long (more than 60 characters)", severity: 5 });
    recommendations.push("Shorten your title to 50-60 characters to avoid truncation in search results");
  } else {
    seoScore += 10;
  }

  // Meta description analysis
  if (!metaDescription || metaDescription.length === 0) {
    issues.push({ type: "error", message: "Meta description is missing", severity: 9 });
    recommendations.push("Add a meta description (150-160 characters) to improve click-through rates");
  } else if (metaDescription.length < 120) {
    issues.push({ type: "warning", message: "Meta description is too short", severity: 5 });
    recommendations.push("Expand your meta description to 120-160 characters");
  } else if (metaDescription.length > 160) {
    issues.push({ type: "warning", message: "Meta description is too long", severity: 4 });
    recommendations.push("Shorten your meta description to 150-160 characters");
  } else {
    seoScore += 10;
  }

  // Content length analysis
  const wordCount = body.split(/\s+/).filter(w => w.length > 0).length;
  if (wordCount < 300) {
    issues.push({ type: "warning", message: "Content is too short (less than 300 words)", severity: 7 });
    recommendations.push("Expand your content to at least 300 words for better SEO");
  } else if (wordCount >= 300 && wordCount <= 3000) {
    seoScore += 15;
  } else if (wordCount > 3000) {
    issues.push({ type: "info", message: "Content is very long (more than 3000 words)", severity: 2 });
    recommendations.push("Consider breaking long content into multiple articles or sections");
  }

  // Heading structure analysis
  const headingRegex = /<h([1-6])>(.*?)<\/h\1>/gi;
  const headings: { level: number; text: string }[] = [];
  let match;
  let hasH1 = false;

  while ((match = headingRegex.exec(body)) !== null) {
    const level = parseInt(match[1]);
    const text = match[2].replace(/<[^>]*>/g, "").trim();
    headings.push({ level, text });
    if (level === 1) hasH1 = true;
  }

  if (!hasH1) {
    issues.push({ type: "error", message: "Missing H1 heading", severity: 8 });
    recommendations.push("Add an H1 heading at the beginning of your content");
  } else {
    seoScore += 10;
  }

  // Keyword analysis
  const keywords = metaKeywords ? metaKeywords.split(",").map(k => k.trim().toLowerCase()) : [];
  const keywordDensity: { keyword: string; density: number }[] = [];
  const bodyLower = body.toLowerCase();

  keywords.forEach(keyword => {
    const regex = new RegExp(`\\b${keyword}\\b`, "g");
    const count = (bodyLower.match(regex) || []).length;
    const density = (count / wordCount) * 100;
    keywordDensity.push({ keyword, density });

    if (density < 0.5) {
      recommendations.push(`Keyword "${keyword}" appears too infrequently. Target 0.5-2.5% density.`);
    } else if (density > 3) {
      issues.push({ type: "warning", message: `Keyword "${keyword}" may be over-optimized (${density.toFixed(2)}%)`, severity: 5 });
      recommendations.push(`Reduce usage of keyword "${keyword}" to avoid keyword stuffing`);
    }
  });

  // Link analysis
  const internalLinkRegex = /href=["'](?!(?:https?:|\/\/))[^"']*["']/gi;
  const externalLinkRegex = /href=["'](?:https?:)?\/\/[^"']*["']/gi;
  const internalLinks = (body.match(internalLinkRegex) || []).length;
  const externalLinks = (body.match(externalLinkRegex) || []).length;

  if (internalLinks === 0) {
    recommendations.push("Add internal links to improve site structure and SEO");
  } else {
    seoScore += 5;
  }

  // Image analysis
  const imageRegex = /<img[^>]*>/gi;
  const imageCount = (body.match(imageRegex) || []).length;

  if (imageCount === 0) {
    recommendations.push("Add images to make your content more engaging and improve SEO");
  } else {
    seoScore += 5;
  }

  // Calculate readability score (simplified Flesch-Kincaid)
  const sentences = body.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
  const syllables = countSyllables(body);
  const readabilityScore = Math.max(0, Math.min(100, 206.835 - 1.015 * (wordCount / sentences) - 84.6 * (syllables / wordCount)));

  if (readabilityScore < 60) {
    issues.push({ type: "warning", message: "Content readability is low", severity: 6 });
    recommendations.push("Simplify your language and use shorter sentences for better readability");
  } else if (readabilityScore >= 60 && readabilityScore <= 70) {
    seoScore += 5;
  } else if (readabilityScore > 70) {
    seoScore += 10;
  }

  // Meta tags validation
  const metaTagsValid = !!title && !!metaDescription && keywords.length > 0;
  if (metaTagsValid) {
    seoScore += 5;
  }

  // Cap score at 100
  seoScore = Math.min(100, seoScore);

  return {
    seoScore: Math.round(seoScore),
    readabilityScore: Math.round(readabilityScore),
    keywordDensity,
    headingStructure: headings,
    contentLength: body.length,
    wordCount,
    keywordCount: keywords.length,
    internalLinks,
    externalLinks,
    imageCount,
    metaTagsValid,
    issues,
    recommendations,
  };
}

/**
 * Counts approximate syllables in text
 */
function countSyllables(text: string): number {
  const words = text.toLowerCase().match(/\b\w+\b/g) || [];
  let syllableCount = 0;

  words.forEach(word => {
    syllableCount += estimateSyllables(word);
  });

  return syllableCount;
}

/**
 * Estimates syllable count for a word
 */
function estimateSyllables(word: string): number {
  word = word.toLowerCase();
  let syllables = 0;
  const vowels = "aeiouy";
  let previousWasVowel = false;

  for (let i = 0; i < word.length; i++) {
    const isVowel = vowels.includes(word[i]);
    if (isVowel && !previousWasVowel) {
      syllables++;
    }
    previousWasVowel = isVowel;
  }

  // Adjustments
  if (word.endsWith("e")) syllables--;
  if (word.endsWith("le") && word.length > 2) syllables++;
  if (syllables === 0) syllables = 1;

  return syllables;
}

/**
 * Generates SEO recommendations based on analysis
 */
export function generateRecommendations(analysis: SeoAnalysisResult): string[] {
  const recommendations = [...analysis.recommendations];

  // Add score-based recommendations
  if (analysis.seoScore < 50) {
    recommendations.unshift("Your SEO score is low. Focus on the critical issues above.");
  } else if (analysis.seoScore < 70) {
    recommendations.unshift("Your SEO score can be improved. Address the warnings above.");
  } else if (analysis.seoScore >= 80) {
    recommendations.unshift("Great SEO score! Keep optimizing for even better results.");
  }

  return recommendations;
}
