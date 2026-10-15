import { eq, and, desc } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, projects, content, contentVersions, seoMetrics, aiSuggestions, userCredits, performanceMetrics, competitorAnalysis, exports } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// Projects helpers
export async function getUserProjects(userId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(projects).where(eq(projects.userId, userId)).orderBy(desc(projects.updatedAt));
}

export async function getProjectById(projectId: number, userId: number) {
  const db = await getDb();
  if (!db) return undefined;

  const result = await db.select().from(projects).where(
    and(eq(projects.id, projectId), eq(projects.userId, userId))
  ).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function createProject(userId: number, name: string, description?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(projects).values({
    userId,
    name,
    description,
  });

  return result;
}

// Content helpers
export async function getProjectContent(projectId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(content).where(eq(content.projectId, projectId)).orderBy(desc(content.updatedAt));
}

export async function getContentById(contentId: number) {
  const db = await getDb();
  if (!db) return undefined;

  const result = await db.select().from(content).where(eq(content.id, contentId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function createContent(projectId: number, userId: number, title: string, body: string, metaDescription?: string, metaKeywords?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

  const result = await db.insert(content).values({
    projectId,
    userId,
    title,
    slug,
    body,
    metaDescription,
    metaKeywords,
  });

  return result;
}

export async function updateContent(contentId: number, updates: Partial<typeof content.$inferInsert>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.update(content).set(updates).where(eq(content.id, contentId));
}

// Content versions helpers
export async function getContentVersions(contentId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(contentVersions).where(eq(contentVersions.contentId, contentId)).orderBy(desc(contentVersions.createdAt));
}

export async function createContentVersion(contentId: number, title: string, body: string, metaDescription?: string, metaKeywords?: string, changeLog?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(contentVersions).values({
    contentId,
    title,
    body,
    metaDescription,
    metaKeywords,
    changeLog,
  });
}

// SEO Metrics helpers
export async function getSeoMetrics(contentId: number) {
  const db = await getDb();
  if (!db) return undefined;

  const result = await db.select().from(seoMetrics).where(eq(seoMetrics.contentId, contentId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function upsertSeoMetrics(contentId: number, metrics: Partial<typeof seoMetrics.$inferInsert>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await getSeoMetrics(contentId);

  if (existing) {
    return await db.update(seoMetrics).set(metrics).where(eq(seoMetrics.contentId, contentId));
  } else {
    return await db.insert(seoMetrics).values({
      contentId,
      ...metrics,
    });
  }
}

// User Credits helpers
export async function getUserCredits(userId: number) {
  const db = await getDb();
  if (!db) return undefined;

  const result = await db.select().from(userCredits).where(eq(userCredits.userId, userId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export async function createUserCredits(userId: number, totalCredits: number = 100) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(userCredits).values({
    userId,
    totalCredits,
  });
}

export async function consumeCredits(userId: number, amount: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const credits = await getUserCredits(userId);
  if (!credits) throw new Error("User credits not found");

  const totalCredits = credits.totalCredits ?? 0;
  const usedCredits = credits.usedCredits ?? 0;
  const remainingCredits = totalCredits - usedCredits - amount;
  if (remainingCredits < 0) throw new Error("Insufficient credits");

  return await db.update(userCredits).set({
    usedCredits: usedCredits + amount,
  }).where(eq(userCredits.userId, userId));
}

// AI Suggestions helpers
export async function getContentSuggestions(contentId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(aiSuggestions).where(eq(aiSuggestions.contentId, contentId)).orderBy(desc(aiSuggestions.createdAt));
}

export async function createAiSuggestion(contentId: number, suggestionType: string, suggestedText: string, originalText?: string, reasoning?: string, creditsUsed: number = 1) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(aiSuggestions).values({
    contentId,
    suggestionType: suggestionType as any,
    suggestedText,
    originalText,
    reasoning,
    creditsUsed,
  });
}

// Performance Metrics helpers
export async function getContentPerformance(contentId: number, metric?: string) {
  const db = await getDb();
  if (!db) return [];

  if (metric) {
    return await db.select().from(performanceMetrics).where(
      and(eq(performanceMetrics.contentId, contentId), eq(performanceMetrics.metric, metric))
    ).orderBy(desc(performanceMetrics.recordedAt));
  }

  return await db.select().from(performanceMetrics).where(eq(performanceMetrics.contentId, contentId)).orderBy(desc(performanceMetrics.recordedAt));
}

export async function recordPerformanceMetric(contentId: number, metric: string, value: number, period?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(performanceMetrics).values({
    contentId,
    metric,
    value: value.toString() as any,
    period,
  });
}

// Exports helpers
export async function createExport(contentId: number, format: string, fileUrl?: string, fileKey?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(exports).values({
    contentId,
    format: format as any,
    fileUrl,
    fileKey,
  });
}

// Competitor Analysis helpers
export async function getCompetitorAnalysis(projectId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(competitorAnalysis).where(eq(competitorAnalysis.projectId, projectId)).orderBy(desc(competitorAnalysis.updatedAt));
}

export async function createCompetitorAnalysis(projectId: number, competitorUrl: string, competitorName?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(competitorAnalysis).values({
    projectId,
    competitorUrl,
    competitorName,
  });
}

export async function updateCompetitorAnalysis(competitorId: number, updates: Partial<typeof competitorAnalysis.$inferInsert>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.update(competitorAnalysis).set(updates).where(eq(competitorAnalysis.id, competitorId));
}
