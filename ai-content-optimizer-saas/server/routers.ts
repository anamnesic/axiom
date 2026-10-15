import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router, protectedProcedure } from "./_core/trpc";
import { z } from "zod";
import * as db from "./db";
import { TRPCError } from "@trpc/server";
import { analyzeSeo } from "./seoAnalyzer";
import { generateTitleSuggestions, generateDescriptionSuggestions, generateCtaSuggestions, generateContentSuggestions, generateKeywordSuggestions } from "./aiSuggestions";

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  // Projects router
  projects: router({
    list: protectedProcedure.query(async ({ ctx }) => {
      return await db.getUserProjects(ctx.user.id);
    }),

    get: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ ctx, input }) => {
        const project = await db.getProjectById(input.projectId, ctx.user.id);
        if (!project) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Project not found" });
        }
        return project;
      }),

    create: protectedProcedure
      .input(z.object({
        name: z.string().min(1).max(255),
        description: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        await db.createProject(ctx.user.id, input.name, input.description);
        return { success: true };
      }),

    update: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        name: z.string().optional(),
        description: z.string().optional(),
        status: z.enum(["active", "archived"]).optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const project = await db.getProjectById(input.projectId, ctx.user.id);
        if (!project) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Project not found" });
        }

        const updates: any = {};
        if (input.name) updates.name = input.name;
        if (input.description) updates.description = input.description;
        if (input.status) updates.status = input.status;

        await db.updateContent(input.projectId, updates);
        return { success: true };
      }),
  }),

  // Content router
  content: router({
    list: protectedProcedure
      .input(z.object({ projectId: z.number() }))
      .query(async ({ ctx, input }) => {
        const project = await db.getProjectById(input.projectId, ctx.user.id);
        if (!project) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Project not found" });
        }
        return await db.getProjectContent(input.projectId);
      }),

    get: protectedProcedure
      .input(z.object({ contentId: z.number() }))
      .query(async ({ ctx, input }) => {
        const content = await db.getContentById(input.contentId);
        if (!content || content.userId !== ctx.user.id) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Content not found" });
        }
        return content;
      }),

    create: protectedProcedure
      .input(z.object({
        projectId: z.number(),
        title: z.string().min(1).max(255),
        body: z.string().min(1),
        metaDescription: z.string().max(160).optional(),
        metaKeywords: z.string().optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const project = await db.getProjectById(input.projectId, ctx.user.id);
        if (!project) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Project not found" });
        }

        await db.createContent(
          input.projectId,
          ctx.user.id,
          input.title,
          input.body,
          input.metaDescription,
          input.metaKeywords
        );

        return { success: true };
      }),

    update: protectedProcedure
      .input(z.object({
        contentId: z.number(),
        title: z.string().optional(),
        body: z.string().optional(),
        metaDescription: z.string().optional(),
        metaKeywords: z.string().optional(),
        status: z.enum(["draft", "published", "archived"]).optional(),
      }))
      .mutation(async ({ ctx, input }) => {
        const content = await db.getContentById(input.contentId);
        if (!content || content.userId !== ctx.user.id) {
          throw new TRPCError({ code: "NOT_FOUND", message: "Content not found" });
        }

        const updates: any = {};
        if (input.title) updates.title = input.title;
        if (input.body) updates.body = input.body;
        if (input.metaDescription) updates.metaDescription = input.metaDescription;
        if (input.metaKeywords) updates.metaKeywords = input.metaKeywords;
        if (input.status) updates.status = input.status;

        await db.updateContent(input.contentId, updates);
        return { success: true };
      }),
  }),

  // Credits router
  credits: router({
    getBalance: protectedProcedure.query(async ({ ctx }) => {
      let credits = await db.getUserCredits(ctx.user.id);
      if (!credits) {
        await db.createUserCredits(ctx.user.id, 100);
        credits = await db.getUserCredits(ctx.user.id);
      }
      return credits;
    }),

    consume: protectedProcedure
      .input(z.object({ amount: z.number().min(1) }))
      .mutation(async ({ ctx, input }) => {
        try {
          await db.consumeCredits(ctx.user.id, input.amount);
          return { success: true };
        } catch (error: any) {
          throw new TRPCError({ code: "PRECONDITION_FAILED", message: error.message });
        }
      }),
  }),

  // SEO Analysis router
  seo: router({
    analyze: protectedProcedure
      .input(z.object({
        title: z.string(),
        body: z.string(),
        metaDescription: z.string().optional(),
        metaKeywords: z.string().optional(),
      }))
      .query(({ input }) => {
        return analyzeSeo(input.title, input.body, input.metaDescription, input.metaKeywords);
      }),
  }),

  // AI Suggestions router
  aiSuggestions: router({
    titleSuggestion: protectedProcedure
      .input(z.object({ title: z.string(), body: z.string() }))
      .mutation(async ({ ctx, input }) => {
        await db.consumeCredits(ctx.user.id, 1);
        return await generateTitleSuggestions(input.title, input.body);
      }),

    descriptionSuggestion: protectedProcedure
      .input(z.object({ metaDescription: z.string(), title: z.string(), body: z.string() }))
      .mutation(async ({ ctx, input }) => {
        await db.consumeCredits(ctx.user.id, 1);
        return await generateDescriptionSuggestions(input.metaDescription, input.title, input.body);
      }),

    ctaSuggestion: protectedProcedure
      .input(z.object({ body: z.string(), title: z.string() }))
      .mutation(async ({ ctx, input }) => {
        await db.consumeCredits(ctx.user.id, 2);
        return await generateCtaSuggestions(input.body, input.title);
      }),

    contentSuggestion: protectedProcedure
      .input(z.object({ body: z.string(), title: z.string() }))
      .mutation(async ({ ctx, input }) => {
        await db.consumeCredits(ctx.user.id, 3);
        return await generateContentSuggestions(input.body, input.title);
      }),

    keywordSuggestion: protectedProcedure
      .input(z.object({ title: z.string(), body: z.string(), currentKeywords: z.string().optional() }))
      .mutation(async ({ ctx, input }) => {
        await db.consumeCredits(ctx.user.id, 1);
        return await generateKeywordSuggestions(input.title, input.body, input.currentKeywords);
      }),
  }),

  // Dashboard router
  dashboard: router({
    stats: protectedProcedure.query(async ({ ctx }) => {
      const projects = await db.getUserProjects(ctx.user.id);
      const credits = await db.getUserCredits(ctx.user.id);

      const totalProjects = projects.length;
      const activeProjects = projects.filter(p => p.status === "active").length;

      return {
        totalProjects,
        activeProjects,
        creditsRemaining: credits ? (credits.totalCredits ?? 0) - (credits.usedCredits ?? 0) : 0,
        recentProjects: projects.slice(0, 5),
      };
    }),
  }),
});

export type AppRouter = typeof appRouter;
