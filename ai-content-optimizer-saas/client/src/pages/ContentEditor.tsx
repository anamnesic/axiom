import { useState, useEffect } from "react";
import { useParams } from "wouter";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle, AlertTriangle, Info } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";

export default function ContentEditor() {
  const { contentId } = useParams<{ contentId: string }>();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [metaDescription, setMetaDescription] = useState("");
  const [metaKeywords, setMetaKeywords] = useState("");
  const [seoAnalysis, setSeoAnalysis] = useState<any>(null);

  const seoAnalyzeQuery = trpc.seo.analyze.useQuery(
    {
      title,
      body,
      metaDescription,
      metaKeywords,
    },
    {
      enabled: title.length > 0 || body.length > 0,
    }
  );

  useEffect(() => {
    if (seoAnalyzeQuery.data) {
      setSeoAnalysis(seoAnalyzeQuery.data);
    }
  }, [seoAnalyzeQuery.data]);

  const getSeoScoreColor = (score: number) => {
    if (score < 40) return "text-red-500";
    if (score < 70) return "text-yellow-500";
    return "text-green-500";
  };

  const getIssueSeverityIcon = (type: string) => {
    switch (type) {
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "warning":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case "info":
        return <Info className="w-4 h-4 text-blue-500" />;
      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editor Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div>
            <h1 className="text-3xl font-bold mb-1">Content Editor</h1>
            <p className="text-muted-foreground">Write and optimize your content with real-time SEO analysis</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Content</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Title</label>
                <Input
                  placeholder="Enter your content title..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  maxLength={60}
                  className="mt-1"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {title.length}/60 characters
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">Content Body</label>
                <Textarea
                  placeholder="Write your content here..."
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={10}
                  className="mt-1 font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {body.split(/\s+/).filter(w => w.length > 0).length} words
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">Meta Description</label>
                <Textarea
                  placeholder="Enter meta description (120-160 characters)..."
                  value={metaDescription}
                  onChange={(e) => setMetaDescription(e.target.value)}
                  maxLength={160}
                  rows={2}
                  className="mt-1"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {metaDescription.length}/160 characters
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">Meta Keywords</label>
                <Input
                  placeholder="Enter keywords separated by commas..."
                  value={metaKeywords}
                  onChange={(e) => setMetaKeywords(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div className="flex gap-2">
                <Button>Save Draft</Button>
                <Button variant="outline">Publish</Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* SEO Analysis Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>SEO Analysis</CardTitle>
              <CardDescription>Real-time optimization metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {seoAnalysis ? (
                <>
                  {/* SEO Score */}
                  <div className="text-center p-4 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground mb-1">SEO Score</p>
                    <p className={`text-4xl font-bold ${getSeoScoreColor(seoAnalysis.seoScore)}`}>
                      {seoAnalysis.seoScore}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">out of 100</p>
                  </div>

                  {/* Readability Score */}
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-sm font-medium">Readability</p>
                    <p className="text-2xl font-bold">{Math.round(seoAnalysis.readabilityScore)}</p>
                    <p className="text-xs text-muted-foreground">Flesch-Kincaid Score</p>
                  </div>

                  {/* Content Metrics */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Word Count</span>
                      <span className="font-medium">{seoAnalysis.wordCount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Content Length</span>
                      <span className="font-medium">{seoAnalysis.contentLength} chars</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Keywords</span>
                      <span className="font-medium">{seoAnalysis.keywordCount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Internal Links</span>
                      <span className="font-medium">{seoAnalysis.internalLinks}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">External Links</span>
                      <span className="font-medium">{seoAnalysis.externalLinks}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Images</span>
                      <span className="font-medium">{seoAnalysis.imageCount}</span>
                    </div>
                  </div>

                  {/* Issues */}
                  {seoAnalysis.issues.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Issues</p>
                      <div className="space-y-1 max-h-40 overflow-y-auto">
                        {seoAnalysis.issues.map((issue: any, idx: number) => (
                          <div key={idx} className="flex gap-2 text-xs p-2 bg-muted rounded">
                            {getIssueSeverityIcon(issue.type)}
                            <span>{issue.message}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {seoAnalysis.recommendations.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Recommendations</p>
                      <div className="space-y-1 max-h-40 overflow-y-auto">
                        {seoAnalysis.recommendations.map((rec: string, idx: number) => (
                          <div key={idx} className="flex gap-2 text-xs p-2 bg-blue-50 dark:bg-blue-950 rounded">
                            <CheckCircle className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Start writing to see SEO analysis
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
