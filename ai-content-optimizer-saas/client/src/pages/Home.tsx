import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { trpc } from "@/lib/trpc";
import { getLoginUrl } from "@/const";
import { BarChart3, Zap, FileText, TrendingUp } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";

export default function Home() {
  const { user, loading } = useAuth();
  const dashboardStats = trpc.dashboard.stats.useQuery(undefined, { enabled: !!user });

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center p-4">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center space-y-2">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-primary rounded-lg flex items-center justify-center">
                <BarChart3 className="w-8 h-8 text-primary-foreground" />
              </div>
            </div>
            <h1 className="text-3xl font-bold">ContentOpt</h1>
            <p className="text-muted-foreground">AI-Powered SEO Content Optimizer</p>
          </div>

          <div className="space-y-4">
            <div className="bg-card rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span className="font-medium">Real-time SEO Analysis</span>
              </div>
              <p className="text-sm text-muted-foreground">Get instant feedback on your content's SEO performance</p>
            </div>

            <div className="bg-card rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-500" />
                <span className="font-medium">AI Suggestions</span>
              </div>
              <p className="text-sm text-muted-foreground">Optimize titles, descriptions, and CTAs with AI</p>
            </div>

            <div className="bg-card rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <span className="font-medium">Performance Tracking</span>
              </div>
              <p className="text-sm text-muted-foreground">Monitor your optimization results and ROI</p>
            </div>
          </div>

          <Button
            size="lg"
            className="w-full"
            onClick={() => (window.location.href = getLoginUrl())}
          >
            Get Started
          </Button>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here's your content optimization overview.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardStats.data?.totalProjects || 0}</div>
              <p className="text-xs text-muted-foreground">{dashboardStats.data?.activeProjects || 0} active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Credits Remaining</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dashboardStats.data?.creditsRemaining || 0}</div>
              <p className="text-xs text-muted-foreground">AI analysis quota</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Content Pieces</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0</div>
              <p className="text-xs text-muted-foreground">Total optimized</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Avg SEO Score</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">--</div>
              <p className="text-xs text-muted-foreground">Out of 100</p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Projects */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Projects</CardTitle>
            <CardDescription>Your most recently updated projects</CardDescription>
          </CardHeader>
          <CardContent>
            {dashboardStats.data?.recentProjects && dashboardStats.data.recentProjects.length > 0 ? (
              <div className="space-y-2">
                {dashboardStats.data.recentProjects.map((project) => (
                  <div key={project.id} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <div>
                      <p className="font-medium">{project.name}</p>
                      <p className="text-sm text-muted-foreground">{project.description}</p>
                    </div>
                    <Button variant="ghost" size="sm">View</Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No projects yet</p>
                <Button>Create First Project</Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
