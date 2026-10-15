import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, decimal, json, boolean } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 */
export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Projects table - organizes content by client or campaign
 */
export const projects = mysqlTable("projects", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description"),
  status: mysqlEnum("status", ["active", "archived"]).default("active").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Project = typeof projects.$inferSelect;
export type InsertProject = typeof projects.$inferInsert;

/**
 * Content table - stores content pieces being optimized
 */
export const content = mysqlTable("content", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  userId: int("userId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  slug: varchar("slug", { length: 255 }).notNull(),
  body: text("body").notNull(),
  metaDescription: varchar("metaDescription", { length: 160 }),
  metaKeywords: text("metaKeywords"),
  seoScore: int("seoScore").default(0),
  readabilityScore: decimal("readabilityScore", { precision: 5, scale: 2 }).default("0"),
  currentVersionId: int("currentVersionId"),
  status: mysqlEnum("status", ["draft", "published", "archived"]).default("draft").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Content = typeof content.$inferSelect;
export type InsertContent = typeof content.$inferInsert;

/**
 * Content versions - tracks history of changes
 */
export const contentVersions = mysqlTable("contentVersions", {
  id: int("id").autoincrement().primaryKey(),
  contentId: int("contentId").notNull(),
  title: varchar("title", { length: 255 }).notNull(),
  body: text("body").notNull(),
  metaDescription: varchar("metaDescription", { length: 160 }),
  metaKeywords: text("metaKeywords"),
  seoScore: int("seoScore"),
  readabilityScore: decimal("readabilityScore", { precision: 5, scale: 2 }),
  changeLog: text("changeLog"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type ContentVersion = typeof contentVersions.$inferSelect;
export type InsertContentVersion = typeof contentVersions.$inferInsert;

/**
 * SEO metrics - stores calculated SEO analysis data
 */
export const seoMetrics = mysqlTable("seoMetrics", {
  id: int("id").autoincrement().primaryKey(),
  contentId: int("contentId").notNull(),
  keywordDensity: json("keywordDensity"), // { keyword: string, density: number }[]
  headingStructure: json("headingStructure"), // { level: number, text: string }[]
  contentLength: int("contentLength"),
  readabilityScore: decimal("readabilityScore", { precision: 5, scale: 2 }),
  keywordCount: int("keywordCount"),
  internalLinks: int("internalLinks"),
  externalLinks: int("externalLinks"),
  imageCount: int("imageCount"),
  metaTagsValid: boolean("metaTagsValid").default(false),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type SeoMetrics = typeof seoMetrics.$inferSelect;
export type InsertSeoMetrics = typeof seoMetrics.$inferInsert;

/**
 * AI suggestions - stores LLM-generated recommendations
 */
export const aiSuggestions = mysqlTable("aiSuggestions", {
  id: int("id").autoincrement().primaryKey(),
  contentId: int("contentId").notNull(),
  suggestionType: mysqlEnum("suggestionType", ["title", "description", "cta", "content", "keyword"]).notNull(),
  originalText: text("originalText"),
  suggestedText: text("suggestedText").notNull(),
  reasoning: text("reasoning"),
  creditsUsed: int("creditsUsed").default(1),
  applied: boolean("applied").default(false),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type AiSuggestion = typeof aiSuggestions.$inferSelect;
export type InsertAiSuggestion = typeof aiSuggestions.$inferInsert;

/**
 * Competitor analysis - tracks competitor SEO data
 */
export const competitorAnalysis = mysqlTable("competitorAnalysis", {
  id: int("id").autoincrement().primaryKey(),
  projectId: int("projectId").notNull(),
  competitorUrl: varchar("competitorUrl", { length: 255 }).notNull(),
  competitorName: varchar("competitorName", { length: 255 }),
  seoScore: int("seoScore"),
  keywordRanking: json("keywordRanking"), // { keyword: string, rank: number }[]
  backlinks: int("backlinks"),
  trafficEstimate: int("trafficEstimate"),
  lastAnalyzed: timestamp("lastAnalyzed"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type CompetitorAnalysis = typeof competitorAnalysis.$inferSelect;
export type InsertCompetitorAnalysis = typeof competitorAnalysis.$inferInsert;

/**
 * User credits - tracks AI usage and subscription
 */
export const userCredits = mysqlTable("userCredits", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull().unique(),
  totalCredits: int("totalCredits").default(0),
  usedCredits: int("usedCredits").default(0),
  subscriptionPlan: mysqlEnum("subscriptionPlan", ["free", "pro", "enterprise"]).default("free").notNull(),
  subscriptionExpiresAt: timestamp("subscriptionExpiresAt"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type UserCredits = typeof userCredits.$inferSelect;
export type InsertUserCredits = typeof userCredits.$inferInsert;

/**
 * Performance metrics - tracks optimization results
 */
export const performanceMetrics = mysqlTable("performanceMetrics", {
  id: int("id").autoincrement().primaryKey(),
  contentId: int("contentId").notNull(),
  metric: varchar("metric", { length: 100 }).notNull(), // e.g., "clicks", "impressions", "ctr", "ranking"
  value: decimal("value", { precision: 10, scale: 2 }),
  period: varchar("period", { length: 50 }), // e.g., "daily", "weekly", "monthly"
  recordedAt: timestamp("recordedAt").defaultNow().notNull(),
});

export type PerformanceMetric = typeof performanceMetrics.$inferSelect;
export type InsertPerformanceMetric = typeof performanceMetrics.$inferInsert;

/**
 * Exports - tracks content exports
 */
export const exports = mysqlTable("exports", {
  id: int("id").autoincrement().primaryKey(),
  contentId: int("contentId").notNull(),
  format: mysqlEnum("format", ["html", "markdown", "text"]).notNull(),
  fileUrl: varchar("fileUrl", { length: 255 }),
  fileKey: varchar("fileKey", { length: 255 }),
  creditsUsed: int("creditsUsed").default(1),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Export = typeof exports.$inferSelect;
export type InsertExport = typeof exports.$inferInsert;
