import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, FileText, Trash2 } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { useLocation } from "wouter";

export default function Projects() {
  const [, setLocation] = useLocation();
  const projectsQuery = trpc.projects.list.useQuery();
  const createProjectMutation = trpc.projects.create.useMutation();
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({ name: "", description: "" });

  const handleCreateProject = async () => {
    if (!formData.name.trim()) return;

    try {
      await createProjectMutation.mutateAsync({
        name: formData.name,
        description: formData.description,
      });
      setFormData({ name: "", description: "" });
      setIsOpen(false);
      projectsQuery.refetch();
    } catch (error) {
      console.error("Error creating project:", error);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Projects</h1>
            <p className="text-muted-foreground">Manage your content optimization projects</p>
          </div>
          <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                New Project
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
                <DialogDescription>
                  Start a new project to organize your content optimization work
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Project Name</label>
                  <Input
                    placeholder="e.g., Q1 Blog Campaign"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Description</label>
                  <Textarea
                    placeholder="Describe your project..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setIsOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateProject} disabled={createProjectMutation.isPending}>
                    {createProjectMutation.isPending ? "Creating..." : "Create"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projectsQuery.isLoading ? (
            <div className="col-span-full text-center py-8">Loading projects...</div>
          ) : projectsQuery.data && projectsQuery.data.length > 0 ? (
            projectsQuery.data.map((project) => (
              <Card key={project.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{project.name}</CardTitle>
                      <CardDescription className="mt-1">{project.description}</CardDescription>
                    </div>
                    <FileText className="w-5 h-5 text-muted-foreground" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">
                      Status: <span className="font-medium capitalize">{project.status}</span>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Updated: {new Date(project.updatedAt).toLocaleDateString()}
                    </div>
                    <Button
                      className="w-full mt-4"
                      onClick={() => setLocation(`/project/${project.id}`)}
                    >
                      View Project
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <div className="col-span-full text-center py-12">
              <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">No projects yet</p>
              <Button onClick={() => setIsOpen(true)}>Create Your First Project</Button>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
